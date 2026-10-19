"""Rotas que entregam as páginas HTML do frontend."""

import posixpath
import re
from functools import lru_cache
from pathlib import PurePosixPath

from fastapi import APIRouter, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.templating import Jinja2Templates

from app.config import FRONTEND_DIR, get_settings
from app.dependencies import RoomCode

templates = Jinja2Templates(directory=FRONTEND_DIR / "templates")

STATIC_JS_DIR = FRONTEND_DIR / "static" / "js"
IMPORT_PATTERN = re.compile(r"""(?:from|import)\s*["'](\./[^"']+\.m?js)["']""")


@lru_cache
def modules_to_preload(entry_module: str) -> list[str]:
    """Todos os módulos JavaScript que uma página carrega (o dela e os que ele importa, e assim por diante).

    O navegador só descobre um módulo depois de baixar quem o importa: com 5 níveis, são 5 idas e vindas à
    rede em fila, o que no celular com internet móvel passa de um segundo. Avisar tudo de uma vez no HTML
    (`modulepreload`) faz o navegador baixar todos ao mesmo tempo.
    """
    found: list[str] = []
    pending = [PurePosixPath(entry_module)]
    while pending:
        module = pending.pop(0)
        module_name = str(module)
        if module_name in found:
            continue
        found.append(module_name)
        source = (STATIC_JS_DIR / module).read_text(encoding="utf-8")
        for relative_import in IMPORT_PATTERN.findall(source):
            imported = PurePosixPath(posixpath.normpath(str(module.parent / relative_import)))
            pending.append(imported)
    return found


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
        "preload_modules": modules_to_preload("home.js"),
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


@router.get("/sobre", response_class=HTMLResponse)
async def about(request: Request) -> HTMLResponse:
    """Página que explica o que o servidor guarda e como denunciar abuso."""
    settings = get_settings()
    page_data = {"app_name": settings.app_name, "contact_email": settings.contact_email}
    return templates.TemplateResponse(request, "about.html", page_data)


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
        "preload_modules": modules_to_preload("room.js"),
    }
    return templates.TemplateResponse(request, "room.html", page_data)


@dev_router.get("/dev/crypto", response_class=HTMLResponse)
async def dev_crypto(request: Request) -> HTMLResponse:
    """Página para testar a criptografia do navegador."""
    page_data = {"app_name": get_settings().app_name}
    return templates.TemplateResponse(request, "dev_crypto.html", page_data)
