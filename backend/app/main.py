"""Ponto de entrada do backend: cria o app FastAPI e liga as rotas."""

import asyncio
from contextlib import asynccontextmanager, suppress

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.cleanup import delete_expired_rooms, run_cleanup_loop
from app.config import FRONTEND_DIR, get_settings
from app.database import create_engine, create_session_maker, create_tables
from app.rate_limit import create_rate_limits
from app.realtime import ConnectionManager
from app.routers import clips, files, pages, rooms, text, ws
from app.security_headers import SecurityHeadersMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Prepara o que o app precisa antes de começar a receber requisições."""
    settings = get_settings()
    settings.storage_dir.mkdir(parents=True, exist_ok=True)

    engine = create_engine(settings.database_url)
    await create_tables(engine)
    app.state.session_maker = create_session_maker(engine)
    app.state.connections = ConnectionManager()
    app.state.rate_limits = create_rate_limits(settings)

    await delete_expired_rooms(app)  # limpa o que expirou enquanto o servidor estava desligado
    cleanup_task = asyncio.create_task(run_cleanup_loop(app, settings.cleanup_interval_minutes))

    yield

    cleanup_task.cancel()
    with suppress(asyncio.CancelledError):
        await cleanup_task
    await engine.dispose()


def create_app() -> FastAPI:
    """Monta o app: API, páginas do frontend e arquivos estáticos (CSS e JS)."""
    settings = get_settings()
    app = FastAPI(title=settings.app_name, debug=settings.debug, lifespan=lifespan)
    app.add_middleware(SecurityHeadersMiddleware, hsts_enabled=settings.cookie_secure)

    app.mount("/static", StaticFiles(directory=FRONTEND_DIR / "static"), name="static")
    app.include_router(pages.router)
    app.include_router(rooms.router)
    app.include_router(files.router)
    app.include_router(text.router)
    app.include_router(clips.router)
    app.include_router(ws.router)
    if settings.debug:
        app.include_router(pages.dev_router)

    @app.get("/api/health", tags=["sistema"])
    async def health() -> dict[str, str]:
        """Responde se o servidor está no ar."""
        return {"status": "ok", "app": settings.app_name}

    return app


app = create_app()
