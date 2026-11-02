"""Testes das correções de segurança (limites de corpo, IPv6, cabeçalhos, WebSocket, sessões)."""

from starlette.websockets import WebSocketDisconnect

from app.rate_limit import normalize_address
from app.routers.ws import MAX_MESSAGES_PER_MINUTE
from app.schemas import MAX_CIPHERTEXT_CHARS
from tests.test_realtime import room_socket_url
from tests.test_rooms import create_room
from tests.test_text import encrypted_text, save_text


def test_addresses_of_the_same_ipv6_prefix_share_one_limit_key():
    assert normalize_address("2001:db8:1:2::1") == normalize_address("2001:db8:1:2:ffff::9")
    assert normalize_address("2001:db8:1:2::1") != normalize_address("2001:db8:1:3::1")


def test_ipv4_and_unknown_addresses_are_kept_as_they_are():
    assert normalize_address("203.0.113.7") == "203.0.113.7"
    assert normalize_address("testclient") == "testclient"


def test_a_huge_version_number_is_refused_instead_of_crashing(client):
    room = create_room(client)

    response = save_text(client, room["code"], encrypted_text(), base_version=2**70)

    assert response.status_code == 422


def test_a_ciphertext_over_the_hard_cap_is_refused_before_decoding(client):
    room = create_room(client)

    response = save_text(client, room["code"], "A" * (MAX_CIPHERTEXT_CHARS + 1), base_version=0)

    assert response.status_code == 422


def test_room_pages_are_never_cached(client):
    room = create_room(client)

    assert client.get(f"/r/{room['code']}").headers["cache-control"] == "no-store"


def test_pages_isolate_themselves_from_other_origins(client):
    headers = client.get("/").headers

    assert headers["cross-origin-opener-policy"] == "same-origin"
    assert headers["cross-origin-resource-policy"] == "same-origin"
    assert headers["cross-origin-embedder-policy"] == "require-corp"


def test_a_device_flooding_the_socket_is_disconnected(client):
    room = create_room(client)

    with client.websocket_connect(room_socket_url(room["code"])) as websocket:
        websocket.receive_json()  # presença inicial
        for _ in range(MAX_MESSAGES_PER_MINUTE + 1):
            websocket.send_json({"type": "ping"})
        try:
            while True:
                websocket.receive_json()
        except WebSocketDisconnect as disconnect:
            assert disconnect.code == 1008


def test_a_device_with_all_its_upload_slots_busy_cannot_start_another(client):
    from app.rate_limit import ConcurrentLimiter
    from tests.test_files import upload

    room = create_room(client)
    limiter = client.app.state.rate_limits.concurrent_uploads
    assert isinstance(limiter, ConcurrentLimiter)
    while limiter.try_acquire("testclient"):
        pass

    assert upload(client, room["code"]).status_code == 429

    limiter.release("testclient")
    assert upload(client, room["code"]).status_code == 201


def test_the_upload_slot_is_returned_even_when_the_upload_is_refused(client):
    from tests.test_files import upload

    room = create_room(client)
    limiter = client.app.state.rate_limits.concurrent_uploads

    for _ in range(10):
        upload(client, room["code"], content=b"")  # recusado: arquivo vazio

    assert limiter.try_acquire("testclient")


def test_the_concurrent_limiter_counts_per_key():
    from app.rate_limit import ConcurrentLimiter

    limiter = ConcurrentLimiter(max_active=1)

    assert limiter.try_acquire("a")
    assert not limiter.try_acquire("a")
    assert limiter.try_acquire("b")
    limiter.release("a")
    assert limiter.try_acquire("a")


def test_on_https_the_cookies_use_the_host_prefix(https_client):
    https_client.post(
        "/api/rooms",
        json={"ttl_hours": 12, "has_password": False, "kdf_salt": "c" * 22, "auth_key": "d" * 43},
    )
    names = set(https_client.cookies.keys())

    assert any(name.startswith("__Host-room_") for name in names)
    assert any(name.startswith("__Host-owner_") for name in names)


# ---------- remover os outros aparelhos ----------


def test_the_owner_removes_other_devices_and_locks_the_room(client):
    from tests.test_rooms import AUTH_KEY, new_device

    room = create_room(client)
    guest = new_device(client)
    assert guest.post(f"/api/rooms/{room['code']}/join", json={"auth_key": AUTH_KEY}).status_code == 200
    assert guest.get(f"/api/rooms/{room['code']}").status_code == 200

    response = client.post(f"/api/rooms/{room['code']}/kick-others")

    assert response.status_code == 200
    assert response.json()["is_locked"] is True
    assert guest.get(f"/api/rooms/{room['code']}").status_code == 401  # o cookie antigo morreu
    assert guest.post(f"/api/rooms/{room['code']}/join", json={"auth_key": AUTH_KEY}).status_code == 403
    assert client.get(f"/api/rooms/{room['code']}").status_code == 200  # o dono continua dentro


def test_a_guest_cannot_remove_other_devices(client):
    from tests.test_rooms import AUTH_KEY, new_device

    room = create_room(client)
    guest = new_device(client)
    guest.post(f"/api/rooms/{room['code']}/join", json={"auth_key": AUTH_KEY})

    assert guest.post(f"/api/rooms/{room['code']}/kick-others").status_code == 403
    assert guest.get(f"/api/rooms/{room['code']}").status_code == 200


def test_removing_other_devices_closes_their_sockets(client):
    from tests.test_rooms import AUTH_KEY, new_device

    room = create_room(client)
    guest = new_device(client)
    guest.post(f"/api/rooms/{room['code']}/join", json={"auth_key": AUTH_KEY})

    with guest.websocket_connect(room_socket_url(room["code"])) as socket:
        socket.receive_json()  # presença
        client.post(f"/api/rooms/{room['code']}/kick-others")
        try:
            while True:
                socket.receive_json()
        except WebSocketDisconnect as disconnect:
            assert disconnect.code == 1008


def test_old_style_session_tokens_are_refused():
    from app.session import create_session_token, read_session_token

    assert read_session_token(create_session_token("room-id", 3)) == ("room-id", 3)
    assert read_session_token("token-invalido") is None


# ---------- salas abertas por origem ----------


def test_one_address_cannot_hold_unlimited_open_rooms(tmp_path, monkeypatch):
    from tests.conftest import start_test_client
    from tests.test_rooms import create_room_payload

    for client in start_test_client(tmp_path, monkeypatch, debug=False, MAX_ACTIVE_ROOMS_PER_ADDRESS="2"):
        assert client.post("/api/rooms", json=create_room_payload()).status_code == 201
        assert client.post("/api/rooms", json=create_room_payload()).status_code == 201

        response = client.post("/api/rooms", json=create_room_payload())

        assert response.status_code == 429
        assert response.json()["detail"] == "too_many_rooms"


def test_the_room_quota_frees_up_when_the_rooms_expire():
    from app.rate_limit import ActiveRoomsQuota

    quota = ActiveRoomsQuota(max_rooms=1)
    quota.record("a", seconds_until_expiry=0)
    assert not quota.is_full("a")

    quota.record("a", seconds_until_expiry=3600)
    assert quota.is_full("a")
    assert not quota.is_full("b")
