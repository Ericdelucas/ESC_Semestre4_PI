"""Rotas de saude e versao, com os paths e contratos originais."""
from __future__ import annotations

from fastapi import APIRouter
from sqlalchemy import func, select

from Backend.db import session_scope
from Backend.db.models import Usuario
from Backend.runtime import _emit
from Backend.services.rag_indexer import status_rag
from Backend.services.email_service import smtp_configurado
from Backend.services.risk_alerts import forcar_alerta_login

router = APIRouter()
APP_VERSION = "1.0.0"
_HEALTH = {"status": "online", "message": "API CTI Backend Ativa"}


def _status_banco() -> dict[str, object]:
    try:
        with session_scope() as db:
            total = int(db.scalar(select(func.count()).select_from(Usuario)) or 0)
        return {"ok": True, "usuarios": total}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}


@router.api_route("/", methods=["GET", "HEAD"])
@router.api_route("/api/health", methods=["GET", "HEAD"])
def health_root() -> dict[str, str]:
    return dict(_HEALTH)


@router.get("/json/version")
def json_version() -> dict[str, str]:
    return {"version": APP_VERSION, "status": "ok"}


@router.api_route("/api/v1/health", methods=["GET", "HEAD"])
def health_v1() -> dict[str, object]:
    _emit("handler /api/v1/health")
    banco = _status_banco()
    rag = status_rag()
    online = bool(banco.get("ok")) and bool(rag.get("ok"))
    return {
        "status": "online" if online else "degraded",
        "message": "API CTI Backend Ativa",
        "version": APP_VERSION,
        "database": banco,
        "rag": {
            "ok": rag.get("ok"),
            "count": rag.get("count"),
            "globs": rag.get("globs"),
            "directory": rag.get("directory"),
        },
        "email": {
            "smtp_configured": smtp_configurado(),
            "force_alert_on_login": forcar_alerta_login(),
            "routes": [
                "POST /api/v1/email/testar",
                "GET /api/v1/email/status",
                "GET /api/v1/email/riscos",
                "POST /api/v1/email/varrer-risco",
            ],
        },
    }
