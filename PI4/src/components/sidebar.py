"""Filtros laterais e seletor de persona."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from src.config import CSV_PATH, PERSONAS


def render_sidebar(df: pd.DataFrame, ind: pd.DataFrame, n_cenarios: int) -> tuple[str | int, str, list[int], list[str]]:
    with st.sidebar:
        st.header("Filtros")
        anos = sorted(int(a) for a in ind["ano_num"].dropna().unique().tolist())
        ano_sel = st.selectbox("Ano do horizonte", options=["Todos", *anos], index=0)
        cenas = sorted(ind["CENA"].dropna().unique().tolist())
        cena_sel = st.selectbox("Cenário em foco", options=cenas, index=0)
        st.markdown("---")
        st.markdown(
            f"**Base:** `{Path(CSV_PATH).name}`  \n"
            f"**Linhas brutas:** {len(df):,}  \n"
            f"**Cenários:** {n_cenarios:,}  \n"
            f"**Anos:** {ind['ano_num'].nunique()}"
        )
    return ano_sel, cena_sel, anos, cenas


def render_persona() -> str:
    persona = st.segmented_control(
        "Visão do stakeholder",
        options=PERSONAS,
        default="Visão Geral",
        key="persona_visao",
    )
    return persona or "Visão Geral"
