"""Arquivos criptografados no disco: storage/{id da sala}/{id do arquivo}.

O servidor só guarda bytes embaralhados. O nome, o tipo e o conteúdo originais nunca chegam aqui.
"""

import asyncio
import shutil
from collections.abc import AsyncIterator
from pathlib import Path

import aiofiles

from app.config import get_settings

PARTIAL_UPLOAD_SUFFIX = ".part"


class FileTooLargeError(Exception):
    """O arquivo enviado passou do tamanho máximo permitido."""


def _room_directory(room_id: str) -> Path:
    return get_settings().storage_dir / room_id


def file_path(room_id: str, file_id: str) -> Path:
    """Caminho do arquivo no disco."""
    return _room_directory(room_id) / file_id


async def save_upload(room_id: str, file_id: str, chunks: AsyncIterator[bytes], max_bytes: int) -> int:
    """Grava o arquivo enviado aos poucos (sem carregá-lo inteiro na memória) e devolve o tamanho.

    O tamanho é conferido durante o envio: se passar de `max_bytes`, para na hora e apaga o que gravou.
    """
    final_path = file_path(room_id, file_id)
    final_path.parent.mkdir(parents=True, exist_ok=True)
    partial_path = final_path.with_suffix(PARTIAL_UPLOAD_SUFFIX)

    size = 0
    saved = False
    try:
        async with aiofiles.open(partial_path, "wb") as output:
            async for chunk in chunks:
                size += len(chunk)
                if size > max_bytes:
                    raise FileTooLargeError
                await output.write(chunk)
        partial_path.replace(final_path)
        saved = True
    finally:
        if not saved:
            partial_path.unlink(missing_ok=True)
    return size


def delete_file(room_id: str, file_id: str) -> None:
    """Apaga o arquivo do disco (não falha se ele já não existir)."""
    file_path(room_id, file_id).unlink(missing_ok=True)


async def delete_room_directory(room_id: str) -> None:
    """Apaga todos os arquivos de uma sala (não falha se a pasta não existir)."""
    # Apagar pode demorar com muitos arquivos grandes; fazemos em outra thread para não travar o servidor.
    await asyncio.to_thread(shutil.rmtree, _room_directory(room_id), ignore_errors=True)
