"""Contador de eventos de segurança, sem nenhum dado pessoal.

Guardamos só QUANTAS vezes algo suspeito aconteceu (senhas erradas, limites estourados...), nunca o IP,
o código da sala ou o conteúdo. De hora em hora, se houve algo, uma linha de resumo vai para o registro
do servidor: dá para perceber um ataque sem transformar o servidor num arquivo de dados de pessoas.
"""

import logging
import time
from collections import Counter

logger = logging.getLogger(__name__)

SUMMARY_INTERVAL_SECONDS = 3600

# Nomes dos eventos.
FAILED_JOIN = "senhas_erradas"
LOCKED_JOIN = "entradas_em_sala_trancada"
NOT_OWNER_ATTEMPT = "acoes_de_dono_por_convidado"
RATE_LIMITED = "pedidos_recusados_por_limite"


class SecurityEvents:
    """Conta eventos de segurança e resume o que aconteceu a cada hora."""

    def __init__(self, summary_interval_seconds: int = SUMMARY_INTERVAL_SECONDS) -> None:
        self._summary_interval_seconds = summary_interval_seconds
        self._counts: Counter[str] = Counter()
        self._last_summary_at = time.monotonic()

    def record(self, event_name: str) -> None:
        """Anota que o evento aconteceu mais uma vez."""
        self._counts[event_name] += 1

    def count(self, event_name: str) -> int:
        return self._counts[event_name]

    def reset(self) -> None:
        self._counts.clear()
        self._last_summary_at = time.monotonic()

    def log_summary_if_due(self) -> None:
        """Se passou uma hora desde o último resumo, registra o que aconteceu (só quando houve algo)."""
        if time.monotonic() - self._last_summary_at < self._summary_interval_seconds:
            return
        self._last_summary_at = time.monotonic()
        if not self._counts:
            return
        summary = ", ".join(f"{name}={total}" for name, total in sorted(self._counts.items()))
        logger.warning("Resumo de segurança da última hora: %s", summary)
        self._counts.clear()


# Um só contador para o processo inteiro (o servidor roda com um processo só).
security_events = SecurityEvents()
