"""Dependências do FastAPI: coisas que várias rotas precisam receber prontas."""

from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends, HTTPException, Path, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Room
from app.room_service import find_active_room
from app.security import ROOM_CODE_PATTERN
from app.session import read_session_token, session_cookie_name

UUID_PATTERN = r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"

# Código da sala na URL, já validado (6 caracteres do alfabeto permitido).
RoomCode = Annotated[str, Path(pattern=ROOM_CODE_PATTERN)]

# Id de arquivo na URL: um UUID (o servidor é quem cria os ids).
FileId = Annotated[str, Path(pattern=UUID_PATTERN)]


async def get_db(request: Request) -> AsyncIterator[AsyncSession]:
    """Entrega uma sessão do banco para a rota e a fecha no final."""
    async with request.app.state.session_maker() as session:
        yield session


async def get_current_room(
    code: RoomCode,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Room:
    """Devolve a sala da URL, mas só se o dispositivo tiver entrado nela (cookie válido)."""
    token = request.cookies.get(session_cookie_name(code))
    if token is None or read_session_token(token) != code:
        raise HTTPException(status_code=401, detail="Entre na sala primeiro.")

    room = await find_active_room(db, code)
    if room is None:
        raise HTTPException(status_code=404, detail="Sala não encontrada ou expirada.")
    return room


# Apelidos para usar nas rotas: `db: Database` e `room: CurrentRoom`.
Database = Annotated[AsyncSession, Depends(get_db)]
CurrentRoom = Annotated[Room, Depends(get_current_room)]
