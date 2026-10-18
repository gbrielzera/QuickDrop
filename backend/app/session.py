"""Sessão de quem entrou numa sala: um cookie assinado, um por sala."""

from collections.abc import Mapping

from fastapi import Response
from itsdangerous import BadSignature, URLSafeTimedSerializer

from app.config import get_settings
from app.models import Room, utc_now

SESSION_SALT = "room-session"
OWNER_SALT = "room-owner"
MINIMUM_COOKIE_SECONDS = 1


def session_cookie_name(room_code: str) -> str:
    """Nome do cookie de uma sala. Cada sala tem o seu, então dá para estar em várias ao mesmo tempo."""
    return f"room_{room_code}"


def owner_cookie_name(room_code: str) -> str:
    """Nome do cookie de dono de uma sala. Só o navegador que criou a sala o recebe."""
    return f"owner_{room_code}"


def _serializer(salt: str = SESSION_SALT) -> URLSafeTimedSerializer:
    # Cada tipo de cookie tem o seu "sal": um token de participante nunca vale como token de dono.
    return URLSafeTimedSerializer(get_settings().secret_key, salt=salt)


def create_session_token(room_id: str) -> str:
    """Cria um token assinado que prova que o dispositivo entrou na sala."""
    return _serializer().dumps(room_id)


def read_session_token(token: str) -> str | None:
    """Devolve o id da sala guardado no token, ou None se o token for falso ou adulterado."""
    try:
        return _serializer().loads(token)
    except BadSignature:
        return None


def has_session_for_room(cookies: Mapping[str, str], room: Room) -> bool:
    """True se os cookies provam que este dispositivo entrou na sala.

    O token guarda o id interno da sala, não o código: se um dia outra sala receber um código antigo,
    os cookies da sala anterior não valem nela.
    """
    token = cookies.get(session_cookie_name(room.code))
    return token is not None and read_session_token(token) == room.id


def is_room_owner(cookies: Mapping[str, str], room: Room) -> bool:
    """True se os cookies provam que este navegador criou a sala."""
    token = cookies.get(owner_cookie_name(room.code))
    if token is None:
        return False
    try:
        # O token guarda o id interno da sala, não o código: não serve para outra sala com o mesmo código.
        return _serializer(OWNER_SALT).loads(token) == room.id
    except BadSignature:
        return False


def _set_room_cookie(response: Response, room: Room, name: str, value: str) -> None:
    seconds_until_expiry = int((room.expires_at - utc_now()).total_seconds())
    response.set_cookie(
        key=name,
        value=value,
        max_age=max(seconds_until_expiry, MINIMUM_COOKIE_SECONDS),
        httponly=True,  # o JavaScript da página não consegue ler o cookie
        samesite="strict",
        secure=get_settings().cookie_secure,
    )


def set_session_cookie(response: Response, room: Room) -> None:
    """Dá ao dispositivo o cookie da sala. Ele deixa de valer junto com a sala."""
    _set_room_cookie(response, room, session_cookie_name(room.code), create_session_token(room.id))


def set_owner_cookie(response: Response, room: Room) -> None:
    """Marca este navegador como o dono da sala (só quem criou recebe)."""
    owner_token = _serializer(OWNER_SALT).dumps(room.id)
    _set_room_cookie(response, room, owner_cookie_name(room.code), owner_token)
