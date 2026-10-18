"""Testes do código compartilhado (/source) e dos blocos de código (/code-clips).

Eles têm o mesmo funcionamento do texto e dos clips, então aqui testamos o que muda: as rotas, os avisos
em tempo real, que os dois conjuntos não se misturam e o limite maior dos blocos de código.
"""

from app.encoding import to_base64url
from tests.test_clips import create_clip, encrypted_clip
from tests.test_rooms import create_room, new_device
from tests.test_text import encrypted_text, save_text

ONE_KILOBYTE = 1024
ENCRYPTED_OVERHEAD_BYTES = 40


def save_source(client, room_code: str, ciphertext: str, base_version: int):
    return client.put(
        f"/api/rooms/{room_code}/source", json={"ciphertext": ciphertext, "base_version": base_version}
    )


def create_code_clip(client, room_code: str, ciphertext: str | None = None):
    ciphertext = encrypted_clip() if ciphertext is None else ciphertext
    return client.post(f"/api/rooms/{room_code}/code-clips", json={"ciphertext": ciphertext})


# ---------- código compartilhado ----------


def test_a_new_room_has_an_empty_source_at_version_zero(client):
    room = create_room(client)

    response = client.get(f"/api/rooms/{room['code']}/source")

    assert response.status_code == 200
    assert response.json() == {"ciphertext": "", "version": 0}


def test_saving_the_source_raises_its_version(client):
    room = create_room(client)
    ciphertext = encrypted_text(b"def ola():\n    return 1\n")

    response = save_source(client, room["code"], ciphertext, base_version=0)

    assert response.json() == {"ciphertext": ciphertext, "version": 1}
    assert client.get(f"/api/rooms/{room['code']}/source").json() == {"ciphertext": ciphertext, "version": 1}


def test_saving_the_source_over_an_outdated_version_is_a_conflict(client):
    room = create_room(client)
    save_source(client, room["code"], encrypted_text(b"A"), base_version=0)

    response = save_source(client, room["code"], encrypted_text(b"B"), base_version=0)

    assert response.status_code == 409
    assert response.json()["detail"]["current"] == {"ciphertext": encrypted_text(b"A"), "version": 1}


def test_the_text_and_the_source_are_independent(client):
    room = create_room(client)

    save_text(client, room["code"], encrypted_text(b"so texto"), base_version=0)
    save_source(client, room["code"], encrypted_text(b"so codigo"), base_version=0)

    assert client.get(f"/api/rooms/{room['code']}/text").json()["ciphertext"] == encrypted_text(b"so texto")
    assert client.get(f"/api/rooms/{room['code']}/source").json()["ciphertext"] == encrypted_text(
        b"so codigo"
    )


def test_a_source_over_the_size_limit_is_refused(client):
    room = create_room(client)
    too_big = encrypted_text(bytes(1024 * ONE_KILOBYTE + 200))

    response = save_source(client, room["code"], too_big, base_version=0)

    assert response.status_code == 413
    assert response.json()["detail"] == "text_too_large"


def test_only_who_joined_the_room_can_use_the_source(client):
    room = create_room(client)
    stranger = new_device(client)
    url = f"/api/rooms/{room['code']}/source"

    assert stranger.get(url).status_code == 401
    assert stranger.put(url, json={"ciphertext": encrypted_text(), "base_version": 0}).status_code == 401


def test_a_saved_source_is_announced_with_its_own_event(client):
    room = create_room(client)

    with client.websocket_connect(f"/ws/rooms/{room['code']}") as websocket:
        websocket.receive_json()  # presença
        save_source(client, room["code"], encrypted_text(), base_version=0)

        message = websocket.receive_json()

    assert message == {"type": "source_updated", "ciphertext": encrypted_text(), "version": 1}


# ---------- blocos de código ----------


def test_a_code_clip_is_created_listed_and_deleted(client):
    room = create_room(client)

    clip = create_code_clip(client, room["code"], encrypted_clip(150)).json()
    listed = client.get(f"/api/rooms/{room['code']}/code-clips").json()
    deleted = client.delete(f"/api/rooms/{room['code']}/code-clips/{clip['id']}")

    assert listed == [clip]
    assert deleted.status_code == 204
    assert client.get(f"/api/rooms/{room['code']}/code-clips").json() == []


def test_text_clips_and_code_clips_do_not_mix(client):
    room = create_room(client)
    text_clip = create_clip(client, room["code"]).json()
    code_clip = create_code_clip(client, room["code"]).json()

    assert [clip["id"] for clip in client.get(f"/api/rooms/{room['code']}/clips").json()] == [text_clip["id"]]
    assert [clip["id"] for clip in client.get(f"/api/rooms/{room['code']}/code-clips").json()] == [
        code_clip["id"]
    ]
    # Um clip de texto não pode ser apagado pela rota dos blocos de código, e vice-versa.
    assert client.delete(f"/api/rooms/{room['code']}/code-clips/{text_clip['id']}").status_code == 404
    assert client.delete(f"/api/rooms/{room['code']}/clips/{code_clip['id']}").status_code == 404


def test_a_code_clip_can_be_bigger_than_a_text_clip(client):
    room = create_room(client)
    bigger_than_a_text_clip = encrypted_clip(100 * ONE_KILOBYTE)

    assert create_clip(client, room["code"], bigger_than_a_text_clip).status_code == 413
    assert create_code_clip(client, room["code"], bigger_than_a_text_clip).status_code == 201


def test_a_code_clip_over_its_limit_is_refused(client):
    room = create_room(client)
    too_big = encrypted_clip(256 * ONE_KILOBYTE + ENCRYPTED_OVERHEAD_BYTES + 100)

    response = create_code_clip(client, room["code"], too_big)

    assert response.status_code == 413
    assert response.json()["detail"] == "clip_too_large"


def test_text_clips_and_code_clips_have_separate_counts(few_clips_client):
    room = create_room(few_clips_client)
    for _ in range(2):
        assert create_clip(few_clips_client, room["code"]).status_code == 201

    # Os clips de texto já chegaram ao limite de 2, mas os blocos de código têm a sua própria conta.
    assert create_clip(few_clips_client, room["code"]).status_code == 413
    assert create_code_clip(few_clips_client, room["code"]).status_code == 201


def test_a_code_clip_must_be_valid(client):
    room = create_room(client)

    assert create_code_clip(client, room["code"], to_base64url(b"curto")).status_code == 422
    assert create_code_clip(client, room["code"], "isto nao e base64 !!!").status_code == 422


def test_only_who_joined_the_room_can_use_the_code_clips(client):
    room = create_room(client)
    clip = create_code_clip(client, room["code"]).json()
    stranger = new_device(client)
    base_url = f"/api/rooms/{room['code']}/code-clips"

    assert stranger.get(base_url).status_code == 401
    assert stranger.post(base_url, json={"ciphertext": encrypted_clip()}).status_code == 401
    assert stranger.delete(f"{base_url}/{clip['id']}").status_code == 401


def test_new_and_deleted_code_clips_are_announced_with_their_own_events(client):
    room = create_room(client)

    with client.websocket_connect(f"/ws/rooms/{room['code']}") as websocket:
        websocket.receive_json()  # presença
        clip = create_code_clip(client, room["code"]).json()
        added = websocket.receive_json()
        client.delete(f"/api/rooms/{room['code']}/code-clips/{clip['id']}")
        deleted = websocket.receive_json()

    assert added == {"type": "code_clip_added", "clip": clip}
    assert deleted == {"type": "code_clip_deleted", "clip_id": clip["id"]}
