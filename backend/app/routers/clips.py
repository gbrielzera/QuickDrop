"""Rotas dos clips: textos colados na sala, cada um guardado criptografado."""

from uuid import uuid4

from fastapi import APIRouter, HTTPException, Response

from app import clip_service
from app.config import get_settings
from app.dependencies import Connections, CurrentRoom, Database, ItemId
from app.encoding import from_base64url, to_base64url
from app.models import Clip
from app.schemas import ClipResponse, CreateClipRequest

router = APIRouter(prefix="/api/rooms/{code}/clips", tags=["clips"])

# A criptografia acrescenta 40 bytes ao texto (número usado uma vez e etiqueta de verificação).
ENCRYPTION_OVERHEAD_ALLOWANCE_BYTES = 64
MIN_ENCRYPTED_CLIP_BYTES = 40

CLIP_TOO_LARGE = "clip_too_large"
CLIPS_FULL = "clips_full"


def _to_clip_response(clip: Clip) -> ClipResponse:
    return ClipResponse(id=clip.id, ciphertext=to_base64url(clip.ciphertext), created_at=clip.created_at_utc)


@router.get("")
async def list_room_clips(room: CurrentRoom, db: Database) -> list[ClipResponse]:
    """Lista os clips da sala."""
    return [_to_clip_response(clip) for clip in await clip_service.list_clips(db, room.id)]


@router.post("", status_code=201)
async def create_clip(
    body: CreateClipRequest, room: CurrentRoom, db: Database, connections: Connections
) -> ClipResponse:
    """Guarda um novo clip (já criptografado)."""
    settings = get_settings()
    ciphertext = from_base64url(body.ciphertext)
    if len(ciphertext) < MIN_ENCRYPTED_CLIP_BYTES:
        raise HTTPException(status_code=422, detail="Clip inválido.")
    if len(ciphertext) > settings.max_clip_size_bytes + ENCRYPTION_OVERHEAD_ALLOWANCE_BYTES:
        raise HTTPException(status_code=413, detail=CLIP_TOO_LARGE)
    if await clip_service.count_clips(db, room.id) >= settings.max_clips_per_room:
        raise HTTPException(status_code=413, detail=CLIPS_FULL)

    clip = await clip_service.save_clip(db, room.id, str(uuid4()), ciphertext)
    clip_response = _to_clip_response(clip)
    await connections.broadcast(
        room.code, {"type": "clip_added", "clip": clip_response.model_dump(mode="json")}
    )
    return clip_response


@router.delete("/{clip_id}", status_code=204)
async def delete_room_clip(
    clip_id: ItemId, room: CurrentRoom, db: Database, connections: Connections
) -> Response:
    """Apaga um clip."""
    clip = await clip_service.find_clip(db, room.id, clip_id)
    if clip is None:
        raise HTTPException(status_code=404, detail="Clip não encontrado.")

    await clip_service.delete_clip(db, clip)
    await connections.broadcast(room.code, {"type": "clip_deleted", "clip_id": clip_id})
    return Response(status_code=204)
