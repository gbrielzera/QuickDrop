"""Rotas que entregam as páginas HTML do frontend."""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.config import FRONTEND_DIR, get_settings

templates = Jinja2Templates(directory=FRONTEND_DIR / "templates")

router = APIRouter(include_in_schema=False)


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
