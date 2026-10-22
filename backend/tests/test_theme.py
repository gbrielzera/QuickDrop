"""Botão de tema claro/escuro no topo das páginas."""


def test_every_page_has_the_theme_toggle_button(client):
    for path in ("/", "/sobre", "/r/ABCDEF"):
        page = client.get(path).text

        assert "topbar__icon theme-toggle" in page
        assert "js/theme-toggle.js" in page


def test_the_saved_theme_is_applied_before_the_stylesheet(client):
    page = client.get("/").text

    assert page.index("js/theme-init.js") < page.index("css/style.css")


def test_the_theme_scripts_are_served(client):
    for path in ("/static/js/theme-init.js", "/static/js/theme-toggle.js", "/static/js/theme.js"):
        assert client.get(path).status_code == 200


def test_the_about_link_is_in_the_top_bar_and_not_in_a_footer(client):
    for path in ("/", "/r/ABCDEF"):
        page = client.get(path).text

        assert page.index('href="/sobre"') < page.index("<main")
        assert "<footer" not in page


def test_the_about_page_marks_its_own_link_as_the_current_page(client):
    assert 'title="Sobre" aria-current="page"' in client.get("/sobre").text
    assert 'aria-current="page"' not in client.get("/").text
