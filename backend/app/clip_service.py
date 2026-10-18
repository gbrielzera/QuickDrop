"""Operações no banco relacionadas aos clips de uma sala (os de texto e os de código).

Os dois funcionam do mesmo jeito; o que muda é a tabela (`model`): Clip ou CodeClip.
"""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import EncryptedClip


async def list_clips(db: AsyncSession, model: type[EncryptedClip], room_id: str):
    """Clips da sala, do mais antigo para o mais novo."""
    query = select(model).where(model.room_id == room_id).order_by(model.created_at)
    result = await db.execute(query)
    return list(result.scalars())


async def count_clips(db: AsyncSession, model: type[EncryptedClip], room_id: str) -> int:
    result = await db.execute(select(func.count()).select_from(model).where(model.room_id == room_id))
    return result.scalar_one()


async def find_clip(db: AsyncSession, model: type[EncryptedClip], room_id: str, clip_id: str):
    """Busca um clip pelo id, mas só dentro da sala."""
    query = select(model).where(model.id == clip_id, model.room_id == room_id)
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def save_clip(
    db: AsyncSession, model: type[EncryptedClip], room_id: str, clip_id: str, ciphertext: bytes
):
    clip = model(id=clip_id, room_id=room_id, ciphertext=ciphertext)
    db.add(clip)
    await db.commit()
    return clip


async def delete_clip(db: AsyncSession, clip: EncryptedClip) -> None:
    await db.delete(clip)
    await db.commit()
