"""Menu suspenso de tres pontinhos com acoes operacionais do dashboard."""

from __future__ import annotations

import streamlit as st

from src.config.i18n import t
from src.controllers.auth import EMAIL_ALERTA_FLAG, EMAIL_KEY, current_role, is_super_admin
from src.models.api_client import get_json, post_json

RISK_SCAN_KEY = "risk_scan"
EMAIL_DIAG_KEY = "ops_email_diag"
TOAST_SMTP = "⚠️ SMTP não configurado no arquivo Backend/.env"


def _email_logado() -> str:
    return str(st.session_state.get(EMAIL_KEY) or "").strip().lower()


def _pode_alertas() -> bool:
    return current_role() in {"ceo", "cfo"} or is_super_admin()


def guardar_varredura(payload: dict[str, object] | None) -> None:
    if isinstance(payload, dict):
        st.session_state[RISK_SCAN_KEY] = payload


def varredura_atual() -> dict[str, object]:
    dados = st.session_state.get(RISK_SCAN_KEY)
    return dados if isinstance(dados, dict) else {}


def toast_smtp() -> None:
    st.toast(TOAST_SMTP, icon="⚠️")


def _eh_smtp_ausente(payload: dict[str, object]) -> bool:
    codigo = str(payload.get("code") or payload.get("message") or "")
    detalhe = str(payload.get("detail") or payload.get("email_error") or "")
    return codigo in {"smtp_not_configured", "SMTP_NOT_CONFIGURED"} or "SMTP_NOT_CONFIGURED" in detalhe


def _texto_diagnostico(payload: dict[str, object], status: int, fallback: str) -> str:
    if status == 404:
        return t("ops.email.not_found")
    partes = [
        str(payload.get("detail") or payload.get("email_error") or payload.get("message") or fallback),
    ]
    fase = payload.get("phase")
    if fase:
        partes.append(f"Fase: {fase}")
    servidor = payload.get("server")
    porta = payload.get("port")
    modo = payload.get("mode")
    if servidor or porta or modo:
        partes.append(f"Transporte: {servidor or '?'}:{porta or '?'} ({modo or '?'})")
    if payload.get("exception"):
        partes.append(f"Exceção: {payload.get('exception')}")
    return "\n\n".join(partes)


def _toast_resposta_email(payload: dict[str, object], status: int, sucesso: str, falha: str) -> None:
    if _eh_smtp_ausente(payload):
        toast_smtp()
        st.session_state[EMAIL_DIAG_KEY] = {"ok": False, "text": TOAST_SMTP}
        return
    if status == 200 and (payload.get("ok") or payload.get("success")):
        texto = str(payload.get("detail") or payload.get("message") or sucesso)
        st.session_state[EMAIL_DIAG_KEY] = {"ok": True, "text": texto}
        st.toast(texto, icon="✅")
        return
    texto = _texto_diagnostico(payload, status, falha)
    st.session_state[EMAIL_DIAG_KEY] = {"ok": False, "text": texto}
    st.toast(texto.split("\n", 1)[0], icon="⚠️")


def _render_diagnostico() -> None:
    dados = st.session_state.get(EMAIL_DIAG_KEY)
    if not isinstance(dados, dict) or not dados.get("text"):
        return
    if dados.get("ok"):
        st.success(str(dados["text"]))
        return
    st.error(str(dados["text"]))


def garantir_varredura_silenciosa() -> None:
    """Nao dispara e-mail nem aviso. So marca a sessao para nao repetir o login."""
    st.session_state[EMAIL_ALERTA_FLAG] = True


def render_ops_menu() -> None:
    with st.container(key="cti_ops_menu"):
        with st.popover("⋮", help=t("ops.menu.help")):
            st.caption(t("ops.menu.title"))
            if _pode_alertas():
                destino = st.text_input(
                    t("ops.email.dest"),
                    value=_email_logado(),
                    key="ops_email_dest",
                )
                if st.button(t("ops.email.send"), key="ops_email_send", use_container_width=True):
                    payload, status = post_json(
                        "/api/v1/email/testar",
                        {"destinatario": destino.strip()},
                        {"email": _email_logado()},
                        timeout=35,
                    )
                    _toast_resposta_email(payload, status, t("ops.email.ok"), t("ops.email.fail"))
                if st.button(t("ops.risk.scan"), key="ops_risk_scan", use_container_width=True):
                    payload, status = post_json(
                        "/api/v1/email/varrer-risco",
                        {"enviar": True, "simular": False},
                        {"email": _email_logado()},
                        timeout=45,
                    )
                    if status == 200 and payload.get("ok"):
                        guardar_varredura(payload)
                    if status == 200 and payload.get("skipped"):
                        st.toast("Alerta consolidado ja enviado. Novo disparo bloqueado pelo debounce.", icon="⚠️")
                    elif status == 200 and payload.get("ok") and not payload.get("critical"):
                        st.toast(t("ops.risk.clear"), icon="✅")
                    else:
                        _toast_resposta_email(payload, status, t("ops.risk.sent"), t("ops.risk.fail"))
                if st.button(t("ops.risk.simulate"), key="ops_risk_simulate", use_container_width=True):
                    payload, status = post_json(
                        "/api/v1/email/varrer-risco",
                        {"enviar": True, "simular": True},
                        {"email": _email_logado()},
                        timeout=45,
                    )
                    if status == 200 and payload.get("ok"):
                        guardar_varredura(payload)
                    _toast_resposta_email(payload, status, t("ops.risk.simulated"), t("ops.risk.fail"))
                _render_diagnostico()
                st.divider()
            if st.button(t("ops.health"), key="ops_health", use_container_width=True):
                payload, status = get_json("/api/v1/health")
                if status == 200 and payload.get("status") in {"online", "degraded"}:
                    st.toast(t("ops.health.ok", status=str(payload.get("status"))), icon="✅")
                else:
                    st.toast(str(payload.get("detail") or t("ops.health.fail")), icon="⚠️")
            if st.button(t("ops.cache"), key="ops_cache", use_container_width=True):
                st.cache_data.clear()
                st.cache_resource.clear()
                st.session_state.pop("cti_custom_indicator_cache", None)
                st.toast(t("ops.cache.ok"), icon="✅")
                st.rerun()
