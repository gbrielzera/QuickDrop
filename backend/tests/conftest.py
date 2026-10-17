import pytest
from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import create_app


def start_test_client(tmp_path, monkeypatch, debug: bool):
    """Cria um cliente de teste usando uma pasta de armazenamento temporária."""
    monkeypatch.setenv("STORAGE_DIR", str(tmp_path / "storage"))
    monkeypatch.setenv("DEBUG", "true" if debug else "false")
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
