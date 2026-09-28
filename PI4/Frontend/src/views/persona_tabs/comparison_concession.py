"""Comparacao da persona Poder Concedente."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.config import COR_VERMELHO
from src.models.formatting import cena_rotulo, fmt_rs

from .common import _balanco_fluxo, _conta, _dre
from .comparison_helpers import _fmt_x, _metric_base
from .styles import SERIES_STYLES


def _concedente_cmp(df: pd.DataFrame, cena: str) -> pd.DataFrame:
    dados = _dre(df, cena).merge(_balanco_fluxo(df, cena), on="ano_num", how="outer").sort_values("ano_num").fillna(0.0)
    dados["CAPEX"] = _conta(dados, "FLU - Investimentos").abs()
    dados["CAPEX Acumulado"] = dados["CAPEX"].cumsum()
    dados["Liquidez Geral"] = (_conta(dados, "BAL - Ativo Circulante").abs() + _conta(dados, "BAL - Realizável a Longo Prazo").abs()) / (
        _conta(dados, "BAL - Passivo Circulante").abs() + _conta(dados, "BAL - Exigível a Longo Prazo").abs()
    ).replace(0, pd.NA)
    dados["Base Final"] = _conta(dados, "BAL - Investimentos - Imobilizado").abs() + _conta(dados, "BAL - Investimentos - Intangível").abs()
    return dados


def _lg_referencia(dados: pd.DataFrame, ano_sel: str | int) -> float:
    if dados.empty:
        return float("nan")
    if ano_sel != "Todos":
        recorte = dados.loc[dados["ano_num"] == int(ano_sel)]
        return float(recorte["Liquidez Geral"].mean()) if not recorte.empty else float("nan")
    ultimo_ano = dados["ano_num"].max()
    return float(dados.loc[dados["ano_num"] == ultimo_ano, "Liquidez Geral"].mean())


def _base_final_ativos(dados: pd.DataFrame) -> float:
    if dados.empty:
        return float("nan")
    ultimo_ano = dados["ano_num"].max()
    final = dados.loc[dados["ano_num"] == ultimo_ano]
    base_bruta = float(final["Base Final"].sum())
    if abs(base_bruta) >= 1:
        return base_bruta
    ativo_total = float(_conta(final, "BAL - Total do Ativo").abs().sum())
    if abs(ativo_total) >= 1:
        return ativo_total
    return float(dados["Base Final"].abs().max())


def _render_cmp_concedente(df: pd.DataFrame, cenarios: list[tuple[str, str]], ano_sel: str | int) -> None:
    dados = {rotulo: _concedente_cmp(df, cena) for rotulo, cena in cenarios}
    metricas = {
        rotulo: {"capex": base["CAPEX"].sum(), "lg": base["Liquidez Geral"].mean(), "base_final": _base_final_ativos(base), "lg_ref": _lg_referencia(base, ano_sel)}
        for rotulo, base in dados.items()
    }
    comp = [rotulo for rotulo, _ in cenarios if rotulo != "A"]

    c1, c2, c3 = st.columns(3)
    with c1:
        _metric_base("CAPEX Acumulado Executado", metricas["A"]["capex"], [(r, metricas[r]["capex"]) for r in comp], fmt_rs)
    with c2:
        _metric_base("Liquidez Geral Média", metricas["A"]["lg"], [(r, metricas[r]["lg"]) for r in comp], _fmt_x)
    with c3:
        _metric_base("Base Final de Ativos Reversíveis", metricas["A"]["base_final"], [(r, metricas[r]["base_final"]) for r in comp], fmt_rs)

    fig = go.Figure()
    for rotulo, cena in cenarios:
        estilo = SERIES_STYLES[rotulo]
        base = dados[rotulo]
        fig.add_scatter(x=base["ano_num"], y=base["Liquidez Geral"], mode="lines+markers", name=f"Série {rotulo} · {cena_rotulo(cena)}", line={"color": estilo["color"], "dash": estilo["dash"]})
    fig.add_hline(y=1.0, line_dash="dash", line_color=COR_VERMELHO, annotation_text="Mínimo contratual 1,0x")
    fig.update_layout(title="Liquidez Geral: base vs estresse", xaxis_title="Ano", yaxis_title="Liquidez Geral (x)", hovermode="x unified")
    st.plotly_chart(fig, width="stretch", theme="streamlit")
    abaixo_limite = [f"Série {rotulo} ({_fmt_x(metricas[rotulo]['lg_ref'])})" for rotulo, _ in cenarios if pd.notna(metricas[rotulo]["lg_ref"]) and metricas[rotulo]["lg_ref"] < 1.0]
    if abaixo_limite:
        st.error("Risco de Descumprimento Contratual / Caducidade: " + ", ".join(abaixo_limite))
    else:
        st.success("Concessão em Conformidade Financeira (Liquidez ≥ 1,0x)")
