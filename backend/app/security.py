"""Código da sala e verificação da authKey enviada pelo navegador."""

import asyncio
import secrets
from concurrent.futures import ThreadPoolExecutor

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError

# Sem 0/O e 1/I/L, que são fáceis de confundir ao digitar. O navegador usa o mesmo alfabeto no segredo.
ROOM_CODE_ALPHABET = "23456789ABCDEFGHJKMNPQRSTUVWXYZ"
ROOM_CODE_LENGTH = 6
ROOM_CODE_PATTERN = f"^[{ROOM_CODE_ALPHABET}]{{{ROOM_CODE_LENGTH}}}$"

# O navegador já aplica o Argon2 na senha; o hash guardado aqui só protege a authKey, que tem 256 bits
# de aleatoriedade. Por isso usamos o mínimo recomendado pela OWASP (19 MiB, 2 passes): o padrão da
# biblioteca (64 MiB) deixaria poucas entradas simultâneas esgotarem a memória de um servidor pequeno.
ARGON2_MEMORY_COST_KIB = 19 * 1024
ARGON2_TIME_COST = 2
ARGON2_PARALLELISM = 1

# No máximo 2 cálculos ao mesmo tempo; os outros esperam na fila.
MAX_CONCURRENT_HASHES = 2

_password_hasher = PasswordHasher(
    memory_cost=ARGON2_MEMORY_COST_KIB, time_cost=ARGON2_TIME_COST, parallelism=ARGON2_PARALLELISM
)
_hash_workers = ThreadPoolExecutor(max_workers=MAX_CONCURRENT_HASHES, thread_name_prefix="argon2")


def generate_room_code() -> str:
    """Gera um código aleatório para a sala. Usa `secrets` (seguro), não `random`."""
    return "".join(secrets.choice(ROOM_CODE_ALPHABET) for _ in range(ROOM_CODE_LENGTH))


async def hash_auth_key(auth_key: str) -> str:
    """Guarda a authKey de forma que ninguém consiga recuperá-la (Argon2).

    O Argon2 é lento de propósito; rodamos em outra thread para não travar o servidor.
    """
    return await asyncio.get_running_loop().run_in_executor(_hash_workers, _password_hasher.hash, auth_key)


async def verify_auth_key(auth_key: str, auth_hash: str) -> bool:
    """Confere se a authKey enviada corresponde ao hash guardado."""
    try:
        return await asyncio.get_running_loop().run_in_executor(
            _hash_workers, _password_hasher.verify, auth_hash, auth_key
        )
    except (VerifyMismatchError, InvalidHashError):
        return False
