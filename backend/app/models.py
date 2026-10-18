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


class RoomText(Base):
    """O texto compartilhado da sala (um por sala), guardado criptografado."""

    __tablename__ = "room_texts"

    room_id: Mapped[str] = mapped_column(ForeignKey("rooms.id", ondelete="CASCADE"), primary_key=True)
    # Vazio enquanto ninguém escreveu nada. O servidor não consegue ler o texto.
    ciphertext: Mapped[bytes] = mapped_column(LargeBinary, default=b"")
    # Sobe 1 a cada alteração. Serve para perceber que outro aparelho mudou o texto antes de nós.
    version: Mapped[int] = mapped_column(default=0)
    updated_at: Mapped[datetime] = mapped_column(default=utc_now)


class Clip(Base):
    """Um clip: um texto colado na sala, guardado criptografado."""

    __tablename__ = "clips"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    room_id: Mapped[str] = mapped_column(ForeignKey("rooms.id", ondelete="CASCADE"), index=True)
    ciphertext: Mapped[bytes] = mapped_column(LargeBinary)
    created_at: Mapped[datetime] = mapped_column(default=utc_now)

    @property
    def created_at_utc(self) -> datetime:
        return with_utc_timezone(self.created_at)
