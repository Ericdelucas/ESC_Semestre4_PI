"""Hash de senha, seed, login e auditoria de acesso."""

from __future__ import annotations

import hashlib
import hmac
import os
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import LogAcesso, Usuario

ITERACOES = 120_000
FUNCAO_PARA_ROLE = {
    "CEO": "ceo",
    "CFO": "cfo",
    "Acionistas": "acionistas",
    "Poder Concedente": "concedente",
}
FUNCOES_VALIDAS = ("CEO", "CFO", "Acionistas", "Poder Concedente")
SUPER_ADMIN_EMAIL = "ericdelucass@gmail.com"
USUARIOS_PADRAO = (
    ("poderconcedente@gmail.com", "123", "Poder Concedente", False),
    ("acionistas@gmail.com", "123", "Acionistas", False),
    ("cfo@gmail.com", "123", "CFO", False),
    ("ceo@gmail.com", "123", "CEO", False),
    (SUPER_ADMIN_EMAIL, "123", "CEO", True),
)


def hash_senha(senha: str) -> str:
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", senha.encode("utf-8"), salt, ITERACOES)
    return f"{salt.hex()}${digest.hex()}"


def verificar_senha(senha: str, senha_hash: str) -> bool:
    try:
        salt_hex, digest_hex = senha_hash.split("$", 1)
        esperado = hashlib.pbkdf2_hmac(
            "sha256",
            senha.encode("utf-8"),
            bytes.fromhex(salt_hex),
            ITERACOES,
        )
    except (ValueError, TypeError):
        return False
    return hmac.compare_digest(esperado.hex(), digest_hex)


def registrar_log(
    db: Session,
    *,
    email: str,
    sucesso: bool,
    mensagem: str,
    funcao: str | None = None,
    ip_origem: str | None = None,
) -> None:
    db.add(
        LogAcesso(
            email_usuario=(email or "").strip().lower(),
            funcao=funcao,
            sucesso=sucesso,
            data_hora=datetime.utcnow(),
            ip_origem=ip_origem,
            mensagem=mensagem,
        )
    )


def eh_super_admin(usuario: Usuario | None) -> bool:
    if usuario is None or not usuario.ativo:
        return False
    return bool(usuario.is_super_admin) or usuario.email.strip().lower() == SUPER_ADMIN_EMAIL


def seed_usuarios(db: Session) -> None:
    for email, senha, funcao, root in USUARIOS_PADRAO:
        email_norm = email.strip().lower()
        existente = db.scalar(select(Usuario).where(Usuario.email == email_norm))
        if existente is not None:
            if root and not existente.is_super_admin:
                existente.is_super_admin = True
                existente.funcao = "CEO"
                existente.ativo = True
            continue
        db.add(
            Usuario(
                email=email_norm,
                senha_hash=hash_senha(senha),
                funcao=funcao,
                ativo=True,
                is_super_admin=root,
                criado_em=datetime.utcnow(),
            )
        )


def autenticar(
    db: Session,
    email: str,
    senha: str,
    ip_origem: str | None = None,
) -> tuple[Usuario | None, str]:
    email_norm = str(email or "").strip().lower()
    usuario = db.scalar(select(Usuario).where(Usuario.email == email_norm))
    if usuario is None:
        registrar_log(
            db,
            email=email_norm,
            sucesso=False,
            mensagem="E-mail nao encontrado",
            ip_origem=ip_origem,
        )
        return None, "E-mail ou senha incorretos."
    if not usuario.ativo:
        registrar_log(
            db,
            email=email_norm,
            sucesso=False,
            mensagem="Usuario inativo",
            funcao=usuario.funcao,
            ip_origem=ip_origem,
        )
        return None, "Usuario inativo."
    if not verificar_senha(senha, usuario.senha_hash):
        registrar_log(
            db,
            email=email_norm,
            sucesso=False,
            mensagem="Senha incorreta",
            funcao=usuario.funcao,
            ip_origem=ip_origem,
        )
        return None, "E-mail ou senha incorretos."
    registrar_log(
        db,
        email=email_norm,
        sucesso=True,
        mensagem="Login efetuado com sucesso",
        funcao=usuario.funcao,
        ip_origem=ip_origem,
    )
    return usuario, "Login efetuado com sucesso"


def usuario_publico(usuario: Usuario) -> dict[str, object]:
    return {
        "id": usuario.id,
        "email": usuario.email,
        "funcao": usuario.funcao,
        "role": FUNCAO_PARA_ROLE.get(usuario.funcao, usuario.funcao.lower()),
        "ativo": usuario.ativo,
        "is_super_admin": eh_super_admin(usuario),
    }


def listar_logs(db: Session, limite: int = 200) -> list[LogAcesso]:
    stmt = select(LogAcesso).order_by(LogAcesso.data_hora.desc(), LogAcesso.id.desc()).limit(max(1, min(limite, 1000)))
    return list(db.scalars(stmt))
