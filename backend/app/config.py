"""Configurações da aplicação, lidas do arquivo backend/.env ou de variáveis de ambiente."""

from functools import lru_cache
from pathlib import Path

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BACKEND_DIR.parent / "frontend"
BYTES_PER_KILOBYTE = 1024
BYTES_PER_MEGABYTE = 1024 * 1024


class Settings(BaseSettings):
    """Todas as configurações do app. Cada campo pode ser sobrescrito no .env (ex.: DEBUG=true)."""

    model_config = SettingsConfigDict(env_file=BACKEND_DIR / ".env", extra="ignore")

    app_name: str = "QuickDrop"
    debug: bool = False

    # Assina o cookie de sessão das salas. Obrigatória: sem ela, qualquer um poderia forjar cookies.
    secret_key: str = Field(min_length=16)

    database_url: str = f"sqlite+aiosqlite:///{BACKEND_DIR / 'quickdrop.db'}"
    storage_dir: Path = BACKEND_DIR / "storage"

    # Limites de tamanho dos arquivos enviados (não há limite de tipo: todo tipo de arquivo é aceito).
    max_file_size_mb: int = 100
    max_room_size_mb: int = 500

    # Limites do texto compartilhado e dos clips (textos colados), em KB, antes de criptografar.
    max_text_size_kb: int = 1024
    max_clip_size_kb: int = 64
    max_code_clip_size_kb: int = 256  # blocos de código costumam ser maiores que textos
    max_clips_per_room: int = 200

    # Contato para denúncias de abuso, mostrado na página /sobre (vazio: a página só orienta).
    contact_email: str = ""

    # Limites do servidor inteiro. Sem eles, poucas pessoas encheriam o disco de uma hospedagem grátis.
    max_total_storage_mb: int = 30 * 1024  # soma dos arquivos de todas as salas
    max_active_rooms: int = 500

    # De quanto em quanto tempo o servidor apaga as salas que expiraram.
    cleanup_interval_minutes: int = 5

    # Limites de tentativas, para ninguém ficar adivinhando códigos e senhas nem criando salas sem parar.
    rate_limit_lookups_per_minute: int = 30  # consultas e entradas por endereço IP
    rate_limit_failed_joins_per_minute: int = 5  # senhas erradas por IP e sala
    rate_limit_room_creations_per_hour: int = 20  # salas criadas por IP

    # Texto separado por vírgulas para ficar fácil de escrever no .env
    allowed_ttl_hours: str = "1,12,24,48"
    default_ttl_hours: int = 12

    # Ligue (COOKIE_SECURE=true) quando o site estiver em HTTPS, para o cookie nunca trafegar em HTTP.
    cookie_secure: bool = False

    @property
    def ttl_options(self) -> list[int]:
        """Opções de expiração da sala em horas. Ex.: "1,12,24,48" vira [1, 12, 24, 48]."""
        return [int(hours) for hours in self.allowed_ttl_hours.split(",")]

    @property
    def max_file_size_bytes(self) -> int:
        return self.max_file_size_mb * BYTES_PER_MEGABYTE

    @property
    def max_room_size_bytes(self) -> int:
        return self.max_room_size_mb * BYTES_PER_MEGABYTE

    @property
    def max_total_storage_bytes(self) -> int:
        return self.max_total_storage_mb * BYTES_PER_MEGABYTE

    @property
    def max_text_size_bytes(self) -> int:
        return self.max_text_size_kb * BYTES_PER_KILOBYTE

    @property
    def max_clip_size_bytes(self) -> int:
        return self.max_clip_size_kb * BYTES_PER_KILOBYTE

    @property
    def max_code_clip_size_bytes(self) -> int:
        return self.max_code_clip_size_kb * BYTES_PER_KILOBYTE

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
