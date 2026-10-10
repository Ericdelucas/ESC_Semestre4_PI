"""Painel exclusivo do Super Admin para gestao de usuarios."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from src.config.i18n import t
from src.controllers.auth import EMAIL_KEY, SUPER_ADMIN_EMAIL, is_super_admin
from src.models.api_client import get_json, post_json

FUNCOES = ("CEO", "CFO", "Acionistas", "Poder Concedente")


def _admin_email() -> str:
    return str(st.session_state.get(EMAIL_KEY) or "").strip().lower()


def render_admin_usuarios() -> None:
    st.markdown(f"#### {t('admin.users.title')}")
    st.caption(t("admin.users.caption"))
    if not is_super_admin() or _admin_email() != SUPER_ADMIN_EMAIL:
        st.warning(t("admin.users.forbidden"))
        return

    with st.form("admin_create_user", clear_on_submit=False):
        email = st.text_input(t("admin.users.email"), placeholder="nome@empresa.com")
        senha = st.text_input(t("admin.users.password"), type="password")
        funcao = st.selectbox(t("admin.users.role"), options=list(FUNCOES))
        enviar = st.form_submit_button(t("admin.users.submit"), type="primary")
    if enviar:
        payload, status = post_json(
            "/api/v1/users/create",
            {"email": email.strip(), "senha": senha, "funcao": funcao},
            {"email": _admin_email()},
        )
        if status == 200 and payload.get("ok"):
            st.success(str(payload.get("message") or t("admin.users.created")))
        else:
            detalhe = payload.get("detail") or payload.get("message") or t("admin.users.error")
            st.error(str(detalhe))

    lista, status = get_json("/api/v1/users/list", {"email": _admin_email()})
    if status != 200 or not lista.get("ok"):
        st.error(str(lista.get("detail") or t("admin.users.list_error")))
        return
    usuarios = lista.get("users") if isinstance(lista.get("users"), list) else []
    if not usuarios:
        st.info(t("admin.users.empty"))
        return
    tabela = pd.DataFrame(usuarios)
    colunas = {
        "id": t("admin.users.col.id"),
        "email": t("admin.users.col.email"),
        "funcao": t("admin.users.col.role"),
        "ativo": t("admin.users.col.active"),
        "is_super_admin": t("admin.users.col.root"),
        "criado_em": t("admin.users.col.created"),
    }
    existentes = [c for c in colunas if c in tabela.columns]
    st.dataframe(tabela[existentes].rename(columns=colunas), use_container_width=True, hide_index=True)
