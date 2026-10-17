import pytest

from app.encoding import from_base64url, to_base64url


def test_round_trip_keeps_the_same_bytes():
    data = bytes(range(256))

    assert from_base64url(to_base64url(data)) == data


def test_the_text_has_no_padding_and_is_url_safe():
    text = to_base64url(b"\xfb\xff\xfe")

    assert "=" not in text
    assert "+" not in text and "/" not in text


@pytest.mark.parametrize("invalid_text", ["isto não é base64", "abc def", "ab!d", "+/+/"])
def test_characters_outside_the_alphabet_are_refused(invalid_text):
    with pytest.raises(ValueError):
        from_base64url(invalid_text)
