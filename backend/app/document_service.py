"""Operações no banco relacionadas aos textos compartilhados de uma sala (o texto e o código).

Os dois funcionam do mesmo jeito; o que muda é a tabela (`model`): RoomText ou SourceCode.
"""

from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import EncryptedDocument, utc_now


async def _find_document(db: AsyncSession, model: type[EncryptedDocument], room_id: str):
    # populate_existing: sempre lê o valor atual do banco, mesmo que a sessão já tenha uma cópia.
    query = select(model).where(model.room_id == room_id).execution_options(populate_existing=True)
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def get_document(db: AsyncSession, model: type[EncryptedDocument], room_id: str):
    """Devolve o documento da sala. A primeira consulta cria um vazio (versão 0)."""
    document = await _find_document(db, model, room_id)
    if document is None:
        db.add(model(room_id=room_id))
        try:
            await db.commit()
        except IntegrityError:
            await db.rollback()  # outro aparelho criou ao mesmo tempo; basta ler o dele
        document = await _find_document(db, model, room_id)
    return document


async def replace_document(
    db: AsyncSession, model: type[EncryptedDocument], room_id: str, ciphertext: bytes, base_version: int
):
    """Troca o documento, mas só se `base_version` for a versão atual.

    Se outro aparelho alterou antes, a versão já mudou e nada é trocado (devolve None).
    A conferência e a troca acontecem numa única instrução do banco, então duas alterações
    ao mesmo tempo nunca passam as duas.
    """
    await get_document(db, model, room_id)  # garante que o documento existe
    change = (
        update(model)
        .where(model.room_id == room_id, model.version == base_version)
        .values(ciphertext=ciphertext, version=model.version + 1, updated_at=utc_now())
    )
    result = await db.execute(change)
    await db.commit()
    if result.rowcount == 0:
        return None
    return await _find_document(db, model, room_id)
