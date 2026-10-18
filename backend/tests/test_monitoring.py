"""Teto geral de pedidos por IP e contagem de eventos de segurança (sem dados pessoais)."""

import logging

import pytest

from app.security_events import (
    FAILED_JOIN,
    LOCKED_JOIN,
    NOT_OWNER_ATTEMPT,
    RATE_LIMITED,
    SecurityEvents,
    security_events,
)
from tests.conftest import start_test_client
from tests.test_files import encrypted_bytes, upload
from tests.test_rooms import AUTH_KEY, OTHER_AUTH_KEY, create_room, new_device

# ---------- teto geral ----------


@pytest.fixture
def tight_api_client(tmp_path, monkeypatch):
    yield from start_test_client(
        tmp_path, monkeypatch, debug=False, RATE_LIMIT_API_PER_MINUTE="5", RATE_LIMIT_UPLOADS_PER_HOUR="2"
    )


def test_the_api_has_a_general_cap_per_ip(tight_api_client):
    room = create_room(tight_api_client)  # 1 pedido

    for _ in range(4):
        assert tight_api_client.get(f"/api/rooms/{room['code']}").status_code == 200
    response = tight_api_client.get(f"/api/rooms/{room['code']}")

    assert response.status_code == 429
    assert int(response.headers["Retry-After"]) >= 1


def test_the_health_check_is_never_limited(tight_api_client):
    for _ in range(20):
        assert tight_api_client.get("/api/health").status_code == 200


def test_uploads_have_their_own_cap_per_ip(tight_api_client):
    room = create_room(tight_api_client)
    assert upload(tight_api_client, room["code"], encrypted_bytes()).status_code == 201
    assert upload(tight_api_client, room["code"], encrypted_bytes()).status_code == 201

    response = upload(tight_api_client, room["code"], encrypted_bytes())

    assert response.status_code == 429


# ---------- eventos de segurança ----------


def test_a_wrong_password_is_counted(client):
    room = create_room(client)

    new_device(client).post(f"/api/rooms/{room['code']}/join", json={"auth_key": OTHER_AUTH_KEY})

    assert security_events.count(FAILED_JOIN) == 1


def test_a_guest_trying_owner_actions_is_counted(client):
    room = create_room(client)
    guest = new_device(client)
    guest.post(f"/api/rooms/{room['code']}/join", json={"auth_key": AUTH_KEY})

    guest.put(f"/api/rooms/{room['code']}/lock", json={"locked": True})
    guest.delete(f"/api/rooms/{room['code']}")

    assert security_events.count(NOT_OWNER_ATTEMPT) == 2


def test_joining_a_locked_room_is_counted(client):
    room = create_room(client)
    client.put(f"/api/rooms/{room['code']}/lock", json={"locked": True})

    new_device(client).post(f"/api/rooms/{room['code']}/join", json={"auth_key": AUTH_KEY})

    assert security_events.count(LOCKED_JOIN) == 1


def test_a_refused_request_is_counted(strict_limits_client):
    room = create_room(strict_limits_client)
    for _ in range(5):
        strict_limits_client.get(f"/api/rooms/{room['code']}/params")

    assert security_events.count(RATE_LIMITED) >= 1


def test_the_summary_lists_only_names_and_counts_and_starts_over(caplog):
    events = SecurityEvents(summary_interval_seconds=0)
    events.record(FAILED_JOIN)
    events.record(FAILED_JOIN)
    events.record(RATE_LIMITED)

    with caplog.at_level(logging.WARNING):
        events.log_summary_if_due()
        events.log_summary_if_due()

    assert [record.getMessage() for record in caplog.records] == [
        f"Resumo de segurança da última hora: {RATE_LIMITED}=1, {FAILED_JOIN}=2"
    ]


def test_no_summary_is_written_when_nothing_happened(caplog):
    events = SecurityEvents(summary_interval_seconds=0)

    with caplog.at_level(logging.WARNING):
        events.log_summary_if_due()

    assert caplog.records == []


def test_the_summary_waits_for_the_interval(caplog):
    events = SecurityEvents(summary_interval_seconds=3600)
    events.record(FAILED_JOIN)

    with caplog.at_level(logging.WARNING):
        events.log_summary_if_due()

    assert caplog.records == []
    assert events.count(FAILED_JOIN) == 1
