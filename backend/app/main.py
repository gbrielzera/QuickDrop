"""Ponto de entrada do backend: cria o app FastAPI e liga as rotas."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.config import FRONTEND_DIR, get_settings
from app.database import create_engine, create_session_maker, create_tables
from app.realtime import ConnectionManager
from app.routers import files, pages, rooms, ws


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Prepara o que o app precisa antes de começar a receber requisições."""
    settings = get_settings()
    settings.storage_dir.mkdir(parents=True, exist_ok=True)

    engine = create_engine(settings.database_url)
    await create_tables(engine)
    app.state.session_maker = create_session_maker(engine)
    app.state.connections = ConnectionManager()

    yield

    await engine.dispose()


def create_app() -> FastAPI:
    """Monta o app: API, páginas do frontend e arquivos estáticos (CSS e JS)."""
    settings = get_settings()
    app = FastAPI(title=settings.app_name, debug=settings.debug, lifespan=lifespan)

    app.mount("/static", StaticFiles(directory=FRONTEND_DIR / "static"), name="static")
    app.include_router(pages.router)
    app.include_router(rooms.router)
    app.include_router(files.router)
    app.include_router(ws.router)
    if settings.debug:
        app.include_router(pages.dev_router)

    @app.get("/api/health", tags=["sistema"])
    async def health() -> dict[str, str]:
        """Responde se o servidor está no ar."""
        return {"status": "ok", "app": settings.app_name}

    return app


app = create_app()
