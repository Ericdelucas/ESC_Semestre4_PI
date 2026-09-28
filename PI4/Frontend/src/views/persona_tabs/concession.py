"""Sub-abas da persona Poder Concedente."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.config import COR, COR_SUAVE, COR_VERMELHO

from .common import _balanco_fluxo, _conta, _dre


def _dre_balanco(df: pd.DataFrame, cena: str) -> pd.DataFrame:
    return _dre(df, cena).merge(_balanco_fluxo(df, cena), on="ano_num", how="outer").sort_values("ano_num").fillna(0.0)


def render_concedente_capex(df: pd.DataFrame, cena: str, ano_sel: str | int) -> None:
    _ = ano_sel
    dados = _dre_balanco(df, cena)
    dados["CAPEX"] = _conta(dados, "FLU - Investimentos").abs()
    dados["CAPEX Acumulado"] = dados["CAPEX"].cumsum()
    dados["CAPEX / Receita Líquida"] = dados["CAPEX"] / dados["Receita Líquida"].replace(0, pd.NA)
    fig = go.Figure()
    fig.add_bar(x=dados["ano_num"], y=dados["CAPEX"], name="CAPEX anual", marker_color=COR_SUAVE)
    fig.add_scatter(x=dados["ano_num"], y=dados["CAPEX Acumulado"], name="CAPEX acumulado", mode="lines+markers", line={"color": COR})
    fig.update_layout(title="Plano de CAPEX", xaxis_title="Ano", yaxis_title="R$")
    st.plotly_chart(fig, width="stretch", theme="streamlit")


def render_concedente_solvencia(df: pd.DataFrame, cena: str, ano_sel: str | int) -> None:
    _ = ano_sel
    dados = _dre_balanco(df, cena)
    lg = (_conta(dados, "BAL - Ativo Circulante").abs() + _conta(dados, "BAL - Realizável a Longo Prazo").abs()) / (
        _conta(dados, "BAL - Passivo Circulante").abs() + _conta(dados, "BAL - Exigível a Longo Prazo").abs()
    ).replace(0, pd.NA)
    dados["Liquidez Geral"] = lg
    dados["Endividamento"] = _conta(dados, "BAL - Total do Passivo").abs() / _conta(dados, "BAL - Total do Ativo").abs().replace(0, pd.NA)
    dados["Cobertura de Juros"] = dados["EBIT"] / _conta(dados, "DRE - Despesas Financeiras").abs().replace(0, pd.NA)
    fig = px.line(dados, x="ano_num", y="Liquidez Geral", markers=True, title="Liquidez Geral com limite de risco")
    fig.add_hline(y=1.0, line_dash="dash", line_color=COR_VERMELHO, annotation_text="Mínimo 1,0x")
    st.plotly_chart(fig, width="stretch", theme="streamlit")
    st.dataframe(dados[["ano_num", "Liquidez Geral", "Endividamento", "Cobertura de Juros"]], width="stretch", hide_index=True)


def render_concedente_ativos(df: pd.DataFrame, cena: str, ano_sel: str | int) -> None:
    _ = ano_sel
    dados = _balanco_fluxo(df, cena)
    bruto = _conta(dados, "BAL - Investimentos - Imobilizado").abs() + _conta(dados, "BAL - Investimentos - Intangível").abs()
    dep = _conta(dados, "BAL - Depreciação Acumulada").abs() + _conta(dados, "BAL - Amortização Acumulada").abs()
    dados["Base Líquida"] = bruto - dep
    dados["Depreciação/Amortização Acumulada"] = dep
    comp = dados[["ano_num", "Base Líquida", "Depreciação/Amortização Acumulada"]].melt("ano_num", var_name="Componente", value_name="Valor")
    fig = px.area(comp, x="ano_num", y="Valor", color="Componente", title="Ativos reversíveis líquidos vs depreciação acumulada")
    st.plotly_chart(fig, width="stretch", theme="streamlit")
