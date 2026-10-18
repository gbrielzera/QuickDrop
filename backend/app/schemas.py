"""Formato dos dados que entram e saem da API de salas."""

from datetime import datetime
from typing import Annotated

from pydantic import AfterValidator, BaseModel, Field, field_validator

from app.config import get_settings
from app.encoding import from_base64url

SALT_BYTES = 16
AUTH_KEY_BYTES = 32


def _must_decode_to(expected_bytes: int):
    """Cria um validador: o texto precisa ser base64url e ter exatamente `expected_bytes` bytes."""

    def check(text: str) -> str:
        if len(from_base64url(text)) != expected_bytes:
            raise ValueError(f"Deve ter {expected_bytes} bytes.")
        return text

    return check


def _must_be_base64url(text: str) -> str:
    """O texto precisa ser base64url válido (de qualquer tamanho)."""
    from_base64url(text)
    return text


Salt = Annotated[str, AfterValidator(_must_decode_to(SALT_BYTES))]
Base64Text = Annotated[str, AfterValidator(_must_be_base64url)]
AuthKey = Annotated[str, AfterValidator(_must_decode_to(AUTH_KEY_BYTES))]


class CreateRoomRequest(BaseModel):
    """Pedido para criar uma sala. A senha nunca é enviada, só a authKey derivada dela."""

    ttl_hours: int
    has_password: bool
    kdf_salt: Salt
    auth_key: AuthKey

    @field_validator("ttl_hours")
    @classmethod
    def ttl_must_be_an_allowed_option(cls, ttl_hours: int) -> int:
        if ttl_hours not in get_settings().ttl_options:
            raise ValueError("Tempo de expiração não permitido.")
        return ttl_hours


class JoinRoomRequest(BaseModel):
    """Pedido para entrar numa sala."""

    auth_key: AuthKey


class CreateRoomResponse(BaseModel):
    code: str
    expires_at: datetime


class RoomParamsResponse(BaseModel):
    """O que o navegador precisa saber antes de entrar, para derivar as chaves."""

    has_password: bool
    kdf_salt: str


class RoomResponse(BaseModel):
    code: str
    has_password: bool
    expires_at: datetime
    # Só o dono (quem criou a sala) pode encerrá-la e trancá-la; a tela usa isto para mostrar os botões.
    is_owner: bool
    is_locked: bool


class LockRoomRequest(BaseModel):
    locked: bool


class FileResponse(BaseModel):
    """Um arquivo da sala. O nome, o tipo e o tamanho originais estão dentro de `encrypted_meta`."""

    id: str
    encrypted_meta: str
    size_bytes: int
    created_at: datetime


class UpdateTextRequest(BaseModel):
    """Novo texto compartilhado (já criptografado) e a versão em que ele se baseou."""

    ciphertext: Base64Text
    base_version: int = Field(ge=0)


class TextResponse(BaseModel):
    """O texto compartilhado criptografado e a versão atual. `ciphertext` vazio = ninguém escreveu ainda."""

    ciphertext: str
    version: int


class CreateClipRequest(BaseModel):
    ciphertext: Base64Text


class ClipResponse(BaseModel):
    id: str
    ciphertext: str
    created_at: datetime
