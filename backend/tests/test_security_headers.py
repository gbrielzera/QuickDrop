from tests.test_rooms import create_room


def test_pages_have_the_security_headers(client):
    response = client.get("/")

    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["referrer-policy"] == "no-referrer"
    assert "camera=()" in response.headers["permissions-policy"]


def test_the_content_security_policy_only_allows_our_own_code(client):
    policy = client.get("/").headers["content-security-policy"]

    assert "default-src 'self'" in policy
    assert "script-src 'self' 'wasm-unsafe-eval'" in policy
    assert "frame-ancestors 'none'" in policy
    assert "object-src 'none'" in policy
    # Nada de scripts ou estilos escritos dentro do HTML, nem execução de texto como código.
    assert "'unsafe-inline'" not in policy
    assert "'unsafe-eval'" not in policy


def test_static_files_and_the_api_have_the_security_headers_too(client):
    room = create_room(client)

    for path in ("/static/css/style.css", f"/api/rooms/{room['code']}", "/api/health"):
        response = client.get(path)
        assert response.headers["x-content-type-options"] == "nosniff", path
        assert "content-security-policy" in response.headers, path


def test_api_responses_are_never_cached(client):
    room = create_room(client)

    assert client.get(f"/api/rooms/{room['code']}").headers["cache-control"] == "no-store"
    assert client.get("/api/health").headers["cache-control"] == "no-store"


def test_static_files_are_revalidated_so_an_update_is_never_missed(client):
    first = client.get("/static/css/style.css")

    assert first.headers["cache-control"] == "no-cache"
    # Com o "etag" o navegador pergunta se mudou e recebe 304 (sem baixar de novo) quando não mudou.
    second = client.get("/static/css/style.css", headers={"if-none-match": first.headers["etag"]})
    assert second.status_code == 304


def test_pages_have_no_cache_header_of_their_own(client):
    assert "cache-control" not in client.get("/").headers


def test_the_download_keeps_its_own_no_store_header(client):
    from tests.test_files import upload

    room = create_room(client)
    file = upload(client, room["code"]).json()

    response = client.get(f"/api/rooms/{room['code']}/files/{file['id']}")

    assert response.headers["cache-control"] == "no-store"


def test_https_is_only_required_when_the_site_runs_on_https(client, https_client):
    assert "strict-transport-security" not in client.get("/").headers
    assert https_client.get("/").headers["strict-transport-security"] == "max-age=31536000"
