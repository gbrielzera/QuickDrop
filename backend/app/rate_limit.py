"""Limite de tentativas: impede que alguém fique adivinhando códigos e senhas, ou crie salas sem parar.

Tudo fica na memória deste processo. Se um dia houver mais de um servidor rodando, estes contadores
passam a viver num Redis compartilhado.
"""

import math
import time
from collections import deque
from dataclasses import dataclass

from fastapi import HTTPException, Request

from app.config import Settings

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


@dataclass
class RateLimits:
    """Todos os limites do app."""

    lookups: RateLimiter  # consultas ao código de uma sala (por IP)
    failed_joins: RateLimiter  # senhas erradas numa sala (por IP e sala)
    room_creations: RateLimiter  # salas criadas (por IP)

    def forget_idle_keys(self) -> None:
        for limiter in (self.lookups, self.failed_joins, self.room_creations):
            limiter.forget_idle_keys()


def create_rate_limits(settings: Settings) -> RateLimits:
    """Monta os limites a partir das configurações."""
    return RateLimits(
        lookups=RateLimiter(settings.rate_limit_lookups_per_minute, SECONDS_PER_MINUTE),
        failed_joins=RateLimiter(settings.rate_limit_failed_joins_per_minute, SECONDS_PER_MINUTE),
        room_creations=RateLimiter(settings.rate_limit_room_creations_per_hour, SECONDS_PER_HOUR),
    )


def client_address(request: Request) -> str:
    """Endereço de quem fez a requisição.

    Atrás de um proxy (como o Caddy), o servidor precisa ser iniciado com --proxy-headers.
    """
    return request.client.host if request.client else "unknown"


def block_if_over_limit(limiter: RateLimiter, key: str) -> None:
    """Responde 429 (muitas tentativas) se a chave já chegou ao limite."""
    if limiter.is_blocked(key):
        retry_after = str(limiter.seconds_until_free(key))
        raise HTTPException(status_code=429, detail=TOO_MANY_ATTEMPTS, headers={"Retry-After": retry_after})


def count_attempt(limiter: RateLimiter, key: str) -> None:
    """Recusa com 429 se a chave já passou do limite; senão, anota esta tentativa."""
    block_if_over_limit(limiter, key)
    limiter.record(key)
