"""Rotas para criar uma sala, entrar nela e consultar seus dados."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import RoomCode, get_current_room, get_db
from app.encoding import from_base64url, to_base64url
from app.models import Room
from app.room_service import RoomCodeUnavailableError, create_room, find_active_room
from app.schemas import (
    CreateRoomRequest,
    CreateRoomResponse,
    JoinRoomRequest,
    RoomParamsResponse,
    RoomResponse,
)
from app.security import hash_auth_key, verify_auth_key
from app.session import set_session_cookie

router = APIRouter(prefix="/api/rooms", tags=["salas"])

Database = Annotated[AsyncSession, Depends(get_db)]


async def _get_active_room_or_404(db: AsyncSession, room_code: str) -> Room:
    room = await find_active_room(db, room_code)
    if room is None:
        raise HTTPException(status_code=404, detail="Sala não encontrada ou expirada.")
    return room


@router.post("", status_code=201)
async def create_new_room(body: CreateRoomRequest, response: Response, db: Database) -> CreateRoomResponse:
    """Cria uma sala. Quem cria já entra nela (recebe o cookie de sessão)."""
    try:
        room = await create_room(
            db,
            ttl_hours=body.ttl_hours,
            has_password=body.has_password,
            kdf_salt=from_base64url(body.kdf_salt),
            auth_hash=await hash_auth_key(body.auth_key),
        )
    except RoomCodeUnavailableError as error:
        raise HTTPException(status_code=503, detail="Tente criar a sala de novo.") from error

    set_session_cookie(response, room)
    return CreateRoomResponse(code=room.code, expires_at=room.expires_at_utc)


@router.get("/{code}/params")
async def get_room_params(code: RoomCode, db: Database) -> RoomParamsResponse:
    """Antes de entrar, o navegador pergunta o salt para derivar as chaves a partir da senha."""
    room = await _get_active_room_or_404(db, code)
    return RoomParamsResponse(has_password=room.has_password, kdf_salt=to_base64url(room.kdf_salt))


@router.post("/{code}/join")
async def join_room(code: RoomCode, body: JoinRoomRequest, response: Response, db: Database) -> RoomResponse:
    """Entra na sala se a authKey estiver certa; devolve o cookie de sessão."""
    room = await _get_active_room_or_404(db, code)
    if not await verify_auth_key(body.auth_key, room.auth_hash):
        raise HTTPException(status_code=401, detail="Senha incorreta.")

    set_session_cookie(response, room)
    return _to_room_response(room)


@router.get("/{code}")
async def get_room(room: Annotated[Room, Depends(get_current_room)]) -> RoomResponse:
    """Dados da sala. Só quem já entrou consegue ver."""
    return _to_room_response(room)


def _to_room_response(room: Room) -> RoomResponse:
    return RoomResponse(code=room.code, has_password=room.has_password, expires_at=room.expires_at_utc)
