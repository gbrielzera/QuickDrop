"""Configurações da aplicação, lidas do arquivo backend/.env ou de variáveis de ambiente."""

from functools import lru_cache
from pathlib import Path

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BACKEND_DIR.parent / "frontend"


class Settings(BaseSettings):
    """Todas as configurações do app. Cada campo pode ser sobrescrito no .env (ex.: DEBUG=true)."""

    model_config = SettingsConfigDict(env_file=BACKEND_DIR / ".env", extra="ignore")

    app_name: str = "QuickDrop"
    debug: bool = False

    # Assina o cookie de sessão das salas. Obrigatória: sem ela, qualquer um poderia forjar cookies.
    secret_key: str = Field(min_length=16)

    database_url: str = f"sqlite+aiosqlite:///{BACKEND_DIR / 'quickdrop.db'}"
    storage_dir: Path = BACKEND_DIR / "storage"

    # Texto separado por vírgulas para ficar fácil de escrever no .env
    allowed_ttl_hours: str = "1,12,24,48"
    default_ttl_hours: int = 12

    # Ligue (COOKIE_SECURE=true) quando o site estiver em HTTPS, para o cookie nunca trafegar em HTTP.
    cookie_secure: bool = False

    @property
    def ttl_options(self) -> list[int]:
        """Opções de expiração da sala em horas. Ex.: "1,12,24,48" vira [1, 12, 24, 48]."""
        return [int(hours) for hours in self.allowed_ttl_hours.split(",")]

    @model_validator(mode="after")
    def check_default_ttl_is_an_option(self) -> "Settings":
        """Impede que o app inicie com uma expiração padrão que não está entre as opções."""
        if self.default_ttl_hours not in self.ttl_options:
            raise ValueError(
                f"DEFAULT_TTL_HOURS ({self.default_ttl_hours}) precisa estar em ALLOWED_TTL_HOURS "
                f"({self.allowed_ttl_hours})"
            )
        return self


@lru_cache
def get_settings() -> Settings:
    """Retorna as configurações, lendo o .env só uma vez."""
    return Settings()
