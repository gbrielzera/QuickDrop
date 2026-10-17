"""Código da sala e verificação da authKey enviada pelo navegador."""

import asyncio
import secrets

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError

# Sem 0/O e 1/I/L, que são fáceis de confundir ao digitar. O navegador usa o mesmo alfabeto no segredo.
ROOM_CODE_ALPHABET = "23456789ABCDEFGHJKMNPQRSTUVWXYZ"
ROOM_CODE_LENGTH = 6
ROOM_CODE_PATTERN = f"^[{ROOM_CODE_ALPHABET}]{{{ROOM_CODE_LENGTH}}}$"

_password_hasher = PasswordHasher()


def generate_room_code() -> str:
    """Gera um código aleatório para a sala. Usa `secrets` (seguro), não `random`."""
    return "".join(secrets.choice(ROOM_CODE_ALPHABET) for _ in range(ROOM_CODE_LENGTH))


async def hash_auth_key(auth_key: str) -> str:
    """Guarda a authKey de forma que ninguém consiga recuperá-la (Argon2).

    O Argon2 é lento de propósito; rodamos em outra thread para não travar o servidor.
    """
    return await asyncio.to_thread(_password_hasher.hash, auth_key)


async def verify_auth_key(auth_key: str, auth_hash: str) -> bool:
    """Confere se a authKey enviada corresponde ao hash guardado."""
    try:
        return await asyncio.to_thread(_password_hasher.verify, auth_hash, auth_key)
    except (VerifyMismatchError, InvalidHashError):
        return False
