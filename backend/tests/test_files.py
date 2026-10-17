from datetime import timedelta

from fastapi.testclient import TestClient

from app.encoding import to_base64url
from app.models import utc_now
from tests.test_rooms import create_room, new_device

ONE_MEGABYTE = 1024 * 1024
ENCRYPTED_META = to_base64url(b"nome-do-arquivo-ja-criptografado")
UPLOAD_HEADERS = {"X-File-Meta": ENCRYPTED_META, "Content-Type": "application/octet-stream"}


def encrypted_bytes(size: int = 1000) -> bytes:
    """Bytes quaisquer: o servidor trata todo arquivo como conteúdo opaco."""
    return bytes(index % 251 for index in range(size))


def upload(client: TestClient, room_code: str, content: bytes | None = None, headers: dict | None = None):
    content = encrypted_bytes() if content is None else content
    return client.post(f"/api/rooms/{room_code}/files", content=content, headers=headers or UPLOAD_HEADERS)


def storage_files(tmp_path) -> list:
    return [path for path in (tmp_path / "storage").rglob("*") if path.is_file()]


# ---------- enviar ----------


def test_upload_returns_the_file_data(client):
    room = create_room(client)
    content = encrypted_bytes(5000)

    response = upload(client, room["code"], content)

    assert response.status_code == 201
    file = response.json()
    assert file["size_bytes"] == 5000
    assert file["encrypted_meta"] == ENCRYPTED_META
    assert file["created_at"].endswith("Z")


def test_upload_saves_the_bytes_on_disk_under_the_file_id(client, tmp_path):
    room = create_room(client)
    content = encrypted_bytes(5000)

    file = upload(client, room["code"], content).json()

    saved = storage_files(tmp_path)
    assert len(saved) == 1
    assert saved[0].name == file["id"]  # o nome do arquivo no disco é o id, nunca o nome original
    assert saved[0].read_bytes() == content


def test_any_kind_of_file_is_accepted(client):
    # O servidor não olha o tipo: o conteúdo chega criptografado e o nome vai dentro dos metadados.
    room = create_room(client)
    headers = UPLOAD_HEADERS | {"Content-Type": "application/x-msdownload"}

    assert upload(client, room["code"], headers=headers).status_code == 201


def test_upload_without_meta_is_rejected(client):
    room = create_room(client)

    response = upload(client, room["code"], headers={"Content-Type": "application/octet-stream"})

    assert response.status_code == 422


def test_upload_with_invalid_meta_is_rejected(client):
    room = create_room(client)

    assert upload(client, room["code"], headers={"X-File-Meta": "isto nao e base64 !!!"}).status_code == 422
    too_long = {"X-File-Meta": to_base64url(bytes(5000))}
    assert upload(client, room["code"], headers=too_long).status_code == 422


def test_an_empty_upload_is_rejected_and_leaves_nothing_on_disk(client, tmp_path):
    room = create_room(client)

    response = upload(client, room["code"], content=b"")

    assert response.status_code == 422
    assert storage_files(tmp_path) == []


# ---------- listar ----------


def test_list_shows_the_uploaded_files_in_order(client):
    room = create_room(client)
    first = upload(client, room["code"], encrypted_bytes(100)).json()
    second = upload(client, room["code"], encrypted_bytes(200)).json()

    response = client.get(f"/api/rooms/{room['code']}/files")

    assert response.status_code == 200
    assert [file["id"] for file in response.json()] == [first["id"], second["id"]]
    assert [file["size_bytes"] for file in response.json()] == [100, 200]


def test_a_new_room_has_no_files(client):
    room = create_room(client)

    assert client.get(f"/api/rooms/{room['code']}/files").json() == []


# ---------- baixar ----------


def test_download_returns_the_same_bytes_as_an_attachment(client):
    room = create_room(client)
    content = encrypted_bytes(5000)
    file = upload(client, room["code"], content).json()

    response = client.get(f"/api/rooms/{room['code']}/files/{file['id']}")

    assert response.status_code == 200
    assert response.content == content
    assert response.headers["content-type"] == "application/octet-stream"
    assert response.headers["content-disposition"].startswith("attachment")
    assert response.headers["x-content-type-options"] == "nosniff"


def test_download_of_an_unknown_file_is_404(client):
    room = create_room(client)

    response = client.get(f"/api/rooms/{room['code']}/files/00000000-0000-4000-8000-000000000000")

    assert response.status_code == 404


def test_a_file_id_that_is_not_a_uuid_is_rejected(client):
    room = create_room(client)

    assert client.get(f"/api/rooms/{room['code']}/files/..%2F..%2Fsegredo").status_code in (404, 422)
    assert client.get(f"/api/rooms/{room['code']}/files/abc").status_code == 422


# ---------- apagar ----------


def test_delete_removes_the_file_from_the_list_and_from_the_disk(client, tmp_path):
    room = create_room(client)
    file = upload(client, room["code"]).json()

    response = client.delete(f"/api/rooms/{room['code']}/files/{file['id']}")

    assert response.status_code == 204
    assert client.get(f"/api/rooms/{room['code']}/files").json() == []
    assert client.get(f"/api/rooms/{room['code']}/files/{file['id']}").status_code == 404
    assert storage_files(tmp_path) == []


def test_delete_of_an_unknown_file_is_404(client):
    room = create_room(client)

    response = client.delete(f"/api/rooms/{room['code']}/files/00000000-0000-4000-8000-000000000000")

    assert response.status_code == 404


# ---------- segurança ----------


def test_only_who_joined_the_room_can_use_its_files(client):
    room = create_room(client)
    file = upload(client, room["code"]).json()
    stranger = new_device(client)
    base_url = f"/api/rooms/{room['code']}/files"

    assert stranger.get(base_url).status_code == 401
    assert stranger.post(base_url, content=encrypted_bytes(), headers=UPLOAD_HEADERS).status_code == 401
    assert stranger.get(f"{base_url}/{file['id']}").status_code == 401
    assert stranger.delete(f"{base_url}/{file['id']}").status_code == 401


def test_a_file_cannot_be_reached_through_another_room(client):
    first_room = create_room(client)
    second_room = create_room(client)
    file = upload(client, first_room["code"]).json()

    # O cookie das duas salas está no mesmo cliente: o acesso à sala é permitido, mas o arquivo não é dela.
    assert client.get(f"/api/rooms/{second_room['code']}/files/{file['id']}").status_code == 404
    assert client.delete(f"/api/rooms/{second_room['code']}/files/{file['id']}").status_code == 404
    assert client.get(f"/api/rooms/{second_room['code']}/files").json() == []


def test_files_of_an_expired_room_are_not_reachable(client, monkeypatch):
    room = create_room(client, ttl_hours=1)
    upload(client, room["code"])
    in_two_hours = utc_now() + timedelta(hours=2)
    monkeypatch.setattr("app.room_service.utc_now", lambda: in_two_hours)

    assert client.get(f"/api/rooms/{room['code']}/files").status_code == 404


# ---------- limites de tamanho ----------


def test_a_file_over_the_size_limit_is_refused_and_nothing_is_kept(small_limits_client, tmp_path):
    room = create_room(small_limits_client)
    # Limite de 2 MB por arquivo (mais a folga de 1 MB do acréscimo da criptografia).
    too_big = encrypted_bytes(3 * ONE_MEGABYTE + 1)

    response = upload(small_limits_client, room["code"], too_big)

    assert response.status_code == 413
    assert response.json()["detail"] == "file_too_large"
    assert storage_files(tmp_path) == []
    assert small_limits_client.get(f"/api/rooms/{room['code']}/files").json() == []


def test_a_file_of_exactly_the_limit_is_accepted(small_limits_client):
    room = create_room(small_limits_client)

    response = upload(small_limits_client, room["code"], encrypted_bytes(2 * ONE_MEGABYTE))

    assert response.status_code == 201


def test_the_room_size_limit_counts_all_its_files(small_limits_client, tmp_path):
    room = create_room(small_limits_client)
    two_megabytes = encrypted_bytes(2 * ONE_MEGABYTE)
    assert upload(small_limits_client, room["code"], two_megabytes).status_code == 201

    # A sala comporta 3 MB; já tem 2 MB, então só cabem mais 1 MB.
    response = upload(small_limits_client, room["code"], two_megabytes)

    assert response.status_code == 413
    assert response.json()["detail"] == "room_full"
    assert len(storage_files(tmp_path)) == 1


def test_deleting_a_file_frees_space_in_the_room(small_limits_client):
    room = create_room(small_limits_client)
    two_megabytes = encrypted_bytes(2 * ONE_MEGABYTE)
    first = upload(small_limits_client, room["code"], two_megabytes).json()
    assert upload(small_limits_client, room["code"], two_megabytes).status_code == 413

    small_limits_client.delete(f"/api/rooms/{room['code']}/files/{first['id']}")

    assert upload(small_limits_client, room["code"], two_megabytes).status_code == 201


def test_a_full_room_refuses_any_new_file(small_limits_client):
    room = create_room(small_limits_client)
    for _ in range(3):
        assert upload(small_limits_client, room["code"], encrypted_bytes(ONE_MEGABYTE)).status_code == 201

    response = upload(small_limits_client, room["code"], encrypted_bytes(100))

    assert response.status_code == 413
    assert response.json()["detail"] == "room_full"
