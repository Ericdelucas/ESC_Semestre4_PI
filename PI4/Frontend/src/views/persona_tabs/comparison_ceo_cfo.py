"""Comparacoes das personas CEO e CFO."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.config import COR_VERMELHO
from src.models.formatting import cena_rotulo, fmt_dias, fmt_rs

from .common import _break_even_df, _dre, _safe_div
from .comparison_helpers import _metric_base
from .styles import SERIES_STYLES


def _ceo_cmp(df: pd.DataFrame, cena: str) -> pd.DataFrame:
    dre = _dre(df, cena)
    be = _break_even_df(df, cena)
    return dre.merge(be[["ano_num", "Break-Even"]], on="ano_num", how="left")


def _render_cmp_ceo(df: pd.DataFrame, cenarios: list[tuple[str, str]]) -> None:
    dados = {rotulo: _ceo_cmp(df, cena) for rotulo, cena in cenarios}
    metricas = {
        rotulo: {
            "receita": base["Receita Líquida"].sum(),
            "ebitda": base["EBITDA"].sum(),
            "margem": _safe_div(base["EBITDA"].sum(), base["Receita Líquida"].sum()),
            "break_even": base["Break-Even"].mean(),
        }
        for rotulo, base in dados.items()
    }
    comp = [rotulo for rotulo, _ in cenarios if rotulo != "A"]

    c1, c2, c3 = st.columns(3)
    with c1:
        _metric_base("Receita Líquida Acumulada", metricas["A"]["receita"], [(r, metricas[r]["receita"]) for r in comp], fmt_rs)
    with c2:
        margem_a = metricas["A"]["margem"]
        if pd.isna(margem_a):
            margem_a = 0.0
        extra = f"Margem média A: {margem_a * 100:.1f}%"
        _metric_base("EBITDA Acumulado", metricas["A"]["ebitda"], [(r, metricas[r]["ebitda"]) for r in comp], fmt_rs, extra=extra)
    with c3:
        _metric_base("Break-Even Médio", metricas["A"]["break_even"], [(r, metricas[r]["break_even"]) for r in comp], fmt_rs, maior_melhor=False)

    fig = go.Figure()
    for rotulo, cena in cenarios:
        estilo = SERIES_STYLES[rotulo]
        base = dados[rotulo]
        nome = f"Série {rotulo} · {cena_rotulo(cena)}"
        fig.add_scatter(x=base["ano_num"], y=base["Receita Líquida"], mode="lines+markers", name=f"{nome} · Receita", line={"color": estilo["color"], "dash": estilo["dash"]})
        fig.add_scatter(x=base["ano_num"], y=base["EBITDA"], mode="lines+markers", name=f"{nome} · EBITDA", line={"color": estilo["color"], "dash": estilo["dash"], "width": 2})
    fig.update_layout(title="Receita Líquida e EBITDA: comparação de cenários", xaxis_title="Ano", yaxis_title="R$", hovermode="x unified")
    st.plotly_chart(fig, width="stretch", theme="streamlit")


def _render_cmp_cfo(ind: pd.DataFrame, cenarios: list[tuple[str, str]]) -> None:
    dados = {rotulo: ind[ind["CENA"] == cena].sort_values("ano_num") for rotulo, cena in cenarios}
    metricas = {
        rotulo: {"ncg": base["NCG"].mean(), "tesouraria": base["Saldo_Tesouraria"].min(), "ciclo": base["Ciclo_Financeiro"].mean()}
        for rotulo, base in dados.items()
    }
    comp = [rotulo for rotulo, _ in cenarios if rotulo != "A"]

    c1, c2, c3 = st.columns(3)
    with c1:
        _metric_base("NCG Média", metricas["A"]["ncg"], [(r, metricas[r]["ncg"]) for r in comp], fmt_rs, maior_melhor=False)
    with c2:
        _metric_base("Menor Saldo de Tesouraria", metricas["A"]["tesouraria"], [(r, metricas[r]["tesouraria"]) for r in comp], fmt_rs)
    with c3:
        _metric_base("Ciclo Financeiro Médio", metricas["A"]["ciclo"], [(r, metricas[r]["ciclo"]) for r in comp], fmt_dias, maior_melhor=False)

    fig = go.Figure()
    for rotulo, cena in cenarios:
        estilo = SERIES_STYLES[rotulo]
        base = dados[rotulo]
        fig.add_scatter(x=base["ano_num"], y=base["Saldo_Tesouraria"], mode="lines", fill="tozeroy", fillcolor=estilo["fill"], name=f"Série {rotulo} · {cena_rotulo(cena)}", line={"color": estilo["color"], "dash": estilo["dash"]})
    fig.add_hline(y=0, line_dash="dash", line_color=COR_VERMELHO, annotation_text="Zero")
    fig.update_layout(title="Teste de estresse de tesouraria", xaxis_title="Ano", yaxis_title="R$", hovermode="x unified")
    st.plotly_chart(fig, width="stretch", theme="streamlit")
