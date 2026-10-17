import pytest
from pydantic import ValidationError

from app.config import Settings


def test_health_returns_ok(client):
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_index_page_shows_default_ttl(client):
    response = client.get("/")

    assert response.status_code == 200
    assert "12h (padrão)" in response.text


def test_static_css_is_served(client):
    response = client.get("/static/css/style.css")

    assert response.status_code == 200


def test_storage_dir_is_created_on_startup(client, tmp_path):
    assert (tmp_path / "storage").is_dir()


def test_ttl_options_are_read_from_env(monkeypatch):
    monkeypatch.setenv("ALLOWED_TTL_HOURS", "1,6,12")
    monkeypatch.setenv("DEFAULT_TTL_HOURS", "6")

    settings = Settings(_env_file=None)

    assert settings.ttl_options == [1, 6, 12]


def test_default_ttl_must_be_one_of_the_options(monkeypatch):
    monkeypatch.setenv("DEFAULT_TTL_HOURS", "5")

    with pytest.raises(ValidationError):
        Settings(_env_file=None)
