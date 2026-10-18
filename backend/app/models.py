"""Tabelas do banco de dados."""

from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import ForeignKey, LargeBinary, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


def utc_now() -> datetime:
    """Hora atual em UTC. O banco guarda horários em UTC, sem informação de fuso."""
    return datetime.now(UTC).replace(tzinfo=None)


def with_utc_timezone(value: datetime) -> datetime:
    """Marca um horário do banco como UTC, para a API enviar em formato que o JavaScript entende."""
    return value.replace(tzinfo=UTC)


class Room(Base):
    """Uma sala: o espaço temporário onde os dispositivos trocam arquivos e textos."""

    __tablename__ = "rooms"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    code: Mapped[str] = mapped_column(String(6), unique=True, index=True)

    # True quando quem criou a sala escolheu a própria senha (False: o app gerou um segredo).
    has_password: Mapped[bool]

    # Dados para o navegador derivar as chaves. O servidor guarda só o hash da authKey,
    # nunca a senha nem a chave de criptografia.
    kdf_salt: Mapped[bytes] = mapped_column(LargeBinary)
    auth_hash: Mapped[str]

    # Sala trancada: ninguém novo entra (quem já entrou continua). Só o dono tranca e destranca.
    locked: Mapped[bool] = mapped_column(default=False, server_default="0")

    created_at: Mapped[datetime] = mapped_column(default=utc_now)
    expires_at: Mapped[datetime] = mapped_column(index=True)

    @property
    def expires_at_utc(self) -> datetime:
        return with_utc_timezone(self.expires_at)


class StoredFile(Base):
    """Um arquivo enviado para uma sala. O conteúdo fica no disco; aqui ficam só os dados de controle."""

    __tablename__ = "files"

    # O id também é o nome do arquivo no disco: o nome original nunca é usado.
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    room_id: Mapped[str] = mapped_column(ForeignKey("rooms.id", ondelete="CASCADE"), index=True)

    # Nome, tipo e tamanho originais, criptografados no navegador. O servidor não consegue ler.
    encrypted_meta: Mapped[bytes] = mapped_column(LargeBinary)
    # Tamanho do arquivo criptografado (é ele que conta para o limite da sala).
    size_bytes: Mapped[int]

    created_at: Mapped[datetime] = mapped_column(default=utc_now)

    @property
    def created_at_utc(self) -> datetime:
        return with_utc_timezone(self.created_at)


class EncryptedDocument(Base):
    """Base dos textos compartilhados da sala (texto e código): um de cada por sala, criptografado."""

    __abstract__ = True

    room_id: Mapped[str] = mapped_column(ForeignKey("rooms.id", ondelete="CASCADE"), primary_key=True)
    # Vazio enquanto ninguém escreveu nada. O servidor não consegue ler o conteúdo.
    ciphertext: Mapped[bytes] = mapped_column(LargeBinary, default=b"")
    # Sobe 1 a cada alteração. Serve para perceber que outro aparelho mudou o conteúdo antes de nós.
    version: Mapped[int] = mapped_column(default=0)
    updated_at: Mapped[datetime] = mapped_column(default=utc_now)


class RoomText(EncryptedDocument):
    """O texto compartilhado da sala."""

    __tablename__ = "room_texts"


class SourceCode(EncryptedDocument):
    """O código compartilhado da sala (mesmo funcionamento do texto, mas mostrado em fonte monoespaçada)."""

    __tablename__ = "room_source_code"


class EncryptedClip(Base):
    """Base dos clips (textos colados na sala), guardados criptografados."""

    __abstract__ = True

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    room_id: Mapped[str] = mapped_column(ForeignKey("rooms.id", ondelete="CASCADE"), index=True)
    ciphertext: Mapped[bytes] = mapped_column(LargeBinary)
    created_at: Mapped[datetime] = mapped_column(default=utc_now)

    @property
    def created_at_utc(self) -> datetime:
        return with_utc_timezone(self.created_at)


class Clip(EncryptedClip):
    """Um clip de texto."""

    __tablename__ = "clips"


class CodeClip(EncryptedClip):
    """Um bloco de código guardado na sala."""

    __tablename__ = "code_clips"
