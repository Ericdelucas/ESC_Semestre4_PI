"""Filtros laterais, idioma e seletor de persona."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from src.config import CSV_PATH, PERSONAS
from src.config.glossary import help_text
from src.config.i18n import LANG_OPTIONS, get_lang, set_lang, t
from src.models.formatting import cena_rotulo, cena_sort_key


def render_language_selector() -> str:
    """Seletor no topo da sidebar; persiste em ``st.session_state['lang']``."""
    if "lang" not in st.session_state:
        st.session_state["lang"] = "pt"

    labels = list(LANG_OPTIONS.values())
    codes = list(LANG_OPTIONS.keys())
    atual = get_lang()
    idx = codes.index(atual) if atual in codes else 0

    with st.sidebar:
        escolha = st.selectbox(
            t("lang.label"),
            options=labels,
            index=idx,
            key="lang_select_label",
        )
        novo = codes[labels.index(escolha)]
        if novo != st.session_state.get("lang"):
            set_lang(novo)
            st.rerun()
    return get_lang()


def render_sidebar(df: pd.DataFrame, ind: pd.DataFrame, n_cenarios: int) -> tuple[str | int, str, list[int], list[str]]:
    with st.sidebar:
        st.header(t("sidebar.filters"))
        anos = sorted(int(a) for a in ind["ano_num"].dropna().unique().tolist())
        # Valor interno estável "__all__" — rótulo muda com o idioma sem perder o filtro
        ano_opts: list[str | int] = ["__all__", *anos]
        ano_choice = st.selectbox(
            t("sidebar.year"),
            options=ano_opts,
            index=0,
            format_func=lambda x: t("filter.all") if x == "__all__" else str(x),
            key="filtro_ano",
            help=help_text("sidebar_year"),
        )
        ano_sel: str | int = "Todos" if ano_choice == "__all__" else int(ano_choice)

        cenas = sorted(ind["CENA"].dropna().unique().tolist(), key=cena_sort_key)
        cena_sel = st.selectbox(
            t("sidebar.scenario"), options=cenas, format_func=cena_rotulo,
            key="filtro_cena", help=help_text("sidebar_scenario"),
        )

        st.markdown("---")
        st.markdown(
            f"**{t('sidebar.base')}:** `{Path(CSV_PATH).name}`  \n"
            f"**{t('sidebar.rows')}:** {len(df):,}  \n"
            f"**{t('sidebar.scenarios')}:** {n_cenarios:,}  \n"
            f"**{t('sidebar.years')}:** {ind['ano_num'].nunique()}"
        )
    return ano_sel, cena_sel, anos, cenas


def render_persona() -> str:
    lang = get_lang()
    labels = [t(f"persona.{p}") for p in PERSONAS]
    label_to_id = dict(zip(labels, PERSONAS, strict=True))
    legado = {"geral": "ceo", "concedente": "docente"}
    atual = st.session_state.get("persona_id", PERSONAS[0])
    if atual not in PERSONAS:
        st.session_state["persona_id"] = legado.get(str(atual), PERSONAS[0])
    if "persona_id" not in st.session_state:
        st.session_state["persona_id"] = PERSONAS[0]
    default_label = t(f"persona.{st.session_state['persona_id']}")
    escolha = st.segmented_control(
        t("persona.label"),
        options=labels,
        default=default_label if default_label in labels else labels[0],
        key=f"persona_visao_v2_{lang}",
        help=help_text("persona"),
    )
    role = label_to_id.get(escolha, PERSONAS[0])
    st.session_state["persona_id"] = role
    return role
