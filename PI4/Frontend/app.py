"""Orquestrador do dashboard CTI."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

PI4_ROOT = Path(__file__).resolve().parents[1]
if str(PI4_ROOT) not in sys.path:
    sys.path.insert(0, str(PI4_ROOT))

from Backend.metrics import montar_indicadores
from src.controllers.auth import (
    flush_login_email_toast,
    is_authenticated,
    refresh_session_cookie,
    render_login,
    render_logout_button,
    restore_persistent_session,
)
from src.controllers.bootstrap import carregar_estado, montar_contexto
from src.controllers.data_input import has_custom_data, render_data_input
from src.controllers.modals import ensure_modal_state, is_relatorio_open
from src.controllers.navigation import render_pagina
from src.controllers.page_setup import configure_page
from src.controllers.sidebar import render_language_selector, render_persona, render_sidebar
from src.views.ai_assistant.panel import render_floating_chat


def montar_indicadores_customizados(df):
    """Evita recalcular indicadores de bases customizadas em todo rerun."""
    cache = st.session_state.setdefault("cti_custom_indicator_cache", {})
    signature = (
        st.session_state.get("cti_active_dataset_name"),
        bool(st.session_state.get("cti_default_dataset_modified")),
        id(df),
        len(df),
    )
    if cache.get("signature") != signature:
        cache["signature"] = signature
        cache["value"] = montar_indicadores(df)
    return cache["value"]


def main() -> None:
    configure_page()
    restore_persistent_session()
    ensure_modal_state()
    render_language_selector()
    if not is_authenticated():
        render_login()
        st.stop()
    refresh_session_cookie()
    flush_login_email_toast()
    render_logout_button()
    estado = carregar_estado()
    if estado is None:
        st.stop()
    df, ind, ranking = estado
    df = render_data_input(df)
    if has_custom_data():
        if df is None or df.empty or "CENA" not in df.columns:
            st.error(
                "A coluna CENA não foi encontrada no ficheiro enviado. "
                "No formato largo use ID_Cenario ou Nome_Cenario; no formato longo use CENA."
            )
        else:
            try:
                ind, ranking = montar_indicadores_customizados(df)
            except Exception as exc:  # noqa: BLE001
                st.error(
                    f"Não foi possível calcular os indicadores da base enviada: {type(exc).__name__}: {exc}. "
                    "A barra lateral permanece disponível para restaurar a base original."
                )
                if "CENA" not in getattr(ranking, "columns", []):
                    ranking = pd.DataFrame({"CENA": df["CENA"].dropna().unique()})
                if "CENA" not in getattr(ind, "columns", []):
                    ind = ranking.copy()

    n_cenarios = int(ranking["CENA"].nunique()) if "CENA" in getattr(ranking, "columns", []) else 0
    ano_sel, cena_sel, anos, cenas = render_sidebar(df, ind, n_cenarios)
    persona = render_persona()
    ctx = montar_contexto(
        df, ind, ranking, ano_sel=ano_sel, cena_sel=cena_sel, anos=anos, cenas=cenas, persona=persona
    )
    render_pagina(ctx)
    if not is_relatorio_open():
        render_floating_chat(ctx)


main()
