"""Gestao de usuarios exclusiva do Super Admin."""

from __future__ import annotations

import re
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select

from Backend.db import session_scope
from Backend.db.auth import FUNCOES_VALIDAS, SUPER_ADMIN_EMAIL, eh_super_admin, hash_senha, usuario_publico
from Backend.db.models import Usuario

router = APIRouter(prefix="/api/v1/users", tags=["users"])
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class UserCreateIn(BaseModel):
    email: str
    senha: str = Field(min_length=1)
    funcao: str


def _exigir_super_admin(email: str) -> Usuario:
    email_norm = (email or "").strip().lower()
    with session_scope() as db:
        solicitante = db.scalar(select(Usuario).where(Usuario.email == email_norm))
        if solicitante is None or not eh_super_admin(solicitante):
            raise HTTPException(status_code=403, detail="Apenas o Super Admin pode gerenciar usuarios.")
        return solicitante


@router.post("/create")
def criar_usuario(body: UserCreateIn, email: str = Query(..., description="E-mail do Super Admin autenticado")) -> dict[str, object]:
    _exigir_super_admin(email)
    novo_email = body.email.strip().lower()
    if not _EMAIL_RE.match(novo_email):
        raise HTTPException(status_code=400, detail="Informe um e-mail valido.")
    funcao = body.funcao.strip()
    if funcao not in FUNCOES_VALIDAS:
        raise HTTPException(status_code=400, detail=f"Funcao invalida. Use: {', '.join(FUNCOES_VALIDAS)}.")
    senha = body.senha.strip()
    if not senha:
        raise HTTPException(status_code=400, detail="Informe uma senha temporaria.")
    with session_scope() as db:
        existente = db.scalar(select(Usuario).where(Usuario.email == novo_email))
        if existente is not None:
            raise HTTPException(status_code=409, detail="Este e-mail ja esta cadastrado.")
        usuario = Usuario(
            email=novo_email,
            senha_hash=hash_senha(senha),
            funcao=funcao,
            ativo=True,
            is_super_admin=novo_email == SUPER_ADMIN_EMAIL,
            criado_em=datetime.utcnow(),
        )
        db.add(usuario)
        db.flush()
        publico = usuario_publico(usuario)
    return {"ok": True, "message": "Usuario cadastrado com sucesso.", "user": publico}


@router.get("/list")
def listar_usuarios(email: str = Query(..., description="E-mail do Super Admin autenticado")) -> dict[str, object]:
    _exigir_super_admin(email)
    with session_scope() as db:
        registros = list(db.scalars(select(Usuario).order_by(Usuario.id.asc())))
        usuarios = [
            {
                **usuario_publico(item),
                "criado_em": item.criado_em.isoformat(sep=" ", timespec="seconds") if item.criado_em else None,
            }
            for item in registros
        ]
    return {"ok": True, "users": usuarios}
