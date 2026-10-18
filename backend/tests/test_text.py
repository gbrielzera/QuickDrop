from app.encoding import to_base64url
from tests.test_rooms import create_room, new_device

ONE_KILOBYTE = 1024


def encrypted_text(content: bytes = b"texto-ja-criptografado") -> str:
    """Bytes quaisquer em base64url: o servidor trata o texto como conteúdo opaco."""
    return to_base64url(content)


def save_text(client, room_code: str, ciphertext: str, base_version: int):
    return client.put(
        f"/api/rooms/{room_code}/text", json={"ciphertext": ciphertext, "base_version": base_version}
    )


def test_a_new_room_has_an_empty_text_at_version_zero(client):
    room = create_room(client)

    response = client.get(f"/api/rooms/{room['code']}/text")

    assert response.status_code == 200
    assert response.json() == {"ciphertext": "", "version": 0}


def test_saving_the_text_raises_the_version(client):
    room = create_room(client)
    ciphertext = encrypted_text()

    response = save_text(client, room["code"], ciphertext, base_version=0)

    assert response.status_code == 200
    assert response.json() == {"ciphertext": ciphertext, "version": 1}
    assert client.get(f"/api/rooms/{room['code']}/text").json() == {"ciphertext": ciphertext, "version": 1}


def test_each_save_raises_the_version_by_one(client):
    room = create_room(client)

    first = save_text(client, room["code"], encrypted_text(b"um"), base_version=0).json()
    second = save_text(client, room["code"], encrypted_text(b"dois"), base_version=first["version"]).json()

    assert (first["version"], second["version"]) == (1, 2)


def test_saving_over_an_outdated_version_is_a_conflict_that_returns_the_current_text(client):
    room = create_room(client)
    save_text(client, room["code"], encrypted_text(b"do-aparelho-A"), base_version=0)

    # O aparelho B ainda achava que a versão era 0.
    response = save_text(client, room["code"], encrypted_text(b"do-aparelho-B"), base_version=0)

    assert response.status_code == 409
    detail = response.json()["detail"]
    assert detail["code"] == "text_conflict"
    assert detail["current"] == {"ciphertext": encrypted_text(b"do-aparelho-A"), "version": 1}
    # O texto do aparelho A continua intacto.
    assert client.get(f"/api/rooms/{room['code']}/text").json()["ciphertext"] == encrypted_text(
        b"do-aparelho-A"
    )


def test_a_text_over_the_size_limit_is_refused(client):
    room = create_room(client)
    too_big = encrypted_text(bytes(1024 * ONE_KILOBYTE + 200))

    response = save_text(client, room["code"], too_big, base_version=0)

    assert response.status_code == 413
    assert response.json()["detail"] == "text_too_large"


def test_a_text_of_exactly_the_limit_is_accepted(client):
    room = create_room(client)
    exactly_the_limit = encrypted_text(bytes(1024 * ONE_KILOBYTE))

    assert save_text(client, room["code"], exactly_the_limit, base_version=0).status_code == 200


def test_invalid_requests_are_refused(client):
    room = create_room(client)
    url = f"/api/rooms/{room['code']}/text"

    assert client.put(url, json={"ciphertext": "nao e base64 !!!", "base_version": 0}).status_code == 422
    assert client.put(url, json={"ciphertext": encrypted_text(), "base_version": -1}).status_code == 422
    assert client.put(url, json={"ciphertext": encrypted_text()}).status_code == 422


def test_only_who_joined_the_room_can_read_or_change_the_text(client):
    room = create_room(client)
    stranger = new_device(client)
    url = f"/api/rooms/{room['code']}/text"

    assert stranger.get(url).status_code == 401
    assert stranger.put(url, json={"ciphertext": encrypted_text(), "base_version": 0}).status_code == 401


def test_a_saved_text_is_announced_to_the_connected_devices(client):
    room = create_room(client)

    with client.websocket_connect(f"/ws/rooms/{room['code']}") as websocket:
        websocket.receive_json()  # presença
        save_text(client, room["code"], encrypted_text(), base_version=0)

        message = websocket.receive_json()

    assert message == {"type": "text_updated", "ciphertext": encrypted_text(), "version": 1}
