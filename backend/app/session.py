"""Sessão de quem entrou numa sala: um cookie assinado, um por sala."""

from fastapi import Response
from itsdangerous import BadSignature, URLSafeTimedSerializer

from app.config import get_settings
from app.models import Room, utc_now

SESSION_SALT = "room-session"
MINIMUM_COOKIE_SECONDS = 1


def session_cookie_name(room_code: str) -> str:
    """Nome do cookie de uma sala. Cada sala tem o seu, então dá para estar em várias ao mesmo tempo."""
    return f"room_{room_code}"


def _serializer() -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(get_settings().secret_key, salt=SESSION_SALT)


def create_session_token(room_code: str) -> str:
    """Cria um token assinado que prova que o dispositivo entrou na sala."""
    return _serializer().dumps(room_code)


def read_session_token(token: str) -> str | None:
    """Devolve o código da sala guardado no token, ou None se o token for falso ou adulterado."""
    try:
        return _serializer().loads(token)
    except BadSignature:
        return None


def set_session_cookie(response: Response, room: Room) -> None:
    """Dá ao dispositivo o cookie da sala. Ele deixa de valer junto com a sala."""
    seconds_until_expiry = int((room.expires_at - utc_now()).total_seconds())
    response.set_cookie(
        key=session_cookie_name(room.code),
        value=create_session_token(room.code),
        max_age=max(seconds_until_expiry, MINIMUM_COOKIE_SECONDS),
        httponly=True,  # o JavaScript da página não consegue ler o cookie
        samesite="strict",
        secure=get_settings().cookie_secure,
    )
