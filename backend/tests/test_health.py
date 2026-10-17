import pytest
from pydantic import ValidationError

from app.config import Settings


def test_health_returns_ok(client):
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_index_page_offers_the_expiration_options_with_12h_selected(client):
    response = client.get("/")

    assert response.status_code == 200
    for hours in (1, 12, 24, 48):
        assert f'value="{hours}"' in response.text
    assert 'value="12" checked' in response.text


def test_room_page_knows_its_room_code(client):
    response = client.get("/r/K7P3XM")

    assert response.status_code == 200
    assert 'data-room-code="K7P3XM"' in response.text


def test_room_page_rejects_an_invalid_code(client):
    assert client.get("/r/ABC").status_code == 422


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
