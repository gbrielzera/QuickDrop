"""Operações no banco relacionadas a salas."""

from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Room, utc_now
from app.security import generate_room_code

MAX_CODE_ATTEMPTS = 10


class RoomCodeUnavailableError(Exception):
    """Não foi possível gerar um código livre (praticamente impossível, mas tratamos)."""


async def find_active_room(db: AsyncSession, room_code: str) -> Room | None:
    """Busca uma sala pelo código. Salas expiradas contam como inexistentes."""
    query = select(Room).where(Room.code == room_code, Room.expires_at > utc_now())
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def _room_code_is_taken(db: AsyncSession, room_code: str) -> bool:
    # Inclui salas expiradas que ainda não foram apagadas: o código é único na tabela inteira.
    result = await db.execute(select(Room.id).where(Room.code == room_code))
    return result.scalar_one_or_none() is not None


async def _generate_free_room_code(db: AsyncSession) -> str:
    for _ in range(MAX_CODE_ATTEMPTS):
        room_code = generate_room_code()
        if not await _room_code_is_taken(db, room_code):
            return room_code
    raise RoomCodeUnavailableError


async def create_room(
    db: AsyncSession,
    ttl_hours: int,
    has_password: bool,
    kdf_salt: bytes,
    auth_hash: str,
) -> Room:
    """Cria e salva uma sala nova, com um código livre."""
    room = Room(
        code=await _generate_free_room_code(db),
        has_password=has_password,
        kdf_salt=kdf_salt,
        auth_hash=auth_hash,
        expires_at=utc_now() + timedelta(hours=ttl_hours),
    )
    db.add(room)
    await db.commit()
    return room
