"""Roteador do comparador de cenarios por persona."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from src.config.i18n import t

from .comparison_ceo_cfo import _render_cmp_ceo, _render_cmp_cfo
from .comparison_concession import _render_cmp_concedente
from .comparison_helpers import _selecionar_cenarios
from .comparison_shareholders import _render_cmp_acionistas


def render_comparar_cenarios(df: pd.DataFrame, ind: pd.DataFrame, cenas: list[str], persona: str, ano_sel: str | int = "Todos") -> None:
    st.markdown(f"#### {t('cmp.ab_title')}")
    cenarios = _selecionar_cenarios(cenas, persona)
    ids = [cena for _, cena in cenarios]
    if len(set(ids)) != len(ids):
        st.info(t("cmp.need_diff"))
        return
    if persona == "ceo":
        _render_cmp_ceo(df, cenarios)
    elif persona == "cfo":
        _render_cmp_cfo(ind, cenarios)
    elif persona == "acionistas":
        _render_cmp_acionistas(df, cenarios)
    else:
        _render_cmp_concedente(df, cenarios, ano_sel)
