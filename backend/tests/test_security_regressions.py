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
