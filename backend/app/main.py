"""Ponto de entrada do backend: cria o app FastAPI e liga as rotas."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.config import FRONTEND_DIR, get_settings
from app.routers import pages


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Prepara o que o app precisa antes de começar a receber requisições."""
    get_settings().storage_dir.mkdir(parents=True, exist_ok=True)
    yield


def create_app() -> FastAPI:
    """Monta o app: API, páginas do frontend e arquivos estáticos (CSS e JS)."""
    settings = get_settings()
    app = FastAPI(title=settings.app_name, debug=settings.debug, lifespan=lifespan)

    app.mount("/static", StaticFiles(directory=FRONTEND_DIR / "static"), name="static")
    app.include_router(pages.router)

    @app.get("/api/health", tags=["sistema"])
    async def health() -> dict[str, str]:
        """Responde se o servidor está no ar."""
        return {"status": "ok", "app": settings.app_name}

    return app


app = create_app()
