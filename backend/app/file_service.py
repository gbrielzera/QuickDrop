"""Operações no banco relacionadas aos arquivos de uma sala."""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import StoredFile


async def list_files(db: AsyncSession, room_id: str) -> list[StoredFile]:
    """Arquivos da sala, do mais antigo para o mais novo."""
    query = select(StoredFile).where(StoredFile.room_id == room_id).order_by(StoredFile.created_at)
    result = await db.execute(query)
    return list(result.scalars())


async def find_file(db: AsyncSession, room_id: str, file_id: str) -> StoredFile | None:
    """Busca um arquivo pelo id, mas só dentro da sala (um arquivo de outra sala não é encontrado)."""
    query = select(StoredFile).where(StoredFile.id == file_id, StoredFile.room_id == room_id)
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def total_size_of_room(db: AsyncSession, room_id: str) -> int:
    """Soma do tamanho de todos os arquivos da sala, em bytes."""
    query = select(func.coalesce(func.sum(StoredFile.size_bytes), 0)).where(StoredFile.room_id == room_id)
    result = await db.execute(query)
    return result.scalar_one()


async def total_size_of_all_files(db: AsyncSession) -> int:
    """Soma do tamanho dos arquivos de todas as salas, em bytes."""
    result = await db.execute(select(func.coalesce(func.sum(StoredFile.size_bytes), 0)))
    return result.scalar_one()


async def save_file_record(
    db: AsyncSession, room_id: str, file_id: str, encrypted_meta: bytes, size_bytes: int
) -> StoredFile:
    """Registra no banco um arquivo que já foi gravado no disco."""
    stored_file = StoredFile(
        id=file_id, room_id=room_id, encrypted_meta=encrypted_meta, size_bytes=size_bytes
    )
    db.add(stored_file)
    await db.commit()
    return stored_file


async def delete_file_record(db: AsyncSession, stored_file: StoredFile) -> None:
    await db.delete(stored_file)
    await db.commit()
