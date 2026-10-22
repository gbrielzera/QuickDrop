"""Testes das proteções acrescentadas depois da revisão de segurança."""

import sqlite3

import pytest
from starlette.websockets import WebSocketDisconnect

from app import file_service
from app.config import get_settings
from app.security import hash_auth_key, verify_auth_key
from app.session import create_session_token, session_cookie_name
from tests.conftest import start_test_client
from tests.test_files import ONE_MEGABYTE, encrypted_bytes, storage_files, upload
from tests.test_rooms import AUTH_KEY, OTHER_AUTH_KEY, create_room, create_room_payload, new_device

# ---------- sala trancada ----------


def join(device, room_code: str):
    return device.post(f"/api/rooms/{room_code}/join", json={"auth_key": AUTH_KEY})


def lock(device, room_code: str, locked: bool = True):
    return device.put(f"/api/rooms/{room_code}/lock", json={"locked": locked})


def test_a_locked_room_refuses_new_devices(client):
    room = create_room(client)

    assert lock(client, room["code"]).status_code == 200
    response = join(new_device(client), room["code"])

    assert response.status_code == 403
    assert response.json()["detail"] == "room_locked"


def test_a_locked_room_lets_devices_that_already_joined_come_back(client):
    room = create_room(client)
    guest = new_device(client)
    assert join(guest, room["code"]).status_code == 200

    lock(client, room["code"])

    assert join(guest, room["code"]).status_code == 200
    assert join(client, room["code"]).status_code == 200


def test_unlocking_the_room_lets_new_devices_in_again(client):
    room = create_room(client)
    lock(client, room["code"])

    lock(client, room["code"], locked=False)

    assert join(new_device(client), room["code"]).status_code == 200


def test_only_the_owner_can_lock_the_room(client):
    room = create_room(client)
    guest = new_device(client)
    join(guest, room["code"])

    response = lock(guest, room["code"])

    assert response.status_code == 403
    assert response.json()["detail"] == "not_owner"
    assert client.get(f"/api/rooms/{room['code']}").json()["is_locked"] is False


def test_the_room_data_tells_whether_it_is_locked(client):
    room = create_room(client)

    assert lock(client, room["code"]).json()["is_locked"] is True
    assert client.get(f"/api/rooms/{room['code']}").json()["is_locked"] is True


def test_a_database_from_before_the_lock_feature_is_upgraded(tmp_path, monkeypatch):
    old_database = sqlite3.connect(tmp_path / "test.db")
    old_database.execute(
        "CREATE TABLE rooms (id VARCHAR(36) PRIMARY KEY, code VARCHAR(6) UNIQUE, has_password BOOLEAN,"
        " kdf_salt BLOB, auth_hash VARCHAR, created_at DATETIME, expires_at DATETIME)"
    )
    old_database.commit()
    old_database.close()

    for client in start_test_client(tmp_path, monkeypatch, debug=False):
        room = create_room(client)

        assert client.get(f"/api/rooms/{room['code']}").json()["is_locked"] is False


# ---------- cookies ----------


def test_a_session_cookie_made_from_the_room_code_is_not_accepted(client):
    room = create_room(client)
    stranger = new_device(client)
    stranger.cookies.set(session_cookie_name(room["code"]), create_session_token(room["code"]))

    assert stranger.get(f"/api/rooms/{room['code']}").status_code == 401


# ---------- limites ----------


def test_concurrent_uploads_cannot_go_over_the_room_limit(small_limits_client, tmp_path, monkeypatch):
    room = create_room(small_limits_client)
    two_megabytes = encrypted_bytes(2 * ONE_MEGABYTE)
    assert upload(small_limits_client, room["code"], two_megabytes).status_code == 201

    # O envio concorrente passou na conferência do início porque ainda não via o primeiro arquivo.
    real_total = file_service.total_size_of_room
    calls = []

    async def blind_first_time(db, room_id):
        calls.append(1)
        return 0 if len(calls) == 1 else await real_total(db, room_id)

    monkeypatch.setattr("app.routers.files.file_service.total_size_of_room", blind_first_time)
    response = upload(small_limits_client, room["code"], two_megabytes)

    assert response.status_code == 413
    assert response.json()["detail"] == "room_full"
    assert len(storage_files(tmp_path)) == 1


@pytest.fixture
def two_devices_client(tmp_path, monkeypatch):
    yield from start_test_client(tmp_path, monkeypatch, debug=False, MAX_CONNECTIONS_PER_ROOM="2")


def test_a_room_accepts_only_the_maximum_number_of_connections(two_devices_client):
    client = two_devices_client
    room = create_room(client)
    path = f"/ws/rooms/{room['code']}"

    with client.websocket_connect(path), client.websocket_connect(path):
        with pytest.raises(WebSocketDisconnect), client.websocket_connect(path) as third:
            third.receive_json()


def test_the_auth_key_hash_is_not_the_auth_key_and_is_stable(client):
    auth_hash = hash_auth_key(AUTH_KEY)

    assert auth_hash != AUTH_KEY
    assert len(auth_hash) == 64
    assert hash_auth_key(AUTH_KEY) == auth_hash


def test_the_auth_key_check_accepts_only_the_right_key(client):
    auth_hash = hash_auth_key(AUTH_KEY)

    assert verify_auth_key(AUTH_KEY, auth_hash) is True
    assert verify_auth_key(OTHER_AUTH_KEY, auth_hash) is False
    assert verify_auth_key(AUTH_KEY, "isto-nao-e-um-hash") is False


def test_a_stolen_hash_is_useless_with_another_secret_key(client, monkeypatch):
    auth_hash = hash_auth_key(AUTH_KEY)

    monkeypatch.setattr(get_settings(), "secret_key", "outra-chave-secreta-do-servidor")

    assert verify_auth_key(AUTH_KEY, auth_hash) is False


# ---------- cabeçalhos e documentação ----------


def test_the_api_documentation_is_off_in_production(client):
    for path in ("/docs", "/redoc", "/openapi.json"):
        assert client.get(path).status_code == 404


def test_the_api_documentation_is_on_while_developing(debug_client):
    assert debug_client.get("/docs").status_code == 200


def test_the_policy_lets_the_page_open_websockets_only_to_its_own_site(client):
    policy = client.get("/sobre", headers={"host": "quickdrop.example"}).headers["content-security-policy"]

    assert "connect-src 'self' ws://quickdrop.example wss://quickdrop.example;" in policy
    assert "ws: " not in policy


def test_a_strange_host_header_never_reaches_the_policy(client):
    policy = client.get("/sobre", headers={"host": "a.com; script-src *"}).headers["content-security-policy"]

    assert "script-src *" not in policy
    assert "connect-src 'self';" in policy


def test_room_creation_still_works_with_the_default_limits(client):
    assert client.post("/api/rooms", json=create_room_payload()).status_code == 201


# ---------- velocidade de carregamento ----------


def test_the_room_page_preloads_every_module_it_needs(client):
    page = client.get("/r/ABCDEF").text

    for module in ("room.js", "crypto.js", "vendor/libsodium-sumo.mjs", "upload-panel.js", "zip.js"):
        assert f'rel="modulepreload" href="http://testserver/static/js/{module}"' in page


def test_the_home_page_preloads_the_modules_it_needs(client):
    page = client.get("/").text

    assert 'rel="modulepreload" href="http://testserver/static/js/home.js"' in page
    assert 'rel="modulepreload" href="http://testserver/static/js/vendor/libsodium-sumo.mjs"' in page
    assert "upload-panel.js" not in page


def test_libraries_fonts_and_icons_are_cached_for_a_day(client):
    for path in (
        "/static/js/vendor/libsodium-sumo.mjs",
        "/static/fonts/inter-latin-500-normal.woff2",
        "/static/icons/favicon-32.png",
    ):
        assert client.get(path).headers["cache-control"] == "public, max-age=86400"


def test_the_apps_own_scripts_are_always_revalidated(client):
    assert client.get("/static/js/room.js").headers["cache-control"] == "no-cache"
