"""Conversão entre bytes e texto base64url, o formato que o navegador e o servidor trocam."""

import base64
import binascii


def to_base64url(data: bytes) -> str:
    """Transforma bytes em texto seguro para URL e JSON, sem o "=" do final."""
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def from_base64url(text: str) -> bytes:
    """Faz o caminho inverso de to_base64url. Lança ValueError se o texto for inválido."""
    if "+" in text or "/" in text:
        raise ValueError("Texto base64url inválido.")  # "+" e "/" são do base64 comum, não do base64url
    padding = "=" * (-len(text) % 4)
    try:
        # validate=True recusa qualquer caractere fora do alfabeto (sem isso, o Python os ignora em silêncio).
        return base64.b64decode(text + padding, altchars=b"-_", validate=True)
    except (binascii.Error, ValueError) as error:
        raise ValueError("Texto base64url inválido.") from error
