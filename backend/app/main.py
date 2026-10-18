"""Ponto de entrada do backend: cria o app FastAPI e liga as rotas."""

import asyncio
from contextlib import asynccontextmanager, suppress

from fastapi import Depends, FastAPI
from fastapi.staticfiles import StaticFiles

from app.cleanup import delete_expired_rooms, run_cleanup_loop
from app.config import FRONTEND_DIR, get_settings
from app.database import create_engine, create_session_maker, create_tables
from app.dependencies import limit_api_requests
from app.rate_limit import create_rate_limits
from app.realtime import ConnectionManager
from app.routers import clips, documents, files, pages, rooms, ws
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
    app.state.upload_lock = asyncio.Lock()

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
    # A documentação automática da API só existe no desenvolvimento: em produção não ajuda ninguém além de
    # quem procura pontos de ataque.
    docs_urls = {} if settings.debug else {"docs_url": None, "redoc_url": None, "openapi_url": None}
    app = FastAPI(title=settings.app_name, debug=settings.debug, lifespan=lifespan, **docs_urls)
    app.add_middleware(SecurityHeadersMiddleware, hsts_enabled=settings.cookie_secure)

    app.mount("/static", StaticFiles(directory=FRONTEND_DIR / "static"), name="static")
    app.include_router(pages.router)
    # Todas as rotas da API (menos /api/health, que o monitoramento consulta) respeitam o teto geral por IP.
    api_limit = [Depends(limit_api_requests)]
    app.include_router(rooms.router, dependencies=api_limit)
    app.include_router(files.router, dependencies=api_limit)
    app.include_router(documents.text_router, dependencies=api_limit)
    app.include_router(documents.source_router, dependencies=api_limit)
    app.include_router(clips.text_clips_router, dependencies=api_limit)
    app.include_router(clips.code_clips_router, dependencies=api_limit)
    app.include_router(ws.router)
    if settings.debug:
        app.include_router(pages.dev_router)

    @app.get("/api/health", tags=["sistema"])
    async def health() -> dict[str, str]:
        """Responde se o servidor está no ar."""
        return {"status": "ok", "app": settings.app_name}

    return app


app = create_app()
