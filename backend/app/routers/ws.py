"""WebSocket de uma sala: avisa em tempo real o que acontece nela.

Mensagens do servidor para o navegador (JSON, com o campo "type"):
- presence: {"online": 2}  quantos aparelhos estão conectados
- file_added: {"file": {...}}  um arquivo novo
- file_deleted: {"file_id": "..."}  um arquivo apagado
- pong: resposta ao "ping" do navegador (mantém a conexão viva)
"""

from urllib.parse import urlparse

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.dependencies import RoomCode
from app.room_service import find_active_room
from app.session import has_session_for_room

router = APIRouter()

WEBSOCKET_POLICY_VIOLATION = 1008
WEBSOCKET_UNSUPPORTED_DATA = 1003


def _comes_from_this_site(websocket: WebSocket) -> bool:
    """Recusa conexões abertas por páginas de outros sites (o navegador sempre informa a origem)."""
    origin = websocket.headers.get("origin")
    if origin is None:
        return True  # programas que não são navegadores não enviam origem; o cookie continua sendo exigido
    return urlparse(origin).netloc == websocket.headers.get("host")


async def _room_exists(websocket: WebSocket, room_code: str) -> bool:
    # A sessão do banco é aberta só para esta consulta, não fica presa durante a conexão inteira.
    async with websocket.app.state.session_maker() as db:
        return await find_active_room(db, room_code) is not None


@router.websocket("/ws/rooms/{code}")
async def room_socket(websocket: WebSocket, code: RoomCode) -> None:
    """Mantém a conexão de um aparelho com a sala. Só entra quem tem o cookie da sala."""
    allowed = _comes_from_this_site(websocket) and has_session_for_room(websocket.cookies, code)
    if not allowed or not await _room_exists(websocket, code):
        await websocket.close(code=WEBSOCKET_POLICY_VIOLATION)
        return

    connections = websocket.app.state.connections
    await connections.connect(code, websocket)
    try:
        while True:
            message = await websocket.receive_json()
            if isinstance(message, dict) and message.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        pass
    except ValueError:
        await websocket.close(code=WEBSOCKET_UNSUPPORTED_DATA)  # mensagem que não é JSON
    finally:
        await connections.disconnect(code, websocket)
