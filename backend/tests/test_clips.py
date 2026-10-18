from app.encoding import to_base64url
from tests.test_rooms import create_room, new_device

ONE_KILOBYTE = 1024
ENCRYPTED_OVERHEAD_BYTES = 40  # número usado uma vez (24) + etiqueta de verificação (16)


def encrypted_clip(size: int = 100) -> str:
    """Bytes quaisquer em base64url: o servidor trata o clip como conteúdo opaco."""
    return to_base64url(bytes(index % 251 for index in range(size)))


def create_clip(client, room_code: str, ciphertext: str | None = None):
    ciphertext = encrypted_clip() if ciphertext is None else ciphertext
    return client.post(f"/api/rooms/{room_code}/clips", json={"ciphertext": ciphertext})


def test_create_returns_the_clip(client):
    room = create_room(client)
    ciphertext = encrypted_clip(120)

    response = create_clip(client, room["code"], ciphertext)

    assert response.status_code == 201
    clip = response.json()
    assert clip["ciphertext"] == ciphertext
    assert clip["created_at"].endswith("Z")
    assert len(clip["id"]) == 36


def test_list_shows_the_clips_in_order(client):
    room = create_room(client)
    first = create_clip(client, room["code"], encrypted_clip(100)).json()
    second = create_clip(client, room["code"], encrypted_clip(200)).json()

    response = client.get(f"/api/rooms/{room['code']}/clips")

    assert [clip["id"] for clip in response.json()] == [first["id"], second["id"]]


def test_delete_removes_the_clip(client):
    room = create_room(client)
    clip = create_clip(client, room["code"]).json()

    response = client.delete(f"/api/rooms/{room['code']}/clips/{clip['id']}")

    assert response.status_code == 204
    assert client.get(f"/api/rooms/{room['code']}/clips").json() == []


def test_delete_of_an_unknown_clip_is_404(client):
    room = create_room(client)

    response = client.delete(f"/api/rooms/{room['code']}/clips/00000000-0000-4000-8000-000000000000")

    assert response.status_code == 404


def test_a_clip_cannot_be_reached_through_another_room(client):
    first_room = create_room(client)
    second_room = create_room(client)
    clip = create_clip(client, first_room["code"]).json()

    assert client.delete(f"/api/rooms/{second_room['code']}/clips/{clip['id']}").status_code == 404
    assert client.get(f"/api/rooms/{second_room['code']}/clips").json() == []


def test_a_clip_too_small_to_be_encrypted_is_refused(client):
    room = create_room(client)

    assert create_clip(client, room["code"], to_base64url(b"curto")).status_code == 422
    assert create_clip(client, room["code"], "").status_code == 422


def test_a_clip_that_is_not_base64url_is_refused(client):
    room = create_room(client)

    assert create_clip(client, room["code"], "isto nao e base64 !!!").status_code == 422


def test_a_clip_over_the_size_limit_is_refused(client):
    room = create_room(client)
    too_big = encrypted_clip(64 * ONE_KILOBYTE + ENCRYPTED_OVERHEAD_BYTES + 100)

    response = create_clip(client, room["code"], too_big)

    assert response.status_code == 413
    assert response.json()["detail"] == "clip_too_large"


def test_a_clip_of_exactly_the_limit_is_accepted(client):
    room = create_room(client)

    response = create_clip(client, room["code"], encrypted_clip(64 * ONE_KILOBYTE))

    assert response.status_code == 201


def test_a_room_only_holds_a_limited_number_of_clips(few_clips_client):
    room = create_room(few_clips_client)
    assert create_clip(few_clips_client, room["code"]).status_code == 201
    assert create_clip(few_clips_client, room["code"]).status_code == 201

    response = create_clip(few_clips_client, room["code"])

    assert response.status_code == 413
    assert response.json()["detail"] == "clips_full"


def test_deleting_a_clip_makes_room_for_a_new_one(few_clips_client):
    room = create_room(few_clips_client)
    first = create_clip(few_clips_client, room["code"]).json()
    create_clip(few_clips_client, room["code"])
    few_clips_client.delete(f"/api/rooms/{room['code']}/clips/{first['id']}")

    assert create_clip(few_clips_client, room["code"]).status_code == 201


def test_only_who_joined_the_room_can_use_its_clips(client):
    room = create_room(client)
    clip = create_clip(client, room["code"]).json()
    stranger = new_device(client)
    base_url = f"/api/rooms/{room['code']}/clips"

    assert stranger.get(base_url).status_code == 401
    assert stranger.post(base_url, json={"ciphertext": encrypted_clip()}).status_code == 401
    assert stranger.delete(f"{base_url}/{clip['id']}").status_code == 401


def test_new_and_deleted_clips_are_announced_to_the_connected_devices(client):
    room = create_room(client)

    with client.websocket_connect(f"/ws/rooms/{room['code']}") as websocket:
        websocket.receive_json()  # presença
        clip = create_clip(client, room["code"]).json()
        added = websocket.receive_json()
        client.delete(f"/api/rooms/{room['code']}/clips/{clip['id']}")
        deleted = websocket.receive_json()

    assert added == {"type": "clip_added", "clip": clip}
    assert deleted == {"type": "clip_deleted", "clip_id": clip["id"]}
