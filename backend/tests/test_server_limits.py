"""Limites do servidor inteiro: espaço total em disco e número de salas ativas."""

from tests.test_files import ONE_MEGABYTE, encrypted_bytes, storage_files, upload
from tests.test_rooms import create_room, create_room_payload


def test_files_of_all_rooms_count_toward_the_server_storage_limit(small_server_client, tmp_path):
    first_room = create_room(small_server_client)
    second_room = create_room(small_server_client)
    assert upload(small_server_client, first_room["code"], encrypted_bytes(ONE_MEGABYTE)).status_code == 201

    # O servidor comporta 2 MB; já tem 1 MB em outra sala, então só cabe mais 1 MB.
    too_big = upload(small_server_client, second_room["code"], encrypted_bytes(ONE_MEGABYTE + 1))

    assert too_big.status_code == 507
    assert too_big.json()["detail"] == "server_full"
    assert len(storage_files(tmp_path)) == 1


def test_a_file_that_fits_the_remaining_server_space_is_accepted(small_server_client):
    first_room = create_room(small_server_client)
    second_room = create_room(small_server_client)
    upload(small_server_client, first_room["code"], encrypted_bytes(ONE_MEGABYTE))

    response = upload(small_server_client, second_room["code"], encrypted_bytes(ONE_MEGABYTE))

    assert response.status_code == 201


def test_a_full_server_refuses_any_new_file(small_server_client):
    room = create_room(small_server_client)
    for _ in range(2):
        assert upload(small_server_client, room["code"], encrypted_bytes(ONE_MEGABYTE)).status_code == 201

    response = upload(small_server_client, room["code"], encrypted_bytes(100))

    assert response.status_code == 507
    assert response.json()["detail"] == "server_full"


def test_deleting_a_file_frees_server_space(small_server_client):
    room = create_room(small_server_client)
    first = upload(small_server_client, room["code"], encrypted_bytes(ONE_MEGABYTE)).json()
    upload(small_server_client, room["code"], encrypted_bytes(ONE_MEGABYTE))
    assert upload(small_server_client, room["code"], encrypted_bytes(100)).status_code == 507

    small_server_client.delete(f"/api/rooms/{room['code']}/files/{first['id']}")

    assert upload(small_server_client, room["code"], encrypted_bytes(100)).status_code == 201


def test_no_new_room_is_created_when_the_server_has_the_maximum_of_active_rooms(small_server_client):
    create_room(small_server_client)
    create_room(small_server_client)

    third_room = small_server_client.post("/api/rooms", json=create_room_payload())

    assert third_room.status_code == 503
    assert third_room.json()["detail"] == "server_full"


def test_closing_a_room_makes_space_for_a_new_one(small_server_client):
    first_room = create_room(small_server_client)
    create_room(small_server_client)
    small_server_client.delete(f"/api/rooms/{first_room['code']}")

    assert small_server_client.post("/api/rooms", json=create_room_payload()).status_code == 201
