"""Tabelas do banco de dados."""

from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import LargeBinary, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


def utc_now() -> datetime:
    """Hora atual em UTC. O banco guarda horários em UTC, sem informação de fuso."""
    return datetime.now(UTC).replace(tzinfo=None)


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
        """Horário de expiração com fuso UTC, para a API enviar em formato que o JavaScript entende."""
        return self.expires_at.replace(tzinfo=UTC)
