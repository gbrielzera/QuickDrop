"""Limite de tentativas: impede que alguém fique adivinhando códigos e senhas, ou crie salas sem parar.

Tudo fica na memória deste processo. Se um dia houver mais de um servidor rodando, estes contadores
passam a viver num Redis compartilhado.
"""

import ipaddress
import math
import time
from collections import deque
from dataclasses import dataclass

from fastapi import HTTPException, Request

from app.config import Settings
from app.security_events import RATE_LIMITED, security_events

SECONDS_PER_MINUTE = 60
SECONDS_PER_HOUR = 3600
TOO_MANY_ATTEMPTS = "too_many_attempts"


def _now() -> float:
    return time.monotonic()


class RateLimiter:
    """Conta quantas vezes cada chave (ex.: um endereço IP) fez algo nos últimos `window_seconds`."""

    def __init__(self, max_hits: int, window_seconds: int) -> None:
        self._max_hits = max_hits
        self._window_seconds = window_seconds
        self._hits_by_key: dict[str, deque[float]] = {}

    def _recent_hits(self, key: str) -> deque[float]:
        hits = self._hits_by_key.get(key, deque())
        while hits and _now() - hits[0] >= self._window_seconds:
            hits.popleft()
        if hits:
            self._hits_by_key[key] = hits
        else:
            self._hits_by_key.pop(key, None)
        return hits

    def is_blocked(self, key: str) -> bool:
        """True se a chave já chegou ao limite dentro da janela de tempo."""
        return len(self._recent_hits(key)) >= self._max_hits

    def seconds_until_free(self, key: str) -> int:
        """Quantos segundos faltam para a chave poder tentar de novo."""
        hits = self._recent_hits(key)
        if not hits:
            return 0
        return max(math.ceil(hits[0] + self._window_seconds - _now()), 1)

    def record(self, key: str) -> None:
        """Anota mais uma tentativa da chave."""
        self._recent_hits(key)
        self._hits_by_key.setdefault(key, deque()).append(_now())

    def reset(self, key: str) -> None:
        """Esquece as tentativas da chave (ex.: depois de entrar com a senha certa)."""
        self._hits_by_key.pop(key, None)

    def forget_idle_keys(self) -> None:
        """Libera a memória das chaves que não tentaram nada recentemente."""
        for key in list(self._hits_by_key):
            self._recent_hits(key)


class ConcurrentLimiter:
    """Conta quantas coisas cada chave (ex.: um endereço IP) está fazendo AGORA, ao mesmo tempo.

    Serve para os envios de arquivo: os bytes só entram na soma do espaço do servidor quando o envio
    termina, então muitos envios simultâneos poderiam ocupar o disco além do limite por um tempo.
    """

    def __init__(self, max_active: int) -> None:
        self._max_active = max_active
        self._active_by_key: dict[str, int] = {}

    def try_acquire(self, key: str) -> bool:
        """Reserva uma vaga para a chave. Devolve False se ela já usa todas as suas vagas."""
        active = self._active_by_key.get(key, 0)
        if active >= self._max_active:
            return False
        self._active_by_key[key] = active + 1
        return True

    def release(self, key: str) -> None:
        """Devolve a vaga reservada por try_acquire."""
        remaining = self._active_by_key.get(key, 0) - 1
        if remaining > 0:
            self._active_by_key[key] = remaining
        else:
            self._active_by_key.pop(key, None)


class ActiveRoomsQuota:
    """Quantas salas ainda abertas cada chave (ex.: um endereço IP) criou.

    Fica só na memória e some quando a sala expira (ou o servidor reinicia): não guardamos quem criou
    cada sala no banco. Encerrar uma sala antes da hora não devolve a vaga, o que é aceitável: o limite
    é alto e existe para impedir que poucos endereços ocupem todas as salas do servidor.
    """

    def __init__(self, max_rooms: int) -> None:
        self._max_rooms = max_rooms
        self._expirations_by_key: dict[str, list[float]] = {}

    def _open_rooms(self, key: str) -> list[float]:
        expirations = [moment for moment in self._expirations_by_key.get(key, []) if moment > _now()]
        if expirations:
            self._expirations_by_key[key] = expirations
        else:
            self._expirations_by_key.pop(key, None)
        return expirations

    def is_full(self, key: str) -> bool:
        """True se a chave já tem o máximo de salas abertas."""
        return len(self._open_rooms(key)) >= self._max_rooms

    def record(self, key: str, seconds_until_expiry: int) -> None:
        """Anota uma sala nova, que deixa de contar quando expirar."""
        expirations = self._open_rooms(key)
        expirations.append(_now() + seconds_until_expiry)
        self._expirations_by_key[key] = expirations

    def forget_idle_keys(self) -> None:
        """Libera a memória das chaves sem nenhuma sala aberta."""
        for key in list(self._expirations_by_key):
            self._open_rooms(key)


@dataclass
class RateLimits:
    """Todos os limites do app."""

    lookups: RateLimiter  # consultas ao código de uma sala (por IP)
    failed_joins: RateLimiter  # senhas erradas numa sala (por IP e sala)
    failed_joins_by_room: RateLimiter  # senhas erradas numa sala, de todos os IPs juntos
    room_creations: RateLimiter  # salas criadas (por IP)
    api_requests: RateLimiter  # teto geral de pedidos à API (por IP)
    uploads: RateLimiter  # arquivos enviados (por IP)
    concurrent_uploads: ConcurrentLimiter  # envios em andamento (por IP)
    active_rooms: ActiveRoomsQuota  # salas abertas por IP

    def forget_idle_keys(self) -> None:
        for limiter in (
            self.lookups,
            self.failed_joins,
            self.failed_joins_by_room,
            self.room_creations,
            self.api_requests,
            self.uploads,
        ):
            limiter.forget_idle_keys()
        self.active_rooms.forget_idle_keys()


def create_rate_limits(settings: Settings) -> RateLimits:
    """Monta os limites a partir das configurações."""
    return RateLimits(
        lookups=RateLimiter(settings.rate_limit_lookups_per_minute, SECONDS_PER_MINUTE),
        failed_joins=RateLimiter(settings.rate_limit_failed_joins_per_minute, SECONDS_PER_MINUTE),
        failed_joins_by_room=RateLimiter(
            settings.rate_limit_failed_joins_per_room_per_minute, SECONDS_PER_MINUTE
        ),
        room_creations=RateLimiter(settings.rate_limit_room_creations_per_hour, SECONDS_PER_HOUR),
        api_requests=RateLimiter(settings.rate_limit_api_per_minute, SECONDS_PER_MINUTE),
        uploads=RateLimiter(settings.rate_limit_uploads_per_hour, SECONDS_PER_HOUR),
        concurrent_uploads=ConcurrentLimiter(settings.max_concurrent_uploads_per_address),
        active_rooms=ActiveRoomsQuota(settings.max_active_rooms_per_address),
    )


IPV6_PREFIX_BITS = 64


def normalize_address(host: str) -> str:
    """Endereço usado como chave dos limites. Em IPv6, vale o prefixo /64 inteiro.

    Quem tem uma conexão IPv6 recebe um /64 (bilhões de endereços): contar cada endereço sozinho
    deixaria essa pessoa escapar de todos os limites.
    """
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        return host
    if address.version == 4:
        return host
    return str(ipaddress.ip_network(f"{address}/{IPV6_PREFIX_BITS}", strict=False))


def client_address(request: Request) -> str:
    """Endereço de quem fez a requisição.

    Atrás de um proxy (como o Caddy), o servidor precisa ser iniciado com --proxy-headers.
    """
    return normalize_address(request.client.host) if request.client else "unknown"


def block_if_over_limit(limiter: RateLimiter, key: str) -> None:
    """Responde 429 (muitas tentativas) se a chave já chegou ao limite."""
    if limiter.is_blocked(key):
        security_events.record(RATE_LIMITED)
        retry_after = str(limiter.seconds_until_free(key))
        raise HTTPException(status_code=429, detail=TOO_MANY_ATTEMPTS, headers={"Retry-After": retry_after})


def count_attempt(limiter: RateLimiter, key: str) -> None:
    """Recusa com 429 se a chave já passou do limite; senão, anota esta tentativa."""
    block_if_over_limit(limiter, key)
    limiter.record(key)
