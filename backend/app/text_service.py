"""Operações no banco relacionadas ao texto compartilhado de uma sala."""

from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import RoomText, utc_now


async def _find_text(db: AsyncSession, room_id: str) -> RoomText | None:
    # populate_existing: sempre lê o valor atual do banco, mesmo que a sessão já tenha uma cópia.
    query = select(RoomText).where(RoomText.room_id == room_id).execution_options(populate_existing=True)
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def get_text(db: AsyncSession, room_id: str) -> RoomText:
    """Devolve o texto da sala. A primeira consulta cria o texto vazio (versão 0)."""
    text = await _find_text(db, room_id)
    if text is None:
        db.add(RoomText(room_id=room_id))
        try:
            await db.commit()
        except IntegrityError:
            await db.rollback()  # outro aparelho criou ao mesmo tempo; basta ler o dele
        text = await _find_text(db, room_id)
    return text


async def replace_text(
    db: AsyncSession, room_id: str, ciphertext: bytes, base_version: int
) -> RoomText | None:
    """Troca o texto, mas só se `base_version` for a versão atual.

    Se outro aparelho alterou o texto antes, a versão já mudou e nada é trocado (devolve None).
    A conferência e a troca acontecem numa única instrução do banco, então duas alterações
    ao mesmo tempo nunca passam as duas.
    """
    await get_text(db, room_id)  # garante que o texto existe
    change = (
        update(RoomText)
        .where(RoomText.room_id == room_id, RoomText.version == base_version)
        .values(ciphertext=ciphertext, version=RoomText.version + 1, updated_at=utc_now())
    )
    result = await db.execute(change)
    await db.commit()
    if result.rowcount == 0:
        return None
    return await _find_text(db, room_id)
