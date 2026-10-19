"""Rotas para criar uma sala, entrar nela e consultar seus dados."""

from fastapi import APIRouter, HTTPException, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.dependencies import Connections, CurrentRoom, Database, Limits, RoomCode
from app.encoding import from_base64url, to_base64url
from app.models import Room
from app.rate_limit import block_if_over_limit, client_address, count_attempt
from app.room_service import (
    REASON_CLOSED,
    RoomCodeUnavailableError,
    count_active_rooms,
    create_room,
    end_room,
    find_active_room,
)
from app.schemas import (
    CreateRoomRequest,
    CreateRoomResponse,
    JoinRoomRequest,
    LockRoomRequest,
    RoomParamsResponse,
    RoomResponse,
)
from app.security import hash_auth_key, verify_auth_key
from app.security_events import FAILED_JOIN, LOCKED_JOIN, NOT_OWNER_ATTEMPT, security_events
from app.session import has_session_for_room, is_room_owner, set_owner_cookie, set_session_cookie

router = APIRouter(prefix="/api/rooms", tags=["salas"])

# Código que o navegador entende para avisar que o servidor atingiu o limite de salas.
SERVER_FULL = "server_full"
NOT_OWNER = "not_owner"
ROOM_LOCKED = "room_locked"


async def _get_active_room_or_404(db: AsyncSession, room_code: str) -> Room:
    room = await find_active_room(db, room_code)
    if room is None:
        raise HTTPException(status_code=404, detail="Sala não encontrada ou expirada.")
    return room


@router.post("", status_code=201)
async def create_new_room(
    body: CreateRoomRequest, request: Request, response: Response, db: Database, limits: Limits
) -> CreateRoomResponse:
    """Cria uma sala. Quem cria já entra nela (recebe o cookie de sessão)."""
    count_attempt(limits.room_creations, client_address(request))
    if await count_active_rooms(db) >= get_settings().max_active_rooms:
        raise HTTPException(status_code=503, detail=SERVER_FULL)
    try:
        room = await create_room(
            db,
            ttl_hours=body.ttl_hours,
            has_password=body.has_password,
            kdf_salt=from_base64url(body.kdf_salt),
            auth_hash=hash_auth_key(body.auth_key),
        )
    except RoomCodeUnavailableError as error:
        raise HTTPException(status_code=503, detail="Tente criar a sala de novo.") from error

    set_session_cookie(response, room)
    set_owner_cookie(response, room)
    return CreateRoomResponse(code=room.code, expires_at=room.expires_at_utc)


@router.get("/{code}/params")
async def get_room_params(
    code: RoomCode, request: Request, db: Database, limits: Limits
) -> RoomParamsResponse:
    """Antes de entrar, o navegador pergunta o salt para derivar as chaves a partir da senha."""
    count_attempt(limits.lookups, client_address(request))
    room = await _get_active_room_or_404(db, code)
    return RoomParamsResponse(has_password=room.has_password, kdf_salt=to_base64url(room.kdf_salt))


@router.post("/{code}/join")
async def join_room(
    code: RoomCode, body: JoinRoomRequest, request: Request, response: Response, db: Database, limits: Limits
) -> RoomResponse:
    """Entra na sala se a authKey estiver certa; devolve o cookie de sessão."""
    address = client_address(request)
    count_attempt(limits.lookups, address)
    room = await _get_active_room_or_404(db, code)

    # Sala trancada: só entra de novo quem já tinha entrado (por exemplo, depois de recarregar a página).
    if room.locked and not has_session_for_room(request.cookies, room):
        security_events.record(LOCKED_JOIN)
        raise HTTPException(status_code=403, detail=ROOM_LOCKED)

    # Quem errou a senha várias vezes espera um pouco, mesmo que a próxima tentativa esteja certa.
    failed_joins_key = f"{address}:{code}"
    block_if_over_limit(limits.failed_joins, failed_joins_key)
    if not verify_auth_key(body.auth_key, room.auth_hash):
        limits.failed_joins.record(failed_joins_key)
        security_events.record(FAILED_JOIN)
        raise HTTPException(status_code=401, detail="Senha incorreta.")
    limits.failed_joins.reset(failed_joins_key)

    set_session_cookie(response, room)
    return _to_room_response(room, request)


@router.get("/{code}")
async def get_room(room: CurrentRoom, request: Request) -> RoomResponse:
    """Dados da sala. Só quem já entrou consegue ver."""
    return _to_room_response(room, request)


@router.put("/{code}/lock")
async def lock_room(body: LockRoomRequest, room: CurrentRoom, request: Request, db: Database) -> RoomResponse:
    """Tranca ou destranca a sala. Só o dono pode."""
    _require_owner(request, room)
    room.locked = body.locked
    db.add(room)
    await db.commit()
    return _to_room_response(room, request)


@router.delete("/{code}", status_code=204)
async def close_room(room: CurrentRoom, request: Request, db: Database, connections: Connections) -> Response:
    """Encerra a sala agora: apaga tudo e avisa os aparelhos conectados.

    Só o dono (o navegador que criou a sala) pode encerrá-la; os convidados não.
    """
    _require_owner(request, room)
    await end_room(db, connections, room, reason=REASON_CLOSED)
    return Response(status_code=204)


def _require_owner(request: Request, room: Room) -> None:
    """Recusa (403) quem não é o dono da sala e anota a tentativa, sem registrar quem foi."""
    if not is_room_owner(request.cookies, room):
        security_events.record(NOT_OWNER_ATTEMPT)
        raise HTTPException(status_code=403, detail=NOT_OWNER)


def _to_room_response(room: Room, request: Request) -> RoomResponse:
    return RoomResponse(
        code=room.code,
        has_password=room.has_password,
        expires_at=room.expires_at_utc,
        is_owner=is_room_owner(request.cookies, room),
        is_locked=room.locked,
    )
