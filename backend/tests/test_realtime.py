import pytest
from starlette.websockets import WebSocketDisconnect

from app.realtime import ConnectionManager
from tests.test_files import ENCRYPTED_META, encrypted_bytes, upload
from tests.test_rooms import AUTH_KEY, create_room, new_device


def room_socket_url(room_code: str) -> str:
    return f"/ws/rooms/{room_code}"


def read_presence(websocket) -> int:
    message = websocket.receive_json()
    assert message["type"] == "presence"
    return message["online"]


class FakeWebSocket:
    """Um WebSocket de mentira que só guarda as mensagens recebidas."""

    def __init__(self, fails_on_send: bool = False):
        self.messages: list[dict] = []
        self.accepted = False
        self.fails_on_send = fails_on_send

    async def accept(self):
        self.accepted = True

    async def send_json(self, message: dict):
        if self.fails_on_send:
            raise RuntimeError("conexão caiu")
        self.messages.append(message)


# ---------- gerenciador de conexões (sem servidor) ----------


async def test_manager_counts_the_devices_of_each_room():
    manager = ConnectionManager()
    first, second, other_room = FakeWebSocket(), FakeWebSocket(), FakeWebSocket()

    await manager.connect("AAAAAA", first)
    await manager.connect("AAAAAA", second)
    await manager.connect("BBBBBB", other_room)

    assert manager.count("AAAAAA") == 2
    assert manager.count("BBBBBB") == 1
    assert manager.count("CCCCCC") == 0


async def test_manager_announces_presence_when_devices_come_and_go():
    manager = ConnectionManager()
    first, second = FakeWebSocket(), FakeWebSocket()

    await manager.connect("AAAAAA", first)
    await manager.connect("AAAAAA", second)
    await manager.disconnect("AAAAAA", second)

    assert first.messages == [
        {"type": "presence", "online": 1},
        {"type": "presence", "online": 2},
        {"type": "presence", "online": 1},
    ]
    assert second.messages == [{"type": "presence", "online": 2}]


async def test_broadcast_reaches_only_the_devices_of_that_room():
    manager = ConnectionManager()
    in_room, other_room = FakeWebSocket(), FakeWebSocket()
    await manager.connect("AAAAAA", in_room)
    await manager.connect("BBBBBB", other_room)

    await manager.broadcast("AAAAAA", {"type": "file_deleted", "file_id": "x"})

    assert {"type": "file_deleted", "file_id": "x"} in in_room.messages
    assert {"type": "file_deleted", "file_id": "x"} not in other_room.messages


async def test_a_connection_that_fails_is_dropped_without_stopping_the_others():
    manager = ConnectionManager()
    healthy, broken = FakeWebSocket(), FakeWebSocket()
    await manager.connect("AAAAAA", healthy)
    await manager.connect("AAAAAA", broken)
    broken.fails_on_send = True

    await manager.broadcast("AAAAAA", {"type": "file_deleted", "file_id": "x"})

    assert manager.count("AAAAAA") == 1
    assert {"type": "file_deleted", "file_id": "x"} in healthy.messages


# ---------- WebSocket da sala ----------


def test_a_device_in_the_room_connects_and_sees_itself_online(client):
    room = create_room(client)

    with client.websocket_connect(room_socket_url(room["code"])) as websocket:
        assert read_presence(websocket) == 1


def test_presence_follows_devices_joining_and_leaving(client):
    room = create_room(client)
    other_device = new_device(client)
    other_device.post(f"/api/rooms/{room['code']}/join", json={"auth_key": AUTH_KEY})

    with client.websocket_connect(room_socket_url(room["code"])) as first:
        assert read_presence(first) == 1
        with other_device.websocket_connect(room_socket_url(room["code"])) as second:
            assert read_presence(first) == 2
            assert read_presence(second) == 2
        assert read_presence(first) == 1


def test_ping_gets_a_pong(client):
    room = create_room(client)

    with client.websocket_connect(room_socket_url(room["code"])) as websocket:
        read_presence(websocket)
        websocket.send_json({"type": "ping"})

        assert websocket.receive_json() == {"type": "pong"}


def test_an_upload_is_announced_to_the_connected_devices(client):
    room = create_room(client)

    with client.websocket_connect(room_socket_url(room["code"])) as websocket:
        read_presence(websocket)
        file = upload(client, room["code"], encrypted_bytes(300)).json()

        message = websocket.receive_json()

    assert message["type"] == "file_added"
    assert message["file"] == file
    assert message["file"]["encrypted_meta"] == ENCRYPTED_META


def test_a_delete_is_announced_to_the_connected_devices(client):
    room = create_room(client)
    file = upload(client, room["code"]).json()

    with client.websocket_connect(room_socket_url(room["code"])) as websocket:
        read_presence(websocket)
        client.delete(f"/api/rooms/{room['code']}/files/{file['id']}")

        assert websocket.receive_json() == {"type": "file_deleted", "file_id": file["id"]}


# ---------- quem não pode entrar ----------


def test_someone_who_did_not_join_the_room_is_refused(client):
    room = create_room(client)
    stranger = new_device(client)

    with pytest.raises(WebSocketDisconnect) as error:
        with stranger.websocket_connect(room_socket_url(room["code"])):
            pass

    assert error.value.code == 1008


def test_the_cookie_of_another_room_is_refused(client):
    first_room = create_room(client)
    second_room = create_room(client)
    stranger = new_device(client)
    stranger.cookies.set(f"room_{second_room['code']}", client.cookies[f"room_{first_room['code']}"])

    with pytest.raises(WebSocketDisconnect):
        with stranger.websocket_connect(room_socket_url(second_room["code"])):
            pass


def test_a_page_from_another_site_is_refused_even_with_the_cookie(client):
    room = create_room(client)

    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect(
            room_socket_url(room["code"]), headers={"origin": "http://evil.example"}
        ):
            pass


def test_the_same_site_is_accepted(client):
    room = create_room(client)

    with client.websocket_connect(
        room_socket_url(room["code"]), headers={"origin": "http://testserver"}
    ) as socket:
        assert read_presence(socket) == 1


def test_a_room_that_does_not_exist_is_refused(client):
    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect(room_socket_url("ZZZZZZ")):
            pass


def test_a_message_that_is_not_json_closes_the_connection(client):
    room = create_room(client)

    with client.websocket_connect(room_socket_url(room["code"])) as websocket:
        read_presence(websocket)
        websocket.send_text("isto não é json")

        with pytest.raises(WebSocketDisconnect) as error:
            websocket.receive_json()

    assert error.value.code == 1003
