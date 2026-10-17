from datetime import timedelta

from fastapi.testclient import TestClient

from app.encoding import to_base64url
from app.models import utc_now

AUTH_KEY = to_base64url(bytes(range(32)))
OTHER_AUTH_KEY = to_base64url(bytes(range(1, 33)))
KDF_SALT = to_base64url(bytes(range(16)))


def create_room_payload(ttl_hours: int = 12, has_password: bool = False) -> dict:
    return {"ttl_hours": ttl_hours, "has_password": has_password, "kdf_salt": KDF_SALT, "auth_key": AUTH_KEY}


def new_device(client) -> TestClient:
    """Outro dispositivo falando com o mesmo servidor: não tem os cookies do primeiro."""
    return TestClient(client.app)


def create_room(client, **payload_changes) -> dict:
    response = client.post("/api/rooms", json=create_room_payload(**payload_changes))
    assert response.status_code == 201
    return response.json()


# ---------- criar sala ----------


def test_create_room_returns_a_code_and_the_expiration(client):
    room = create_room(client, ttl_hours=12)

    assert len(room["code"]) == 6
    assert room["expires_at"].endswith("Z")  # o JavaScript precisa saber que é UTC
    assert "room_" + room["code"] in client.cookies


def test_create_room_expires_after_the_chosen_time(client):
    room = create_room(client, ttl_hours=24)

    response = client.get(f"/api/rooms/{room['code']}")

    expires_at = utc_now() + timedelta(hours=24)
    assert response.json()["expires_at"][:13] == expires_at.isoformat()[:13]


def test_create_room_rejects_a_ttl_that_is_not_an_option(client):
    response = client.post("/api/rooms", json=create_room_payload(ttl_hours=5))

    assert response.status_code == 422


def test_create_room_rejects_a_salt_with_the_wrong_size(client):
    payload = create_room_payload() | {"kdf_salt": to_base64url(b"curto")}

    assert client.post("/api/rooms", json=payload).status_code == 422


def test_create_room_rejects_an_auth_key_with_the_wrong_size(client):
    payload = create_room_payload() | {"auth_key": to_base64url(b"curta")}

    assert client.post("/api/rooms", json=payload).status_code == 422


def test_create_room_rejects_text_that_is_not_base64url(client):
    payload = create_room_payload() | {"auth_key": "isto não é base64 !!!"}

    assert client.post("/api/rooms", json=payload).status_code == 422


def test_each_room_gets_a_different_code(client):
    codes = {create_room(client)["code"] for _ in range(5)}

    assert len(codes) == 5


def test_create_room_tries_again_when_the_code_is_already_taken(client, monkeypatch):
    codes = iter(["AAAAAA", "AAAAAA", "BBBBBB"])
    monkeypatch.setattr("app.room_service.generate_room_code", lambda: next(codes))

    first_room = create_room(client)
    second_room = create_room(client)

    assert first_room["code"] == "AAAAAA"
    assert second_room["code"] == "BBBBBB"


def test_the_database_never_stores_the_auth_key_in_plain_text(client, tmp_path):
    create_room(client)

    database_bytes = (tmp_path / "test.db").read_bytes()
    assert AUTH_KEY.encode() not in database_bytes


# ---------- parâmetros para derivar as chaves ----------


def test_params_returns_the_salt_and_if_the_room_has_a_password(client):
    room = create_room(client, has_password=True)

    response = client.get(f"/api/rooms/{room['code']}/params")

    assert response.status_code == 200
    assert response.json() == {"has_password": True, "kdf_salt": KDF_SALT}


def test_params_of_an_unknown_room_is_404(client):
    assert client.get("/api/rooms/ZZZZZZ/params").status_code == 404


def test_a_code_with_forbidden_characters_is_rejected(client):
    # "O", "0", "I", "1" e "L" não existem no alfabeto dos códigos.
    assert client.get("/api/rooms/OOOOOO/params").status_code == 422
    assert client.get("/api/rooms/ABC/params").status_code == 422


# ---------- entrar na sala ----------


def test_join_with_the_right_auth_key_gives_a_session_cookie(client):
    room = create_room(client)
    other_device = new_device(client)

    response = other_device.post(f"/api/rooms/{room['code']}/join", json={"auth_key": AUTH_KEY})

    assert response.status_code == 200
    assert response.json()["code"] == room["code"]
    assert "room_" + room["code"] in other_device.cookies


def test_join_with_the_wrong_auth_key_is_refused(client):
    room = create_room(client)
    other_device = new_device(client)

    response = other_device.post(f"/api/rooms/{room['code']}/join", json={"auth_key": OTHER_AUTH_KEY})

    assert response.status_code == 401
    assert "room_" + room["code"] not in other_device.cookies


def test_join_an_unknown_room_is_404(client):
    response = client.post("/api/rooms/ZZZZZZ/join", json={"auth_key": AUTH_KEY})

    assert response.status_code == 404


# ---------- sessão ----------


def test_room_data_requires_having_joined(client):
    room = create_room(client)
    stranger = new_device(client)

    response = stranger.get(f"/api/rooms/{room['code']}")

    assert response.status_code == 401


def test_a_cookie_from_another_room_does_not_open_this_room(client):
    first_room = create_room(client)
    second_room = create_room(client)
    stranger = new_device(client)
    stranger.cookies.set(f"room_{second_room['code']}", client.cookies[f"room_{first_room['code']}"])

    response = stranger.get(f"/api/rooms/{second_room['code']}")

    assert response.status_code == 401


def test_a_forged_cookie_is_refused(client):
    room = create_room(client)
    stranger = new_device(client)
    stranger.cookies.set(f"room_{room['code']}", "cookie-falsificado")

    response = stranger.get(f"/api/rooms/{room['code']}")

    assert response.status_code == 401


def test_room_data_for_someone_who_joined(client):
    room = create_room(client, has_password=True)

    response = client.get(f"/api/rooms/{room['code']}")

    assert response.status_code == 200
    assert response.json()["code"] == room["code"]
    assert response.json()["has_password"] is True


# ---------- expiração ----------


def test_an_expired_room_no_longer_exists(client, monkeypatch):
    room = create_room(client, ttl_hours=1)
    in_two_hours = utc_now() + timedelta(hours=2)
    monkeypatch.setattr("app.room_service.utc_now", lambda: in_two_hours)

    assert client.get(f"/api/rooms/{room['code']}/params").status_code == 404
    assert client.post(f"/api/rooms/{room['code']}/join", json={"auth_key": AUTH_KEY}).status_code == 404
    assert client.get(f"/api/rooms/{room['code']}").status_code == 404
