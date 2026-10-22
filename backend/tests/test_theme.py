"""Botão de tema claro/escuro no topo das páginas."""


def test_every_page_has_the_theme_toggle_button(client):
    for path in ("/", "/sobre", "/r/ABCDEF"):
        page = client.get(path).text

        assert 'class="theme-toggle"' in page
        assert "js/theme-toggle.js" in page


def test_the_saved_theme_is_applied_before_the_stylesheet(client):
    page = client.get("/").text

    assert page.index("js/theme-init.js") < page.index("css/style.css")


def test_the_theme_scripts_are_served(client):
    for path in ("/static/js/theme-init.js", "/static/js/theme-toggle.js", "/static/js/theme.js"):
        assert client.get(path).status_code == 200
