"""Conexão com o banco de dados.

Começamos com SQLite (um arquivo só, sem instalar nada). Para usar PostgreSQL no futuro,
basta trocar DATABASE_URL no .env.
"""

from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Classe-mãe de todas as tabelas."""


def create_engine(database_url: str) -> AsyncEngine:
    """Cria a conexão com o banco."""
    engine = create_async_engine(database_url)
    if database_url.startswith("sqlite"):
        event.listen(engine.sync_engine, "connect", _turn_on_foreign_keys)
    return engine


def _turn_on_foreign_keys(connection, _connection_record) -> None:
    # O SQLite ignora chaves estrangeiras (como "apagar os arquivos junto com a sala") se não pedirmos.
    cursor = connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


def create_session_maker(engine: AsyncEngine) -> async_sessionmaker:
    """Cria a "fábrica" de sessões: cada requisição abre a sua."""
    return async_sessionmaker(engine, expire_on_commit=False)


async def create_tables(engine: AsyncEngine) -> None:
    """Cria as tabelas que ainda não existem."""
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
