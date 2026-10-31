"""Autenticacao e consulta dos logs de acesso."""
from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import select

from Backend.db import session_scope
from Backend.db.auth import autenticar, listar_logs, registrar_log, usuario_publico
from Backend.db.models import Usuario
from Backend.runtime import _emit
from Backend.services.risk_alerts import FUNCOES_EXECUTIVAS, disparar_alerta_risco, forcar_alerta_login

router = APIRouter()


class LoginIn(BaseModel):
    email: str
    password: str


class LogoutIn(BaseModel):
    email: str


def _ip_cliente(request: Request) -> str:
    encaminhado = request.headers.get("x-forwarded-for", "")
    if encaminhado:
        return encaminhado.split(",")[0].strip()
    if request.client:
        return request.client.host
    return ""


def _alerta_risco_em_fundo(email: str) -> None:
    try:
        disparar_alerta_risco(
            email,
            forcar=False,
            simular=forcar_alerta_login(),
            origem="login",
        )
    except Exception as exc:  # noqa: BLE001
        _emit(f"LOGIN alerta risco em fundo falhou: {type(exc).__name__}: {exc}")


@router.post("/api/v1/auth/login")
def login(body: LoginIn, request: Request, background_tasks: BackgroundTasks) -> dict[str, object]:
    ip = _ip_cliente(request)
    _emit(
        f"LOGIN CHEGOU method={request.method} url={request.url} ip={ip} "
        f"email={body.email!r} senha=***len={len(body.password or '')} "
        f"headers={dict(request.headers)}"
    )
    with session_scope() as db:
        usuario, mensagem = autenticar(db, body.email, body.password, ip_origem=ip)
        publico = usuario_publico(usuario) if usuario is not None else None
    _emit(
        f"LOGIN VALIDACAO email={body.email!r} ok={usuario is not None} "
        f"mensagem={mensagem!r} role={(publico or {}).get('role')!r} "
        f"funcao={(publico or {}).get('funcao')!r}"
    )
    if usuario is None or publico is None:
        _emit(f"LOGIN REJEITADO 401 email={body.email!r} detalhe={mensagem!r}")
        raise HTTPException(status_code=401, detail=mensagem)
    if str(publico.get("funcao") or "") in FUNCOES_EXECUTIVAS or bool(publico.get("is_super_admin")):
        background_tasks.add_task(_alerta_risco_em_fundo, str(publico.get("email") or body.email))
    _emit(f"LOGIN OK 200 email={publico.get('email')!r} role={publico.get('role')!r}")
    return {"ok": True, "message": mensagem, "user": publico, "risk_alert": None}


@router.post("/api/v1/auth/logout")
def logout(body: LogoutIn, request: Request) -> dict[str, object]:
    email = body.email.strip().lower()
    with session_scope() as db:
        usuario = db.scalar(select(Usuario).where(Usuario.email == email))
        registrar_log(
            db,
            email=email,
            sucesso=True,
            mensagem="Logout efetuado",
            funcao=usuario.funcao if usuario is not None else None,
            ip_origem=_ip_cliente(request),
        )
    return {"ok": True, "message": "Logout efetuado"}


@router.get("/api/v1/auth/logs")
def logs_acesso(email: str, limite: int = 200) -> dict[str, object]:
    email_norm = email.strip().lower()
    with session_scope() as db:
        solicitante = db.scalar(select(Usuario).where(Usuario.email == email_norm))
        if solicitante is None or solicitante.funcao != "CEO" or not solicitante.ativo:
            raise HTTPException(status_code=403, detail="Apenas o CEO pode consultar os logs de acesso.")
        registros = listar_logs(db, limite)
        return {
            "ok": True,
            "logs": [
                {
                    "id": item.id,
                    "email_usuario": item.email_usuario,
                    "funcao": item.funcao,
                    "sucesso": item.sucesso,
                    "data_hora": item.data_hora.isoformat(sep=" ", timespec="seconds") if item.data_hora else None,
                    "ip_origem": item.ip_origem,
                    "mensagem": item.mensagem,
                }
                for item in registros
            ],
        }
