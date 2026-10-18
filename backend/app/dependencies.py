"""Dependências do FastAPI: coisas que várias rotas precisam receber prontas."""

import asyncio
from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends, HTTPException, Path, Request
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.requests import HTTPConnection

from app.models import Room
from app.rate_limit import RateLimits
from app.realtime import ConnectionManager
from app.room_service import find_active_room
from app.security import ROOM_CODE_PATTERN
from app.session import has_session_for_room

UUID_PATTERN = r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"

# Código da sala na URL, já validado (6 caracteres do alfabeto permitido).
RoomCode = Annotated[str, Path(pattern=ROOM_CODE_PATTERN)]

# Id de arquivo ou de clip na URL: um UUID (o servidor é quem cria os ids).
ItemId = Annotated[str, Path(pattern=UUID_PATTERN)]


async def get_db(connection: HTTPConnection) -> AsyncIterator[AsyncSession]:
    """Entrega uma sessão do banco para a rota e a fecha no final."""
    async with connection.app.state.session_maker() as session:
        yield session


async def get_connections(connection: HTTPConnection) -> ConnectionManager:
    """Entrega o gerenciador das conexões em tempo real."""
    return connection.app.state.connections


async def get_rate_limits(connection: HTTPConnection) -> RateLimits:
    """Entrega os limites de tentativas."""
    return connection.app.state.rate_limits


async def get_upload_lock(connection: HTTPConnection) -> asyncio.Lock:
    """Entrega o cadeado que organiza a conferência de espaço dos envios."""
    return connection.app.state.upload_lock


async def get_current_room(
    code: RoomCode,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Room:
    """Devolve a sala da URL, mas só se o dispositivo tiver entrado nela (cookie válido)."""
    room = await find_active_room(db, code)
    if room is None:
        raise HTTPException(status_code=404, detail="Sala não encontrada ou expirada.")
    if not has_session_for_room(request.cookies, room):
        raise HTTPException(status_code=401, detail="Entre na sala primeiro.")
    return room


# Apelidos para usar nas rotas: `db: Database` e `room: CurrentRoom`.
Database = Annotated[AsyncSession, Depends(get_db)]
CurrentRoom = Annotated[Room, Depends(get_current_room)]
Connections = Annotated[ConnectionManager, Depends(get_connections)]
Limits = Annotated[RateLimits, Depends(get_rate_limits)]
UploadLock = Annotated[asyncio.Lock, Depends(get_upload_lock)]
