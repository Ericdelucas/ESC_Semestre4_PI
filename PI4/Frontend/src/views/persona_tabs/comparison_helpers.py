"""Helpers visuais do comparador de cenarios."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from src.config import COR_OK, COR_VERMELHO
from src.models.formatting import cena_rotulo

from .common import _safe_div


def _selecionar_cenarios(cenas: list[str], persona: str) -> list[tuple[str, str]]:
    col_a, col_b, col_c = st.columns(3)
    default_b = 1 if len(cenas) > 1 else 0
    opcoes_c = [None, *cenas]
    default_c = 3 if len(cenas) > 2 else 0
    with col_a:
        cena_a = st.selectbox("Cenário A (Base):", options=cenas, index=0, format_func=cena_rotulo, key=f"cmp_abc_a_{persona}")
    with col_b:
        cena_b = st.selectbox("Cenário B (Comparativo 1):", options=cenas, index=default_b, format_func=cena_rotulo, key=f"cmp_abc_b_{persona}")
    with col_c:
        cena_c = st.selectbox(
            "Cenário C (Comparativo 2 / Opcional):",
            options=opcoes_c,
            index=default_c,
            format_func=lambda cena: "Nenhum" if cena is None else cena_rotulo(cena),
            key=f"cmp_abc_c_{persona}",
        )
    selecionados = [("A", cena_a), ("B", cena_b)]
    if cena_c is not None:
        selecionados.append(("C", cena_c))
    return selecionados


def _delta(valor_a: float, valor_b: float, fmt, *, maior_melhor: bool = True) -> tuple[str, str]:
    if pd.isna(valor_a) or pd.isna(valor_b):
        return "—", "off"
    dif = valor_b - valor_a
    pct = _safe_div(dif, abs(valor_a))
    pct_txt = f" ({pct * 100:+.1f}%)" if pd.notna(pct) else ""
    favoravel = dif >= 0 if maior_melhor else dif <= 0
    cor = "normal" if (dif >= 0) == favoravel else "inverse"
    return f"{fmt(dif)}{pct_txt}", cor


def _cor_delta(valor_a: float, valor_b: float, *, maior_melhor: bool = True) -> str:
    if pd.isna(valor_a) or pd.isna(valor_b):
        return "#8A8F98"
    dif = valor_b - valor_a
    favoravel = dif >= 0 if maior_melhor else dif <= 0
    return COR_OK if favoravel else COR_VERMELHO


def _metric_base(label: str, valor_a: float, comparativos: list[tuple[str, float]], fmt, *, maior_melhor: bool = True, help_text: str | None = None, extra: str | None = None) -> None:
    st.metric(label, fmt(valor_a), help=help_text)
    if extra:
        st.caption(extra)
    for rotulo, valor in comparativos:
        delta, _ = _delta(valor_a, valor, fmt, maior_melhor=maior_melhor)
        cor = _cor_delta(valor_a, valor, maior_melhor=maior_melhor)
        st.markdown(f"<div style='font-size:0.82rem;font-weight:700;color:{cor};'>Δ {rotulo}: {delta}</div>", unsafe_allow_html=True)


def _fmt_x(valor: float) -> str:
    return "—" if pd.isna(valor) else f"{valor:.2f}x"
