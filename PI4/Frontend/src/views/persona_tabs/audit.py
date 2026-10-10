"""Aba CEO de auditoria de logs de acesso."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from src.config.i18n import t
from src.controllers.auth import current_role, fetch_access_logs
from src.models.formatting.tables import render_table


def render_ceo_auditoria() -> None:
    st.markdown(f"#### {t('audit.logs.title')}")
    st.caption(t("audit.logs.caption"))
    if current_role() != "ceo":
        st.warning(t("audit.logs.forbidden"))
        return
    logs, erro = fetch_access_logs()
    if erro:
        st.error(erro)
        return
    if not logs:
        st.info(t("audit.logs.empty"))
        return
    tabela = pd.DataFrame(logs)
    colunas = {
        "id": t("audit.logs.col.id"),
        "data_hora": t("audit.logs.col.when"),
        "email_usuario": t("audit.logs.col.email"),
        "funcao": t("audit.logs.col.role"),
        "sucesso": t("audit.logs.col.ok"),
        "ip_origem": t("audit.logs.col.ip"),
        "mensagem": t("audit.logs.col.message"),
    }
    existentes = [c for c in colunas if c in tabela.columns]
    visao = tabela[existentes].rename(columns=colunas)
    render_table(visao)
