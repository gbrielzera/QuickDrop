"""Rotas que entregam as páginas HTML do frontend."""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.config import FRONTEND_DIR, get_settings
from app.dependencies import RoomCode

templates = Jinja2Templates(directory=FRONTEND_DIR / "templates")

router = APIRouter(include_in_schema=False)

# Páginas que só existem durante o desenvolvimento (o app só inclui este router com DEBUG=true).
dev_router = APIRouter(include_in_schema=False)


@router.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    """Página inicial."""
    settings = get_settings()
    page_data = {
        "app_name": settings.app_name,
        "ttl_options": settings.ttl_options,
        "default_ttl": settings.default_ttl_hours,
    }
    return templates.TemplateResponse(request, "index.html", page_data)


@router.get("/r/{code}", response_class=HTMLResponse)
async def room_page(code: RoomCode, request: Request) -> HTMLResponse:
    """Página de uma sala. O navegador entra na sala e mostra o conteúdo (tudo é descriptografado lá)."""
    page_data = {"app_name": get_settings().app_name, "room_code": code}
    return templates.TemplateResponse(request, "room.html", page_data)


@dev_router.get("/dev/crypto", response_class=HTMLResponse)
async def dev_crypto(request: Request) -> HTMLResponse:
    """Página para testar a criptografia do navegador."""
    page_data = {"app_name": get_settings().app_name}
    return templates.TemplateResponse(request, "dev_crypto.html", page_data)
