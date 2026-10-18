import os

# O app exige SECRET_KEY ao ser importado; nos testes usamos uma chave fixa.
os.environ.setdefault("SECRET_KEY", "chave-secreta-somente-para-testes")

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.config import get_settings  # noqa: E402
from app.main import create_app  # noqa: E402


def start_test_client(tmp_path, monkeypatch, debug: bool, **extra_settings: str):
    """Cria um cliente de teste com banco e pasta de arquivos temporários.

    `extra_settings` troca configurações do app, ex.: MAX_FILE_SIZE_MB="1".
    """
    monkeypatch.setenv("SECRET_KEY", "chave-secreta-somente-para-testes")
    monkeypatch.setenv("STORAGE_DIR", str(tmp_path / "storage"))
    monkeypatch.setenv("DATABASE_URL", f"sqlite+aiosqlite:///{tmp_path / 'test.db'}")
    monkeypatch.setenv("DEBUG", "true" if debug else "false")
    for name, value in extra_settings.items():
        monkeypatch.setenv(name, value)
    get_settings.cache_clear()

    with TestClient(create_app()) as test_client:
        yield test_client

    get_settings.cache_clear()


@pytest.fixture
def client(tmp_path, monkeypatch):
    """Cliente de teste com DEBUG desligado (como em produção)."""
    yield from start_test_client(tmp_path, monkeypatch, debug=False)


@pytest.fixture
def debug_client(tmp_path, monkeypatch):
    """Cliente de teste com DEBUG ligado (páginas de desenvolvimento disponíveis)."""
    yield from start_test_client(tmp_path, monkeypatch, debug=True)


@pytest.fixture
def small_limits_client(tmp_path, monkeypatch):
    """Cliente de teste com limites pequenos: 2 MB por arquivo e 3 MB por sala."""
    yield from start_test_client(
        tmp_path, monkeypatch, debug=False, MAX_FILE_SIZE_MB="2", MAX_ROOM_SIZE_MB="3"
    )


@pytest.fixture
def few_clips_client(tmp_path, monkeypatch):
    """Cliente de teste em que cada sala comporta só 2 clips."""
    yield from start_test_client(tmp_path, monkeypatch, debug=False, MAX_CLIPS_PER_ROOM="2")
