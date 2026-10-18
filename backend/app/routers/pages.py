"""Rotas que entregam as páginas HTML do frontend."""

from fastapi import APIRouter, Request
from fastapi.responses import FileResponse, HTMLResponse
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


# O service worker precisa ser servido da raiz do site: o endereço dele define até onde ele pode atuar.
@router.get("/service-worker.js")
async def service_worker() -> FileResponse:
    """O service worker do app instalável. Sem cache, para uma versão nova valer logo."""
    return FileResponse(
        FRONTEND_DIR / "static" / "service-worker.js",
        media_type="text/javascript",
        headers={"Cache-Control": "no-cache"},
    )


@router.get("/manifest.webmanifest")
async def web_manifest() -> FileResponse:
    """O manifesto que descreve o app para o navegador (nome, ícones, cores)."""
    return FileResponse(
        FRONTEND_DIR / "static" / "manifest.webmanifest", media_type="application/manifest+json"
    )


@router.get("/r/{code}", response_class=HTMLResponse)
async def room_page(code: RoomCode, request: Request) -> HTMLResponse:
    """Página de uma sala. O navegador entra na sala e mostra o conteúdo (tudo é descriptografado lá)."""
    settings = get_settings()
    page_data = {
        "app_name": settings.app_name,
        "room_code": code,
        # O JavaScript usa estes limites para avisar antes de enviar um arquivo grande demais.
        "max_file_bytes": settings.max_file_size_bytes,
        "max_room_bytes": settings.max_room_size_bytes,
        "max_text_bytes": settings.max_text_size_bytes,
        "max_clip_bytes": settings.max_clip_size_bytes,
        "max_code_clip_bytes": settings.max_code_clip_size_bytes,
    }
    return templates.TemplateResponse(request, "room.html", page_data)


@dev_router.get("/dev/crypto", response_class=HTMLResponse)
async def dev_crypto(request: Request) -> HTMLResponse:
    """Página para testar a criptografia do navegador."""
    page_data = {"app_name": get_settings().app_name}
    return templates.TemplateResponse(request, "dev_crypto.html", page_data)
