import pytest

from app.rate_limit import RateLimiter
from tests.test_rooms import AUTH_KEY, OTHER_AUTH_KEY, create_room, create_room_payload, new_device


class FakeClock:
    """Relógio de mentira: o tempo só passa quando o teste manda."""

    def __init__(self):
        self.seconds = 1000.0

    def __call__(self) -> float:
        return self.seconds


@pytest.fixture
def clock(monkeypatch):
    fake_clock = FakeClock()
    monkeypatch.setattr("app.rate_limit._now", fake_clock)
    return fake_clock


# ---------- o contador ----------


def test_a_key_is_blocked_after_reaching_the_limit(clock):
    limiter = RateLimiter(max_hits=3, window_seconds=60)

    for _ in range(3):
        assert not limiter.is_blocked("ip")
        limiter.record("ip")

    assert limiter.is_blocked("ip")


def test_each_key_has_its_own_count(clock):
    limiter = RateLimiter(max_hits=1, window_seconds=60)
    limiter.record("first")

    assert limiter.is_blocked("first")
    assert not limiter.is_blocked("second")


def test_the_key_is_free_again_after_the_window(clock):
    limiter = RateLimiter(max_hits=1, window_seconds=60)
    limiter.record("ip")

    clock.seconds += 60

    assert not limiter.is_blocked("ip")


def test_seconds_until_free_counts_down(clock):
    limiter = RateLimiter(max_hits=1, window_seconds=60)
    limiter.record("ip")
    clock.seconds += 20

    assert limiter.seconds_until_free("ip") == 40
    assert limiter.seconds_until_free("someone-else") == 0


def test_reset_forgets_the_key(clock):
    limiter = RateLimiter(max_hits=1, window_seconds=60)
    limiter.record("ip")

    limiter.reset("ip")

    assert not limiter.is_blocked("ip")


def test_idle_keys_are_forgotten_to_free_memory(clock):
    limiter = RateLimiter(max_hits=5, window_seconds=60)
    limiter.record("ip")
    clock.seconds += 61

    limiter.forget_idle_keys()

    assert limiter._hits_by_key == {}


# ---------- senha errada ----------


def test_too_many_wrong_passwords_block_the_next_attempts(strict_limits_client, clock):
    client = strict_limits_client
    room = create_room(client)
    join_url = f"/api/rooms/{room['code']}/join"
    other_device = new_device(client)

    for _ in range(3):
        assert other_device.post(join_url, json={"auth_key": OTHER_AUTH_KEY}).status_code == 401

    blocked = other_device.post(join_url, json={"auth_key": OTHER_AUTH_KEY})
    assert blocked.status_code == 429
    assert blocked.json()["detail"] == "too_many_attempts"
    assert int(blocked.headers["retry-after"]) > 0


def test_the_right_password_is_also_refused_while_blocked(strict_limits_client, clock):
    client = strict_limits_client
    room = create_room(client)
    join_url = f"/api/rooms/{room['code']}/join"
    other_device = new_device(client)
    for _ in range(3):
        other_device.post(join_url, json={"auth_key": OTHER_AUTH_KEY})

    assert other_device.post(join_url, json={"auth_key": AUTH_KEY}).status_code == 429


def test_after_the_wait_the_right_password_works_again(strict_limits_client, clock):
    client = strict_limits_client
    room = create_room(client)
    join_url = f"/api/rooms/{room['code']}/join"
    other_device = new_device(client)
    for _ in range(3):
        other_device.post(join_url, json={"auth_key": OTHER_AUTH_KEY})

    clock.seconds += 61

    assert other_device.post(join_url, json={"auth_key": AUTH_KEY}).status_code == 200


def test_the_wrong_password_count_is_per_room(strict_limits_client, clock):
    client = strict_limits_client
    first_room = create_room(client)
    second_room = create_room(client, ttl_hours=24)
    other_device = new_device(client)
    for _ in range(3):
        other_device.post(f"/api/rooms/{first_room['code']}/join", json={"auth_key": OTHER_AUTH_KEY})

    response = other_device.post(f"/api/rooms/{second_room['code']}/join", json={"auth_key": OTHER_AUTH_KEY})

    assert response.status_code == 401  # errou a senha, mas não está bloqueado nesta sala


# ---------- consultas e criação de salas ----------


def test_too_many_lookups_from_the_same_address_are_refused(strict_limits_client, clock):
    client = strict_limits_client

    statuses = [client.get("/api/rooms/ZZZZZZ/params").status_code for _ in range(5)]

    assert statuses == [404, 404, 404, 404, 429]


def test_the_lookup_limit_applies_to_entering_too(strict_limits_client, clock):
    client = strict_limits_client
    for _ in range(4):
        client.get("/api/rooms/ZZZZZZ/params")

    response = client.post("/api/rooms/ZZZZZZ/join", json={"auth_key": AUTH_KEY})

    assert response.status_code == 429


def test_lookups_work_again_after_the_wait(strict_limits_client, clock):
    client = strict_limits_client
    for _ in range(5):
        client.get("/api/rooms/ZZZZZZ/params")

    clock.seconds += 61

    assert client.get("/api/rooms/ZZZZZZ/params").status_code == 404


def test_too_many_rooms_created_from_the_same_address_are_refused(strict_limits_client, clock):
    client = strict_limits_client

    statuses = [client.post("/api/rooms", json=create_room_payload()).status_code for _ in range(3)]

    assert statuses == [201, 201, 429]
