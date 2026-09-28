"""Orquestrador do dashboard CTI."""

from __future__ import annotations

import streamlit as st

from chat_component import render_floating_chat
from src.controllers.bootstrap import carregar_estado, montar_contexto
from src.controllers.data_input import has_custom_data, render_data_input
from src.controllers.navigation import render_pagina
from src.controllers.page_setup import configure_page
from src.controllers.sidebar import render_language_selector, render_persona, render_sidebar
from src.models.analytics import montar_indicadores


def main() -> None:
    configure_page()
    render_language_selector()
    estado = carregar_estado()
    if estado is None:
        st.stop()
    df, ind, ranking = estado
    df = render_data_input(df)
    if has_custom_data():
        ind, ranking = montar_indicadores(df)

    ano_sel, cena_sel, anos, cenas = render_sidebar(df, ind, int(ranking["CENA"].nunique()))
    persona = render_persona()
    ctx = montar_contexto(
        df, ind, ranking, ano_sel=ano_sel, cena_sel=cena_sel, anos=anos, cenas=cenas, persona=persona
    )
    render_pagina(ctx)
    render_floating_chat()


main()
