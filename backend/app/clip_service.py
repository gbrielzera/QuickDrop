"""Operações no banco relacionadas aos clips (textos colados) de uma sala."""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Clip


async def list_clips(db: AsyncSession, room_id: str) -> list[Clip]:
    """Clips da sala, do mais antigo para o mais novo."""
    query = select(Clip).where(Clip.room_id == room_id).order_by(Clip.created_at)
    result = await db.execute(query)
    return list(result.scalars())


async def count_clips(db: AsyncSession, room_id: str) -> int:
    result = await db.execute(select(func.count()).select_from(Clip).where(Clip.room_id == room_id))
    return result.scalar_one()


async def find_clip(db: AsyncSession, room_id: str, clip_id: str) -> Clip | None:
    """Busca um clip pelo id, mas só dentro da sala."""
    query = select(Clip).where(Clip.id == clip_id, Clip.room_id == room_id)
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def save_clip(db: AsyncSession, room_id: str, clip_id: str, ciphertext: bytes) -> Clip:
    clip = Clip(id=clip_id, room_id=room_id, ciphertext=ciphertext)
    db.add(clip)
    await db.commit()
    return clip


async def delete_clip(db: AsyncSession, clip: Clip) -> None:
    await db.delete(clip)
    await db.commit()
