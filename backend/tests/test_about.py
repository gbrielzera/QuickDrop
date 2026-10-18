from tests.conftest import start_test_client


def test_the_about_page_is_served(client):
    response = client.get("/sobre")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Sobre o QuickDrop" in response.text


def test_the_about_page_without_a_contact_does_not_show_a_mail_link(client):
    assert "mailto:" not in client.get("/sobre").text


def test_the_about_page_shows_the_abuse_contact_when_configured(tmp_path, monkeypatch):
    for client in start_test_client(tmp_path, monkeypatch, debug=False, CONTACT_EMAIL="abuso@exemplo.com"):
        page = client.get("/sobre").text

        assert 'href="mailto:abuso@exemplo.com"' in page
