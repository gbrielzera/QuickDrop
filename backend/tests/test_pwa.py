def test_the_service_worker_is_served_from_the_root_without_cache(client):
    response = client.get("/service-worker.js")

    assert response.status_code == 200
    assert "javascript" in response.headers["content-type"]
    assert response.headers["cache-control"] == "no-cache"
    assert "addEventListener" in response.text


def test_the_service_worker_does_not_cache_rooms_or_the_api(client):
    # Salas, arquivos e API nunca vão para o cache: o worker só dá plano B para páginas.
    code = client.get("/service-worker.js").text

    assert 'event.request.mode !== "navigate"' in code
    assert "/api/" not in code


def test_the_manifest_describes_an_installable_app(client):
    response = client.get("/manifest.webmanifest")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/manifest+json")
    manifest = response.json()
    assert manifest["name"] == "QuickDrop"
    assert manifest["display"] == "standalone"
    assert manifest["start_url"] == "/"
    sizes = {icon["sizes"] for icon in manifest["icons"]}
    assert {"192x192", "512x512"} <= sizes
    assert any(icon.get("purpose") == "maskable" for icon in manifest["icons"])


def test_every_icon_in_the_manifest_exists(client):
    manifest = client.get("/manifest.webmanifest").json()

    for icon in manifest["icons"]:
        response = client.get(icon["src"])
        assert response.status_code == 200, icon["src"]
        assert response.headers["content-type"] == "image/png"


def test_pages_link_the_manifest_the_icons_and_register_the_worker(client):
    html = client.get("/").text

    assert 'rel="manifest" href="/manifest.webmanifest"' in html
    assert "apple-touch-icon" in html
    assert 'name="theme-color"' in html
    assert "js/pwa.js" in html


def test_the_offline_page_exists_and_needs_no_inline_code(client):
    response = client.get("/static/offline.html")

    assert response.status_code == 200
    # A política de segurança proíbe estilos e scripts escritos dentro do HTML.
    assert "<style" not in response.text
    assert "<script" not in response.text
    assert "onclick" not in response.text
