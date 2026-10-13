"""Ciclo de vida, CORS e logs da API CTI."""
from __future__ import annotations

import logging
import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from Backend.diag import log_ambiente
from Backend.db import init_db, seed_usuarios

logging.basicConfig(
    level=logging.INFO,
    stream=sys.stdout,
    format="%(asctime)s [fastapi] %(levelname)s %(message)s",
    force=True,
)
_log = logging.getLogger("cti.fastapi")


def _emit(message: str) -> None:
    print(f"[fastapi] {message}", flush=True)
    _log.info(message)


_LOCAL_ORIGINS = [
    "http://localhost:8501",
    "http://127.0.0.1:8501",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "http://localhost:8081",
    "http://127.0.0.1:8081",
]


def _cors_origins() -> list[str]:
    extras = [item.strip() for item in os.environ.get("CORS_ORIGINS", "").split(",") if item.strip()]
    normalized: list[str] = []
    frontend_url = (os.environ.get("FRONTEND_URL") or "").strip()
    for origin in extras + [frontend_url] + _LOCAL_ORIGINS:
        if origin and "://" not in origin:
            origin = f"https://{origin}"
        origin = origin.rstrip("/")
        if origin and origin not in normalized:
            normalized.append(origin)
    render_url = (os.environ.get("RENDER_EXTERNAL_URL") or "").rstrip("/")
    if render_url and render_url not in normalized:
        normalized.append(render_url)
    return normalized


def _cors_origin_regex() -> str:
    return os.environ.get(
        "CORS_ORIGIN_REGEX",
        r"https?://(localhost|127\.0\.0\.1)(:\d+)?|https://.*\.onrender\.com",
    )


def _log_bind_info() -> None:
    public_port = os.environ.get("PORT", "<nao definido>")
    _emit(f"processo API a iniciar. cwd={Path.cwd()}")
    _emit(f"PORT publica (Render)={public_port}")
    _emit("Web Service Backend: uvicorn main:app --host 0.0.0.0 --port $PORT (cwd=Backend)")
    log_ambiente("fastapi")


def _log_rotas(application: FastAPI) -> None:
    rotas = []
    for route in application.routes:
        methods = sorted(getattr(route, "methods", None) or [])
        path = getattr(route, "path", str(route))
        rotas.append(f"{','.join(methods) or '-'} {path}")
    _emit(f"{len(rotas)} rotas registadas:")
    for item in rotas:
        _emit(f"  rota: {item}")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    _log_bind_info()
    _emit("lifespan: init_db()")
    try:
        init_db()
    except Exception as exc:  # noqa: BLE001
        _emit(f"aviso init_db ({type(exc).__name__}: {exc}) — API continua")
    _emit("lifespan: seed_usuarios()")
    try:
        seed_usuarios()
    except Exception as exc:  # noqa: BLE001
        _emit(f"aviso seed_usuarios ({type(exc).__name__}: {exc}) — API continua")
    _log_rotas(_app)
    try:
        from Backend.services.email_service import smtp_configurado

        smtp_configurado()
        user = (os.environ.get("SMTP_USER") or "").strip()
        senha = (os.environ.get("SMTP_PASSWORD") or "").strip()
        _emit(
            f"SMTP user_definido={bool(user)} senha_len={len(senha.replace(' ', ''))} "
            f"configurado={smtp_configurado()}"
        )
    except Exception as exc:  # noqa: BLE001
        _emit(f"aviso SMTP no arranque ({type(exc).__name__}: {exc})")
    _emit("lifespan: API pronta a aceitar pedidos")
    yield
    _emit("lifespan: a encerrar a API")


async def _log_pedidos(request: Request, call_next):
    _emit(f"pedido IN {request.method} {request.url} client={request.client}")
    try:
        response = await call_next(request)
    except Exception as exc:  # noqa: BLE001
        _emit(f"pedido ERRO {request.method} {request.url} {type(exc).__name__}: {exc}")
        raise
    _emit(f"pedido OUT {request.method} {request.url} status={response.status_code}")
    return response


def configure_application(app: FastAPI) -> None:
    """Regista os middlewares existentes sem alterar a politica CORS."""
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_cors_origins(),
        allow_origin_regex=_cors_origin_regex(),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.middleware("http")(_log_pedidos)
