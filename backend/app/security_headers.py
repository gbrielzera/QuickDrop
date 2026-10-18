"""Cabeçalhos de segurança que o servidor acrescenta a todas as respostas HTTP."""

import re

from starlette.datastructures import Headers, MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

# O app só carrega código, estilos e fontes do próprio servidor. "wasm-unsafe-eval" é necessário para
# o módulo WebAssembly da criptografia (libsodium); não permite executar texto como JavaScript.
# O {websocket_hosts} é preenchido com o endereço do próprio site: alguns navegadores não entendem que
# o 'self' também vale para WebSocket, mas nenhum deles deixa a página falar com outro servidor.
CONTENT_SECURITY_POLICY = "; ".join(
    [
        "default-src 'self'",
        "script-src 'self' 'wasm-unsafe-eval'",
        "style-src 'self'",
        "img-src 'self' data: blob:",
        "font-src 'self'",
        "connect-src 'self'{websocket_hosts}",
        "object-src 'none'",
        "base-uri 'none'",
        "form-action 'self'",
        "frame-ancestors 'none'",
    ]
)

SAFE_HOST_PATTERN = re.compile(r"^[A-Za-z0-9.\-]+(:[0-9]{1,5})?$")

SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    # O código da sala aparece no endereço da página: nunca o repassamos a outros sites.
    "Referrer-Policy": "no-referrer",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=(), payment=()",
}

# Diz ao navegador para usar só HTTPS neste site por um ano. Só faz sentido quando o site está em HTTPS.
HSTS_VALUE = "max-age=31536000"


def _content_security_policy(request_host: str) -> str:
    """A política de segurança, com o WebSocket liberado só para o endereço deste site."""
    if not SAFE_HOST_PATTERN.match(request_host):
        return CONTENT_SECURITY_POLICY.format(websocket_hosts="")
    return CONTENT_SECURITY_POLICY.format(websocket_hosts=f" ws://{request_host} wss://{request_host}")


class SecurityHeadersMiddleware:
    """Acrescenta os cabeçalhos de segurança a cada resposta HTTP (WebSockets não passam por aqui)."""

    def __init__(self, app: ASGIApp, hsts_enabled: bool) -> None:
        self.app = app
        self.hsts_enabled = hsts_enabled

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def send_with_security_headers(message: Message) -> None:
            if message["type"] == "http.response.start":
                request_host = Headers(scope=scope).get("host", "")
                self._add_headers(MutableHeaders(scope=message), scope["path"], request_host)
            await send(message)

        await self.app(scope, receive, send_with_security_headers)

    def _add_headers(self, headers: MutableHeaders, path: str, request_host: str) -> None:
        headers.setdefault("Content-Security-Policy", _content_security_policy(request_host))
        for name, value in SECURITY_HEADERS.items():
            headers.setdefault(name, value)
        if self.hsts_enabled:
            headers.setdefault("Strict-Transport-Security", HSTS_VALUE)
        if path.startswith("/api/"):
            # As respostas da API têm dados da sala: nada de guardá-las em cache.
            headers.setdefault("Cache-Control", "no-store")
        elif path.startswith("/static/"):
            # Sem isto o navegador pode reaproveitar por horas um JavaScript antigo depois de uma atualização.
            # "no-cache" deixa guardar, mas pergunta ao servidor se mudou (e ele responde 304 se não mudou).
            headers.setdefault("Cache-Control", "no-cache")
