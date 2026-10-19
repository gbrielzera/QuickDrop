"""Código da sala e verificação da authKey enviada pelo navegador."""

import hashlib
import hmac
import secrets

from app.config import get_settings

# Sem 0/O e 1/I/L, que são fáceis de confundir ao digitar. O navegador usa o mesmo alfabeto no segredo.
ROOM_CODE_ALPHABET = "23456789ABCDEFGHJKMNPQRSTUVWXYZ"
ROOM_CODE_LENGTH = 6
ROOM_CODE_PATTERN = f"^[{ROOM_CODE_ALPHABET}]{{{ROOM_CODE_LENGTH}}}$"


def generate_room_code() -> str:
    """Gera um código aleatório para a sala. Usa `secrets` (seguro), não `random`."""
    return "".join(secrets.choice(ROOM_CODE_ALPHABET) for _ in range(ROOM_CODE_LENGTH))


def hash_auth_key(auth_key: str) -> str:
    """Guarda a authKey de forma que quem roubar só o banco de dados não consiga conferir palpites.

    A authKey já sai do Argon2id do navegador (caro de propósito), então repetir um Argon2 aqui só custaria
    ~300 ms de CPU em cada entrada, num servidor pequeno, sem tornar o ataque muito mais difícil. Usamos um
    HMAC-SHA256 com a SECRET_KEY como chave: é instantâneo e, sem a SECRET_KEY (que não fica no banco),
    o hash roubado não serve nem para testar senhas.
    """
    secret_key = get_settings().secret_key.encode()
    return hmac.new(secret_key, auth_key.encode(), hashlib.sha256).hexdigest()


def verify_auth_key(auth_key: str, auth_hash: str) -> bool:
    """Confere se a authKey enviada corresponde ao hash guardado (em tempo constante)."""
    return hmac.compare_digest(hash_auth_key(auth_key), auth_hash)
