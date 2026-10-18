"""Rotas dos textos compartilhados da sala: o texto (`/text`) e o código (`/source`).

O conteúdo chega criptografado pelo navegador; o servidor só guarda e repassa bytes embaralhados.
Quando dois aparelhos editam ao mesmo tempo, vale a versão: quem tenta salvar sobre uma
versão que já mudou recebe 409 com o conteúdo atual, e o navegador decide o que fazer.

As duas rotas são iguais; a função `create_document_router` monta uma para cada tabela.
"""

from fastapi import APIRouter, HTTPException

from app import document_service
from app.config import get_settings
from app.dependencies import Connections, CurrentRoom, Database
from app.encoding import from_base64url, to_base64url
from app.models import EncryptedDocument, RoomText, SourceCode
from app.schemas import TextResponse, UpdateTextRequest

# A criptografia acrescenta 40 bytes ao conteúdo (número usado uma vez e etiqueta de verificação).
ENCRYPTION_OVERHEAD_ALLOWANCE_BYTES = 64

TEXT_TOO_LARGE = "text_too_large"
TEXT_CONFLICT = "text_conflict"


def _to_response(document: EncryptedDocument) -> TextResponse:
    return TextResponse(ciphertext=to_base64url(document.ciphertext), version=document.version)


def create_document_router(
    prefix: str, model: type[EncryptedDocument], updated_event: str, tag: str
) -> APIRouter:
    """Monta as rotas de um documento. `updated_event` é o aviso enviado aos outros aparelhos."""
    router = APIRouter(prefix=f"/api/rooms/{{code}}/{prefix}", tags=[tag])

    @router.get("")
    async def get_document(room: CurrentRoom, db: Database) -> TextResponse:
        """O conteúdo atual (vazio e versão 0 enquanto ninguém escreveu)."""
        return _to_response(await document_service.get_document(db, model, room.id))

    @router.put("")
    async def update_document(
        body: UpdateTextRequest, room: CurrentRoom, db: Database, connections: Connections
    ) -> TextResponse:
        """Salva o conteúdo, se `base_version` ainda for a versão atual. Senão, 409 com o conteúdo atual."""
        ciphertext = from_base64url(body.ciphertext)
        if len(ciphertext) > get_settings().max_text_size_bytes + ENCRYPTION_OVERHEAD_ALLOWANCE_BYTES:
            raise HTTPException(status_code=413, detail=TEXT_TOO_LARGE)

        updated = await document_service.replace_document(db, model, room.id, ciphertext, body.base_version)
        if updated is None:
            current = _to_response(await document_service.get_document(db, model, room.id))
            raise HTTPException(
                status_code=409, detail={"code": TEXT_CONFLICT, "current": current.model_dump()}
            )

        response = _to_response(updated)
        await connections.broadcast(room.code, {"type": updated_event, **response.model_dump()})
        return response

    return router


text_router = create_document_router("text", RoomText, "text_updated", "texto")
source_router = create_document_router("source", SourceCode, "source_updated", "código")
