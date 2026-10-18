"""Rotas dos arquivos de uma sala: enviar, listar, baixar e apagar.

Todo arquivo chega já criptografado pelo navegador; o servidor nunca vê o conteúdo nem o nome.
Qualquer tipo de arquivo é aceito. Os únicos limites são de tamanho.
"""

from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Header, HTTPException, Request, Response
from fastapi.responses import FileResponse as DiskFileResponse
from starlette.requests import ClientDisconnect

from app import file_service, storage
from app.config import BYTES_PER_MEGABYTE, get_settings
from app.dependencies import Connections, CurrentRoom, Database, ItemId
from app.encoding import from_base64url, to_base64url
from app.models import StoredFile
from app.schemas import FileResponse

router = APIRouter(prefix="/api/rooms/{code}/files", tags=["arquivos"])

# O arquivo criptografado é um pouco maior que o original (cabeçalho e uma etiqueta por bloco de 1 MB).
# Esta folga evita recusar um arquivo de exatamente MAX_FILE_SIZE_MB por causa desse acréscimo.
ENCRYPTION_OVERHEAD_ALLOWANCE_BYTES = BYTES_PER_MEGABYTE

# Um arquivo criptografado nunca é vazio: tem pelo menos o cabeçalho (24 bytes) e uma etiqueta (17 bytes).
MIN_ENCRYPTED_FILE_BYTES = 41

MAX_META_BYTES = 4096

# Códigos que o navegador entende para mostrar a mensagem certa.
FILE_TOO_LARGE = "file_too_large"
ROOM_FULL = "room_full"


def _to_file_response(stored_file: StoredFile) -> FileResponse:
    return FileResponse(
        id=stored_file.id,
        encrypted_meta=to_base64url(stored_file.encrypted_meta),
        size_bytes=stored_file.size_bytes,
        created_at=stored_file.created_at_utc,
    )


def _read_encrypted_meta(header_value: str) -> bytes:
    try:
        encrypted_meta = from_base64url(header_value)
    except ValueError as error:
        raise HTTPException(status_code=422, detail="Metadados inválidos.") from error
    if not encrypted_meta or len(encrypted_meta) > MAX_META_BYTES:
        raise HTTPException(status_code=422, detail="Metadados inválidos.")
    return encrypted_meta


@router.get("")
async def list_room_files(room: CurrentRoom, db: Database) -> list[FileResponse]:
    """Lista os arquivos da sala."""
    stored_files = await file_service.list_files(db, room.id)
    return [_to_file_response(stored_file) for stored_file in stored_files]


@router.post("", status_code=201)
async def upload_file(
    request: Request,
    room: CurrentRoom,
    db: Database,
    connections: Connections,
    x_file_meta: Annotated[str, Header()],
) -> FileResponse:
    """Recebe um arquivo já criptografado (o corpo da requisição).

    O cabeçalho `X-File-Meta` leva o nome, o tipo e o tamanho originais, também criptografados.
    """
    encrypted_meta = _read_encrypted_meta(x_file_meta)

    settings = get_settings()
    file_limit_bytes = settings.max_file_size_bytes + ENCRYPTION_OVERHEAD_ALLOWANCE_BYTES
    room_space_left_bytes = settings.max_room_size_bytes - await file_service.total_size_of_room(db, room.id)
    room_is_the_limit = room_space_left_bytes < file_limit_bytes
    max_bytes = room_space_left_bytes if room_is_the_limit else file_limit_bytes
    limit_error = ROOM_FULL if room_is_the_limit else FILE_TOO_LARGE
    if max_bytes <= 0:
        raise HTTPException(status_code=413, detail=ROOM_FULL)

    # Se o navegador avisou o tamanho antes de enviar, recusamos sem nem começar a gravar.
    declared_size = request.headers.get("content-length")
    if declared_size and declared_size.isdigit() and int(declared_size) > max_bytes:
        raise HTTPException(status_code=413, detail=limit_error)

    file_id = str(uuid4())
    try:
        size_bytes = await storage.save_upload(room.id, file_id, request.stream(), max_bytes)
    except storage.FileTooLargeError as error:
        raise HTTPException(status_code=413, detail=limit_error) from error
    except ClientDisconnect as error:
        # O aparelho desistiu no meio do envio (comum no celular, quando a tela apaga ou o Wi-Fi cai).
        # O arquivo parcial já foi apagado por save_upload; ninguém está esperando resposta.
        raise HTTPException(status_code=400, detail="upload_interrupted") from error

    if size_bytes < MIN_ENCRYPTED_FILE_BYTES:
        storage.delete_file(room.id, file_id)
        raise HTTPException(status_code=422, detail="Arquivo inválido.")

    stored_file = await file_service.save_file_record(db, room.id, file_id, encrypted_meta, size_bytes)
    file_response = _to_file_response(stored_file)
    await connections.broadcast(
        room.code, {"type": "file_added", "file": file_response.model_dump(mode="json")}
    )
    return file_response


@router.get("/{file_id}")
async def download_file(file_id: ItemId, room: CurrentRoom, db: Database) -> DiskFileResponse:
    """Entrega o arquivo criptografado. Quem descriptografa (e dá o nome de volta) é o navegador."""
    stored_file = await file_service.find_file(db, room.id, file_id)
    path = storage.file_path(room.id, file_id)
    if stored_file is None or not path.exists():
        raise HTTPException(status_code=404, detail="Arquivo não encontrado.")

    return DiskFileResponse(
        path,
        media_type="application/octet-stream",
        # Sempre baixar, nunca abrir no navegador. O nome real só existe dentro do arquivo criptografado.
        headers={
            "Content-Disposition": 'attachment; filename="quickdrop-file"',
            "X-Content-Type-Options": "nosniff",
            "Cache-Control": "no-store",
        },
    )


@router.delete("/{file_id}", status_code=204)
async def delete_room_file(
    file_id: ItemId, room: CurrentRoom, db: Database, connections: Connections
) -> Response:
    """Apaga um arquivo da sala (do disco e do banco)."""
    stored_file = await file_service.find_file(db, room.id, file_id)
    if stored_file is None:
        raise HTTPException(status_code=404, detail="Arquivo não encontrado.")

    storage.delete_file(room.id, file_id)
    await file_service.delete_file_record(db, stored_file)
    await connections.broadcast(room.code, {"type": "file_deleted", "file_id": file_id})
    return Response(status_code=204)
