"""Cabeçalhos de segurança que o servidor acrescenta a todas as respostas HTTP."""

from starlette.datastructures import MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

# O app só carrega código, estilos e fontes do próprio servidor. "wasm-unsafe-eval" é necessário para
# o módulo WebAssembly da criptografia (libsodium); não permite executar texto como JavaScript.
CONTENT_SECURITY_POLICY = "; ".join(
    [
        "default-src 'self'",
        "script-src 'self' 'wasm-unsafe-eval'",
        "style-src 'self'",
        "img-src 'self' data: blob:",
        "font-src 'self'",
        "connect-src 'self' ws: wss:",
        "object-src 'none'",
        "base-uri 'none'",
        "form-action 'self'",
        "frame-ancestors 'none'",
    ]
)

SECURITY_HEADERS = {
    "Content-Security-Policy": CONTENT_SECURITY_POLICY,
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    # O código da sala aparece no endereço da página: nunca o repassamos a outros sites.
    "Referrer-Policy": "no-referrer",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=(), payment=()",
}

# Diz ao navegador para usar só HTTPS neste site por um ano. Só faz sentido quando o site está em HTTPS.
HSTS_VALUE = "max-age=31536000"


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
                self._add_headers(MutableHeaders(scope=message), scope["path"])
            await send(message)

        await self.app(scope, receive, send_with_security_headers)

    def _add_headers(self, headers: MutableHeaders, path: str) -> None:
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
