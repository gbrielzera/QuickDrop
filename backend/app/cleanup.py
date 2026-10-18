"""Limpeza automática: apaga as salas que expiraram, com tudo o que havia nelas."""

import asyncio
import logging

from fastapi import FastAPI

from app import room_service

logger = logging.getLogger(__name__)

SECONDS_PER_MINUTE = 60


async def delete_expired_rooms(app: FastAPI) -> int:
    """Apaga as salas expiradas (arquivos no disco e registros no banco). Devolve quantas apagou."""
    async with app.state.session_maker() as db:
        expired_rooms = await room_service.find_expired_rooms(db)
        for room in expired_rooms:
            await room_service.end_room(db, app.state.connections, room, reason=room_service.REASON_EXPIRED)
    return len(expired_rooms)


async def run_cleanup_loop(app: FastAPI, interval_minutes: int) -> None:
    """Roda a limpeza de tempos em tempos, até o servidor ser desligado."""
    while True:
        await asyncio.sleep(interval_minutes * SECONDS_PER_MINUTE)
        try:
            await delete_expired_rooms(app)
            app.state.rate_limits.forget_idle_keys()
        except Exception:
            # Uma falha não pode derrubar a limpeza das próximas vezes.
            logger.exception("Falha ao limpar as salas expiradas")
