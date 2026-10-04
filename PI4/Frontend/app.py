"""Orquestrador do dashboard CTI."""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

PI4_ROOT = Path(__file__).resolve().parents[1]
if str(PI4_ROOT) not in sys.path:
    sys.path.insert(0, str(PI4_ROOT))

from Backend.metrics import montar_indicadores
from src.controllers.bootstrap import carregar_estado, montar_contexto
from src.controllers.data_input import has_custom_data, render_data_input
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
    render_language_selector()
    estado = carregar_estado()
    if estado is None:
        st.stop()
    df, ind, ranking = estado
    df = render_data_input(df)
    if has_custom_data():
        ind, ranking = montar_indicadores_customizados(df)

    ano_sel, cena_sel, anos, cenas = render_sidebar(df, ind, int(ranking["CENA"].nunique()))
    persona = render_persona()
    ctx = montar_contexto(
        df, ind, ranking, ano_sel=ano_sel, cena_sel=cena_sel, anos=anos, cenas=cenas, persona=persona
    )
    render_pagina(ctx)
    render_floating_chat(ctx)


main()
