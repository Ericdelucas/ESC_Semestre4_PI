"""Login e hierarquia de acesso (RBAC) do dashboard CTI via API."""

from __future__ import annotations

import streamlit as st

from src.config.i18n import get_lang, t
from src.controllers.session_cookie import (
    COOKIE_NAME,
    bootstrap_cookies,
    cookie_manager,
    delete_session_cookie,
    read_session_cookie,
    write_session_cookie,
)
from src.models.api_client import get_json, post_json

AUTH_KEY = "authenticated"
ROLE_KEY = "user_role"
EMAIL_KEY = "user_email"
FUNCAO_KEY = "user_funcao"
EMAIL_ALERTA_FLAG = "email_alerta_verificado"
EMAIL_TOAST_KEY = "_email_login_toast"
SUPER_ADMIN_EMAIL = "ericdelucass@gmail.com"

ROLE_PERSONAS: dict[str, tuple[str, ...]] = {
    "concedente": ("concedente",),
    "acionistas": ("acionistas",),
    "cfo": ("cfo", "acionistas", "concedente"),
    "ceo": ("ceo", "cfo", "acionistas", "concedente"),
}

_LOGIN_CSS = """
<style>
div[class*="st-key-cti_login_card"] {
  max-width: 28rem;
  margin: 4rem auto 0 auto;
  padding: 1.6rem 1.5rem 1.3rem 1.5rem;
  border: 1px solid rgba(31, 78, 69, 0.28);
  border-radius: 14px;
  background: var(--secondary-background-color);
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.12);
}
div[class*="st-key-cti_login_card"] h1 {
  font-size: 1.55rem !important;
  margin-bottom: 0.2rem !important;
}
</style>
"""


def ensure_auth_state() -> None:
    st.session_state.setdefault(AUTH_KEY, False)
    st.session_state.setdefault(ROLE_KEY, None)
    st.session_state.setdefault(EMAIL_KEY, None)
    st.session_state.setdefault(FUNCAO_KEY, None)
    st.session_state.setdefault(EMAIL_ALERTA_FLAG, False)


def is_authenticated() -> bool:
    ensure_auth_state()
    return bool(st.session_state.get(AUTH_KEY))


def flush_login_email_toast() -> None:
    """Mostra o toast do login uma unica vez, sem bloco fixo na tela."""
    kind = st.session_state.pop(EMAIL_TOAST_KEY, None)
    if kind == "smtp":
        st.toast("⚠️ SMTP não configurado no arquivo Backend/.env", icon="⚠️")
    elif kind == "sent":
        st.toast(t("ops.risk.sent"), icon="⚠️")


def _aplicar_usuario(email: str, role: str, funcao: str) -> None:
    st.session_state[AUTH_KEY] = True
    st.session_state[ROLE_KEY] = role
    st.session_state[EMAIL_KEY] = email
    st.session_state[FUNCAO_KEY] = funcao
    if st.session_state.get("persona_id") not in ROLE_PERSONAS.get(role, ()):
        st.session_state["persona_id"] = allowed_personas(role)[0] if role in ROLE_PERSONAS else None
    st.session_state.pop("pending_persona_id", None)


def restore_persistent_session() -> bool:
    """Le o cookie antes do login; restaura a sessao se o TTL de 5 min ainda valer."""
    bootstrap_cookies()
    ensure_auth_state()
    payload = read_session_cookie()
    if payload is None:
        if cookie_manager().get(COOKIE_NAME):
            delete_session_cookie()
        if st.session_state.get(AUTH_KEY) and not st.session_state.get(EMAIL_KEY):
            st.session_state[AUTH_KEY] = False
        return False
    role = str(payload.get("role") or "")
    if role not in ROLE_PERSONAS:
        delete_session_cookie()
        return False
    email = str(payload.get("email") or "")
    funcao = str(payload.get("funcao") or "")
    _aplicar_usuario(email, role, funcao)
    write_session_cookie(email, role, funcao)
    st.session_state[EMAIL_ALERTA_FLAG] = True
    return True


def refresh_session_cookie() -> None:
    """Renova o TTL de 5 minutos a cada interacao autenticada (inatividade)."""
    if not is_authenticated():
        return
    email = str(st.session_state.get(EMAIL_KEY) or "")
    role = str(st.session_state.get(ROLE_KEY) or "")
    funcao = str(st.session_state.get(FUNCAO_KEY) or "")
    if email and role in ROLE_PERSONAS:
        write_session_cookie(email, role, funcao)


def current_role() -> str | None:
    ensure_auth_state()
    role = st.session_state.get(ROLE_KEY)
    return str(role) if role else None


def allowed_personas(role: str | None = None) -> list[str]:
    alvo = role or current_role()
    return list(ROLE_PERSONAS.get(str(alvo), ()))


def can_access_persona(persona: str, role: str | None = None) -> bool:
    return persona in allowed_personas(role)


def is_super_admin() -> bool:
    ensure_auth_state()
    email = str(st.session_state.get(EMAIL_KEY) or "").strip().lower()
    return email == SUPER_ADMIN_EMAIL


def _detalhe_erro(payload: dict[str, object]) -> str:
    detalhe = payload.get("detail", payload.get("message", t("login.error")))
    if isinstance(detalhe, list) and detalhe:
        primeiro = detalhe[0]
        if isinstance(primeiro, dict):
            return str(primeiro.get("msg", t("login.error")))
        return str(primeiro)
    return str(detalhe or t("login.error"))


def authenticate(email: str, password: str) -> tuple[bool, str]:
    payload, status = post_json("/api/v1/auth/login", {"email": email, "password": password})
    if status == 200 and payload.get("ok"):
        user = payload.get("user") if isinstance(payload.get("user"), dict) else {}
        role = str(user.get("role") or "")
        if role not in ROLE_PERSONAS:
            return False, t("login.error")
        email_norm = str(user.get("email") or email).strip().lower()
        funcao = str(user.get("funcao") or "")
        _aplicar_usuario(email_norm, role, funcao)
        write_session_cookie(email_norm, role, funcao, force=True)
        risco = payload.get("risk_alert") if isinstance(payload.get("risk_alert"), dict) else None
        if risco is not None:
            st.session_state["risk_scan"] = risco
        if not st.session_state.get(EMAIL_ALERTA_FLAG):
            erro = str((risco or {}).get("email_error") or (risco or {}).get("message") or "")
            if risco and (erro in {"SMTP_NOT_CONFIGURED"} or "SMTP_NOT_CONFIGURED" in erro):
                st.session_state[EMAIL_TOAST_KEY] = "smtp"
            elif risco and risco.get("sent"):
                st.session_state[EMAIL_TOAST_KEY] = "sent"
        st.session_state[EMAIL_ALERTA_FLAG] = True
        return True, str(payload.get("message") or "")
    if status == 503:
        return False, t("login.backend_offline")
    return False, _detalhe_erro(payload)


def logout() -> None:
    email = str(st.session_state.get(EMAIL_KEY) or "").strip()
    delete_session_cookie()
    if email:
        post_json("/api/v1/auth/logout", {"email": email})
    lang = get_lang()
    for chave in list(st.session_state.keys()):
        del st.session_state[chave]
    st.session_state["lang"] = lang
    st.session_state["language"] = lang
    st.session_state[AUTH_KEY] = False
    st.session_state[ROLE_KEY] = None
    st.session_state[EMAIL_KEY] = None
    st.session_state[FUNCAO_KEY] = None


def fetch_access_logs(limite: int = 200) -> tuple[list[dict[str, object]], str | None]:
    email = str(st.session_state.get(EMAIL_KEY) or "").strip()
    payload, status = get_json("/api/v1/auth/logs", {"email": email, "limite": limite})
    if status == 200 and payload.get("ok"):
        logs = payload.get("logs")
        return list(logs) if isinstance(logs, list) else [], None
    if status == 503:
        return [], t("login.backend_offline")
    return [], _detalhe_erro(payload)


def render_logout_button() -> None:
    with st.sidebar:
        papel = current_role() or ""
        email = st.session_state.get(EMAIL_KEY) or ""
        st.caption(f"{t('login.signed_in')}: **{t(f'persona.{papel}')}**")
        if email:
            st.caption(email)
        if is_super_admin():
            st.caption(t("admin.users.badge"))
        if st.button(t("login.logout"), key="cti_logout_btn", use_container_width=True):
            logout()
            st.rerun()


def render_login() -> None:
    ensure_auth_state()
    st.markdown(_LOGIN_CSS, unsafe_allow_html=True)
    with st.container(key="cti_login_card"):
        st.title(t("login.title"))
        st.caption(t("login.subtitle"))
        with st.form("cti_login_form", clear_on_submit=False):
            email = st.text_input(t("login.email"), placeholder="ceo@gmail.com")
            password = st.text_input(t("login.password"), type="password")
            enviado = st.form_submit_button(t("login.submit"), type="primary", use_container_width=True)
        if enviado:
            ok, mensagem = authenticate(email, password)
            if ok:
                st.rerun()
            st.error(mensagem or t("login.error"))
