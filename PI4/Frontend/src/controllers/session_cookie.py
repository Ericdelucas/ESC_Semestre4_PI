"""Sessao persistente em cookie do navegador (TTL de inatividade)."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import streamlit as st

COOKIE_NAME = "cti_auth"
TTL_SECONDS = 300
_BOOTSTRAP_KEY = "_cti_cookie_bootstrapped"


def _secret() -> bytes:
    env = (os.environ.get("CTI_SESSION_SECRET") or "").strip()
    if env:
        return env.encode("utf-8")
    cache_dir = Path(__file__).resolve().parents[3] / "Backend" / "cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    secret_path = cache_dir / ".session_secret"
    if secret_path.is_file():
        bruto = secret_path.read_text(encoding="utf-8").strip()
        if bruto:
            return bruto.encode("utf-8")
    gerado = os.urandom(32).hex()
    secret_path.write_text(gerado, encoding="utf-8")
    return gerado.encode("utf-8")


def encode_session(email: str, role: str, funcao: str) -> str:
    payload = {
        "email": email.strip().lower(),
        "role": role,
        "funcao": funcao,
        "iat": int(time.time()),
    }
    corpo = base64.urlsafe_b64encode(json.dumps(payload, separators=(",", ":")).encode("utf-8")).decode("ascii")
    assinatura = hmac.new(_secret(), corpo.encode("ascii"), hashlib.sha256).hexdigest()
    return f"{corpo}.{assinatura}"


def decode_session(token: str | None) -> dict[str, Any] | None:
    if not token or "." not in token:
        return None
    corpo, assinatura = token.rsplit(".", 1)
    esperado = hmac.new(_secret(), corpo.encode("ascii"), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(assinatura, esperado):
        return None
    try:
        payload = json.loads(base64.urlsafe_b64decode(corpo.encode("ascii")))
    except (ValueError, json.JSONDecodeError):
        return None
    if not isinstance(payload, dict):
        return None
    emitido = int(payload.get("iat") or 0)
    if emitido <= 0 or (time.time() - emitido) > TTL_SECONDS:
        return None
    email = str(payload.get("email") or "").strip().lower()
    role = str(payload.get("role") or "").strip()
    if not email or not role:
        return None
    payload["email"] = email
    payload["role"] = role
    payload["funcao"] = str(payload.get("funcao") or "")
    return payload


def cookie_manager():
    existente = st.session_state.get("_cti_cm_obj")
    if existente is not None:
        return existente
    import extra_streamlit_components as stx

    gerente = stx.CookieManager(key="cti_cookie_manager")
    st.session_state["_cti_cm_obj"] = gerente
    return gerente


def bootstrap_cookies() -> Any:
    """Monta o CookieManager e faz um rerun para hidratar os cookies do navegador."""
    gerente = cookie_manager()
    _ = gerente.get_all()
    if not st.session_state.get(_BOOTSTRAP_KEY):
        st.session_state[_BOOTSTRAP_KEY] = True
        st.rerun()
    return gerente


def read_session_cookie() -> dict[str, Any] | None:
    gerente = cookie_manager()
    return decode_session(gerente.get(COOKIE_NAME))


def write_session_cookie(email: str, role: str, funcao: str, *, force: bool = False) -> None:
    gerente = cookie_manager()
    atual = decode_session(gerente.get(COOKIE_NAME))
    if (
        not force
        and atual
        and atual.get("email") == email
        and atual.get("role") == role
        and (time.time() - int(atual.get("iat") or 0)) < 20
    ):
        return
    expira = datetime.now(timezone.utc) + timedelta(seconds=TTL_SECONDS)
    gerente.set(
        COOKIE_NAME,
        encode_session(email, role, funcao),
        expires_at=expira,
        max_age=TTL_SECONDS,
        same_site="lax",
        key="cti_cookie_set",
    )


def delete_session_cookie() -> None:
    gerente = cookie_manager()
    try:
        gerente.delete(COOKIE_NAME, key="cti_cookie_delete")
    except Exception:
        try:
            gerente.set(
                COOKIE_NAME,
                "",
                expires_at=datetime.now(timezone.utc) - timedelta(days=1),
                key="cti_cookie_expire",
            )
        except Exception:
            pass
