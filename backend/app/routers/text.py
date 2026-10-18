"""Rotas do texto compartilhado da sala (o editor).

O texto chega criptografado pelo navegador; o servidor só guarda e repassa bytes embaralhados.
Quando dois aparelhos editam ao mesmo tempo, vale a versão: quem tenta salvar sobre uma
versão que já mudou recebe 409 com o texto atual, e o navegador decide o que fazer.
"""

from fastapi import APIRouter, HTTPException

from app import text_service
from app.config import get_settings
from app.dependencies import Connections, CurrentRoom, Database
from app.encoding import from_base64url, to_base64url
from app.models import RoomText
from app.schemas import TextResponse, UpdateTextRequest

router = APIRouter(prefix="/api/rooms/{code}/text", tags=["texto"])

# A criptografia acrescenta 40 bytes ao texto (número usado uma vez e etiqueta de verificação).
ENCRYPTION_OVERHEAD_ALLOWANCE_BYTES = 64

TEXT_TOO_LARGE = "text_too_large"
TEXT_CONFLICT = "text_conflict"


def _to_text_response(room_text: RoomText) -> TextResponse:
    return TextResponse(ciphertext=to_base64url(room_text.ciphertext), version=room_text.version)


@router.get("")
async def get_shared_text(room: CurrentRoom, db: Database) -> TextResponse:
    """O texto compartilhado atual."""
    return _to_text_response(await text_service.get_text(db, room.id))


@router.put("")
async def update_shared_text(
    body: UpdateTextRequest, room: CurrentRoom, db: Database, connections: Connections
) -> TextResponse:
    """Salva o texto, se `base_version` ainda for a versão atual. Senão, 409 com o texto atual."""
    ciphertext = from_base64url(body.ciphertext)
    if len(ciphertext) > get_settings().max_text_size_bytes + ENCRYPTION_OVERHEAD_ALLOWANCE_BYTES:
        raise HTTPException(status_code=413, detail=TEXT_TOO_LARGE)

    updated = await text_service.replace_text(db, room.id, ciphertext, body.base_version)
    if updated is None:
        current = _to_text_response(await text_service.get_text(db, room.id))
        raise HTTPException(status_code=409, detail={"code": TEXT_CONFLICT, "current": current.model_dump()})

    response = _to_text_response(updated)
    await connections.broadcast(room.code, {"type": "text_updated", **response.model_dump()})
    return response
