from datetime import timedelta

import pytest
from sqlalchemy import func, select
from starlette.websockets import WebSocketDisconnect

from app.cleanup import delete_expired_rooms
from app.models import Clip, CodeClip, Room, RoomText, SourceCode, StoredFile, utc_now
from tests.test_clips import create_clip
from tests.test_files import storage_files, upload
from tests.test_rooms import create_room, new_device
from tests.test_text import encrypted_text, save_text


def count_rows(client, model) -> int:
    """Quantas linhas a tabela tem agora (consulta direta ao banco)."""

    async def count() -> int:
        async with client.app.state.session_maker() as db:
            return (await db.execute(select(func.count()).select_from(model))).scalar_one()

    return client.portal.call(count)


def fill_room(client, room_code: str) -> None:
    """Coloca um arquivo, um texto, um clip, um código e um bloco de código na sala."""
    upload(client, room_code)
    save_text(client, room_code, encrypted_text(), base_version=0)
    create_clip(client, room_code)
    client.put(f"/api/rooms/{room_code}/source", json={"ciphertext": encrypted_text(), "base_version": 0})
    client.post(f"/api/rooms/{room_code}/code-clips", json={"ciphertext": encrypted_text(b"x" * 60)})


def expire_all_rooms(monkeypatch) -> None:
    """Faz de conta que já se passaram duas horas."""
    in_two_hours = utc_now() + timedelta(hours=2)
    monkeypatch.setattr("app.room_service.utc_now", lambda: in_two_hours)


# ---------- encerrar a sala ----------


def test_closing_a_room_deletes_everything_in_it(client, tmp_path):
    room = create_room(client)
    fill_room(client, room["code"])

    response = client.delete(f"/api/rooms/{room['code']}")

    assert response.status_code == 204
    assert storage_files(tmp_path) == []
    for model in (Room, StoredFile, RoomText, Clip, SourceCode, CodeClip):
        assert count_rows(client, model) == 0


def test_a_closed_room_no_longer_exists(client):
    room = create_room(client)

    client.delete(f"/api/rooms/{room['code']}")

    assert client.get(f"/api/rooms/{room['code']}/params").status_code == 404
    assert client.get(f"/api/rooms/{room['code']}").status_code == 404


def test_only_who_joined_can_close_the_room(client):
    room = create_room(client)
    stranger = new_device(client)

    assert stranger.delete(f"/api/rooms/{room['code']}").status_code == 401
    assert client.get(f"/api/rooms/{room['code']}").status_code == 200


def test_closing_a_room_does_not_touch_other_rooms(client, tmp_path):
    first_room = create_room(client)
    second_room = create_room(client)
    fill_room(client, first_room["code"])
    fill_room(client, second_room["code"])

    client.delete(f"/api/rooms/{first_room['code']}")

    assert len(storage_files(tmp_path)) == 1
    assert client.get(f"/api/rooms/{second_room['code']}/files").status_code == 200
    assert count_rows(client, Room) == 1


def test_closing_a_room_tells_the_connected_devices(client):
    room = create_room(client)

    with client.websocket_connect(f"/ws/rooms/{room['code']}") as websocket:
        websocket.receive_json()  # presença
        client.delete(f"/api/rooms/{room['code']}")

        assert websocket.receive_json() == {"type": "room_closed", "reason": "closed"}
        with pytest.raises(WebSocketDisconnect):
            websocket.receive_json()  # o servidor fechou a conexão


# ---------- expiração automática ----------


def test_cleanup_deletes_the_expired_rooms_with_everything_in_them(client, tmp_path, monkeypatch):
    room = create_room(client, ttl_hours=1)
    fill_room(client, room["code"])
    expire_all_rooms(monkeypatch)

    deleted = client.portal.call(delete_expired_rooms, client.app)

    assert deleted == 1
    assert storage_files(tmp_path) == []
    for model in (Room, StoredFile, RoomText, Clip, SourceCode, CodeClip):
        assert count_rows(client, model) == 0


def test_cleanup_keeps_the_rooms_that_have_not_expired(client, tmp_path):
    room = create_room(client, ttl_hours=12)
    fill_room(client, room["code"])

    deleted = client.portal.call(delete_expired_rooms, client.app)

    assert deleted == 0
    assert len(storage_files(tmp_path)) == 1
    assert count_rows(client, Room) == 1


def test_cleanup_only_deletes_the_rooms_that_expired(client, monkeypatch):
    short_room = create_room(client, ttl_hours=1)
    long_room = create_room(client, ttl_hours=48)
    in_two_hours = utc_now() + timedelta(hours=2)
    monkeypatch.setattr("app.room_service.utc_now", lambda: in_two_hours)

    client.portal.call(delete_expired_rooms, client.app)

    remaining_codes = client.portal.call(_room_codes, client.app)
    assert remaining_codes == [long_room["code"]]
    assert short_room["code"] not in remaining_codes


def test_cleanup_tells_the_connected_devices_the_room_expired(client, monkeypatch):
    room = create_room(client, ttl_hours=1)

    with client.websocket_connect(f"/ws/rooms/{room['code']}") as websocket:
        websocket.receive_json()  # presença
        expire_all_rooms(monkeypatch)
        client.portal.call(delete_expired_rooms, client.app)

        assert websocket.receive_json() == {"type": "room_closed", "reason": "expired"}


async def _room_codes(app) -> list[str]:
    async with app.state.session_maker() as db:
        return list((await db.execute(select(Room.code))).scalars())
