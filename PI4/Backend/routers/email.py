"""Endpoints de teste SMTP e varredura de risco."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select

from Backend.db import session_scope
from Backend.db.auth import eh_super_admin
from Backend.db.models import Usuario
from Backend.services.email_service import SMTP_NAO_CONFIGURADO, enviar_alerta_email, html_teste_smtp, smtp_configurado, validar_email
from Backend.services.risk_alerts import FUNCOES_EXECUTIVAS, disparar_alerta_risco, forcar_alerta_login, varrer_riscos

router = APIRouter(prefix="/api/v1/email", tags=["email"])


class EmailTesteIn(BaseModel):
    destinatario: str


class VarreduraIn(BaseModel):
    enviar: bool = True
    simular: bool = False


def _usuario_ativo(email: str) -> Usuario:
    email_norm = (email or "").strip().lower()
    with session_scope() as db:
        usuario = db.scalar(select(Usuario).where(Usuario.email == email_norm))
        if usuario is None or not usuario.ativo:
            raise HTTPException(status_code=403, detail="Usuario nao autorizado.")
        return usuario


def _exigir_executivo(email: str) -> Usuario:
    usuario = _usuario_ativo(email)
    if usuario.funcao not in FUNCOES_EXECUTIVAS and not eh_super_admin(usuario):
        raise HTTPException(status_code=403, detail="Apenas CEO/CFO podem acionar alertas de risco.")
    return usuario


@router.post("/testar")
def testar_email(body: EmailTesteIn, email: str = Query(..., description="E-mail do usuario autenticado")) -> dict[str, object]:
    usuario = _usuario_ativo(email)
    if usuario.funcao not in FUNCOES_EXECUTIVAS and not eh_super_admin(usuario):
        raise HTTPException(status_code=403, detail="Apenas o perfil executivo pode testar o envio de e-mails.")
    try:
        destino = validar_email(body.destinatario)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    resultado = enviar_alerta_email(
        destino,
        "Grupo ESC - Teste de Conectividade SMTP",
        html_teste_smtp(),
    )
    return {
        "ok": bool(resultado.get("success")),
        "success": bool(resultado.get("success")),
        "message": resultado.get("message"),
        "detail": resultado.get("detail"),
        "phase": resultado.get("phase"),
        "server": resultado.get("server"),
        "port": resultado.get("port"),
        "mode": resultado.get("mode"),
        "exception": resultado.get("exception"),
        "code": "smtp_not_configured" if resultado.get("message") == "SMTP_NOT_CONFIGURED" else ("sent" if resultado.get("success") else str(resultado.get("message") or "smtp_error")),
        "destinatario": destino,
    }


@router.get("/status")
def status_email() -> dict[str, object]:
    return {
        "ok": True,
        "smtp_configured": smtp_configurado(),
        "force_alert_on_login": forcar_alerta_login(),
        "message": None if smtp_configurado() else SMTP_NAO_CONFIGURADO,
    }


@router.get("/riscos")
def consultar_riscos(email: str = Query(..., description="E-mail do usuario autenticado")) -> dict[str, object]:
    _exigir_executivo(email)
    return {"ok": True, **varrer_riscos()}


@router.post("/varrer-risco")
def varrer_e_alertar(body: VarreduraIn, email: str = Query(..., description="E-mail do usuario autenticado")) -> dict[str, object]:
    usuario = _exigir_executivo(email)
    if body.enviar:
        resultado = disparar_alerta_risco(
            usuario.email,
            forcar=False,
            simular=body.simular,
            origem="manual",
        )
    else:
        resultado = varrer_riscos()
        resultado["sent"] = False
        resultado["recipients"] = []
        resultado["email_error"] = None
    return {"ok": True, **resultado}
