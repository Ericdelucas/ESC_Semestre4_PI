"""Sub-abas da persona Poder Concedente."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.config import COR, COR_SUAVE, COR_VERMELHO
from src.config.i18n import t
from src.models.formatting.tables import render_table

from .common import _balanco_fluxo, _dre
from Backend.metrics.dashboard_metrics import concession_metrics


def _dre_balanco(df: pd.DataFrame, cena: str) -> pd.DataFrame:
    dados = _dre(df, cena).merge(_balanco_fluxo(df, cena), on="ano_num", how="outer").sort_values("ano_num").fillna(0.0)
    return concession_metrics(dados)


def render_concedente_capex(df: pd.DataFrame, cena: str, ano_sel: str | int) -> None:
    _ = ano_sel
    dados = _dre_balanco(df, cena)
    fig = go.Figure()
    fig.add_bar(x=dados["ano_num"], y=dados["CAPEX"], name=t("pc.capex_annual"), marker_color=COR_SUAVE)
    fig.add_scatter(x=dados["ano_num"], y=dados["CAPEX Acumulado"], name=t("pc.capex_cumul"), mode="lines+markers", line={"color": COR})
    fig.update_layout(title=t("pc.chart.capex"), xaxis_title=t("chart.year"), yaxis_title="R$")
    st.plotly_chart(fig, width="stretch", theme="streamlit")


def render_concedente_solvencia(df: pd.DataFrame, cena: str, ano_sel: str | int) -> None:
    _ = ano_sel
    dados = _dre_balanco(df, cena)
    fig = px.line(dados, x="ano_num", y="Liquidez Geral", markers=True, title=t("pc.chart.liq"))
    fig.add_hline(y=1.0, line_dash="dash", line_color=COR_VERMELHO, annotation_text=t("pc.hline.min"))
    st.plotly_chart(fig, width="stretch", theme="streamlit")
    render_table(
        dados[["ano_num", "Liquidez Geral", "Endividamento", "Cobertura de Juros"]].rename(
            columns={
                "ano_num": t("chart.year"),
                "Liquidez Geral": t("pc.liq"),
                "Endividamento": t("pc.debt"),
                "Cobertura de Juros": t("pc.coverage"),
            }
        )
    )


def render_concedente_ativos(df: pd.DataFrame, cena: str, ano_sel: str | int) -> None:
    _ = ano_sel
    dados = _dre_balanco(df, cena)
    dados[t("pc.net_base")] = dados['Base Líquida de Ativos']
    dados[t("pc.dep_acc")] = dados['Depreciação Acumulada']
    comp = dados[["ano_num", t("pc.net_base"), t("pc.dep_acc")]].melt("ano_num", var_name="Componente", value_name="Valor")
    fig = px.area(comp, x="ano_num", y="Valor", color="Componente", title=t("pc.chart.assets"))
    st.plotly_chart(fig, width="stretch", theme="streamlit")
