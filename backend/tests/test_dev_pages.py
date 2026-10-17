def test_dev_crypto_page_is_available_in_debug_mode(debug_client):
    response = debug_client.get("/dev/crypto")

    assert response.status_code == 200
    assert "js/dev-crypto.js" in response.text


def test_dev_crypto_page_does_not_exist_without_debug(client):
    response = client.get("/dev/crypto")

    assert response.status_code == 404


def test_javascript_modules_are_served_with_a_javascript_content_type(client):
    # Navegadores recusam módulos .mjs/.js entregues com outro tipo de conteúdo.
    for path in ("/static/js/crypto.js", "/static/js/vendor/libsodium-wrappers.mjs"):
        response = client.get(path)

        assert response.status_code == 200
        assert "javascript" in response.headers["content-type"]
