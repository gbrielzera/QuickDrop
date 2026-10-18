"""Conexões em tempo real: quem está conectado em cada sala e envio de avisos a todos eles.

As conexões ficam na memória deste processo. Se um dia houver mais de um servidor rodando,
aqui entra um Redis para os servidores avisarem uns aos outros.
"""

import asyncio

from fastapi import WebSocket


class ConnectionManager:
    """Guarda os WebSockets abertos de cada sala."""

    def __init__(self) -> None:
        self._sockets_by_room: dict[str, set[WebSocket]] = {}

    def count(self, room_code: str) -> int:
        """Quantos aparelhos estão conectados na sala."""
        return len(self._sockets_by_room.get(room_code, set()))

    async def connect(self, room_code: str, websocket: WebSocket) -> None:
        """Aceita a conexão e avisa a todos que a sala tem mais um aparelho."""
        await websocket.accept()
        self._sockets_by_room.setdefault(room_code, set()).add(websocket)
        await self._broadcast_presence(room_code)

    async def disconnect(self, room_code: str, websocket: WebSocket) -> None:
        """Tira a conexão da sala e avisa a todos que a sala tem um aparelho a menos."""
        self._forget(room_code, websocket)
        await self._broadcast_presence(room_code)

    async def broadcast(self, room_code: str, message: dict) -> None:
        """Envia a mensagem para todos os aparelhos conectados na sala."""
        sockets = list(self._sockets_by_room.get(room_code, set()))
        await asyncio.gather(*(self._send(room_code, websocket, message) for websocket in sockets))

    async def _broadcast_presence(self, room_code: str) -> None:
        await self.broadcast(room_code, {"type": "presence", "online": self.count(room_code)})

    async def _send(self, room_code: str, websocket: WebSocket, message: dict) -> None:
        try:
            await websocket.send_json(message)
        except Exception:
            # Conexão que caiu sem avisar: deixa de contar. A rota do WebSocket termina sozinha.
            self._forget(room_code, websocket)

    def _forget(self, room_code: str, websocket: WebSocket) -> None:
        sockets = self._sockets_by_room.get(room_code)
        if sockets is None:
            return
        sockets.discard(websocket)
        if not sockets:
            del self._sockets_by_room[room_code]
