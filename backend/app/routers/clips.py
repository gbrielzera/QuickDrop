"""Rotas dos clips: textos (`/clips`) e blocos de código (`/code-clips`) colados na sala.

Cada clip é guardado criptografado. As duas rotas são iguais; a função `create_clips_router`
monta uma para cada tabela.
"""

from collections.abc import Callable
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Response

from app import clip_service
from app.config import Settings, get_settings
from app.dependencies import Connections, CurrentRoom, Database, ItemId
from app.encoding import from_base64url, to_base64url
from app.models import Clip, CodeClip, EncryptedClip
from app.schemas import ClipResponse, CreateClipRequest

# A criptografia acrescenta 40 bytes ao texto (número usado uma vez e etiqueta de verificação).
ENCRYPTION_OVERHEAD_ALLOWANCE_BYTES = 64
MIN_ENCRYPTED_CLIP_BYTES = 40

CLIP_TOO_LARGE = "clip_too_large"
CLIPS_FULL = "clips_full"


def _to_clip_response(clip: EncryptedClip) -> ClipResponse:
    return ClipResponse(id=clip.id, ciphertext=to_base64url(clip.ciphertext), created_at=clip.created_at_utc)


def create_clips_router(
    prefix: str,
    model: type[EncryptedClip],
    max_clip_bytes: Callable[[Settings], int],
    event_prefix: str,
    tag: str,
) -> APIRouter:
    """Monta as rotas dos clips de uma tabela.

    `max_clip_bytes` diz o tamanho máximo de cada clip e `event_prefix` dá nome aos avisos
    enviados aos outros aparelhos ("clip" gera clip_added e clip_deleted).
    """
    router = APIRouter(prefix=f"/api/rooms/{{code}}/{prefix}", tags=[tag])

    @router.get("")
    async def list_room_clips(room: CurrentRoom, db: Database) -> list[ClipResponse]:
        """Lista os clips da sala."""
        return [_to_clip_response(clip) for clip in await clip_service.list_clips(db, model, room.id)]

    @router.post("", status_code=201)
    async def create_clip(
        body: CreateClipRequest, room: CurrentRoom, db: Database, connections: Connections
    ) -> ClipResponse:
        """Guarda um novo clip (já criptografado)."""
        settings = get_settings()
        ciphertext = from_base64url(body.ciphertext)
        if len(ciphertext) < MIN_ENCRYPTED_CLIP_BYTES:
            raise HTTPException(status_code=422, detail="Clip inválido.")
        if len(ciphertext) > max_clip_bytes(settings) + ENCRYPTION_OVERHEAD_ALLOWANCE_BYTES:
            raise HTTPException(status_code=413, detail=CLIP_TOO_LARGE)
        if await clip_service.count_clips(db, model, room.id) >= settings.max_clips_per_room:
            raise HTTPException(status_code=413, detail=CLIPS_FULL)

        clip = await clip_service.save_clip(db, model, room.id, str(uuid4()), ciphertext)
        clip_response = _to_clip_response(clip)
        await connections.broadcast(
            room.code, {"type": f"{event_prefix}_added", "clip": clip_response.model_dump(mode="json")}
        )
        return clip_response

    @router.delete("/{clip_id}", status_code=204)
    async def delete_room_clip(
        clip_id: ItemId, room: CurrentRoom, db: Database, connections: Connections
    ) -> Response:
        """Apaga um clip."""
        clip = await clip_service.find_clip(db, model, room.id, clip_id)
        if clip is None:
            raise HTTPException(status_code=404, detail="Clip não encontrado.")

        await clip_service.delete_clip(db, clip)
        await connections.broadcast(room.code, {"type": f"{event_prefix}_deleted", "clip_id": clip_id})
        return Response(status_code=204)

    return router


text_clips_router = create_clips_router(
    "clips", Clip, lambda settings: settings.max_clip_size_bytes, "clip", "clips"
)
code_clips_router = create_clips_router(
    "code-clips",
    CodeClip,
    lambda settings: settings.max_code_clip_size_bytes,
    "code_clip",
    "blocos de código",
)
