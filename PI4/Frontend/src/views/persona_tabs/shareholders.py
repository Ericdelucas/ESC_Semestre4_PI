"""Sub-abas da persona Acionistas."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from src.config import COR_ALERTA, COR_OK
from src.config.i18n import t
from src.models.formatting.tables import render_table

from .common import _financeiro


def render_acionistas_retorno(df: pd.DataFrame, cena: str, ano_sel: str | int) -> None:
    _ = ano_sel
    dados = _financeiro(df, cena)
    fig = px.line(dados.melt("ano_num", value_vars=["ROIC", "ROE", "WACC"], var_name="Indicador", value_name="Valor"), x="ano_num", y="Valor", color="Indicador", markers=True, title=t("sh.chart.roic"))
    fig.update_layout(yaxis_tickformat=".1%", xaxis_title=t("chart.year"))
    st.plotly_chart(fig, width="stretch", theme="streamlit")


def render_acionistas_eva(df: pd.DataFrame, cena: str, ano_sel: str | int) -> None:
    _ = ano_sel
    dados = _financeiro(df, cena)
    dados["ano_str"] = dados["ano_num"].map(lambda n: t("filter.year_n", n=n))
    dados["EVA_limpo"] = dados["EVA"].fillna(0)
    dados["eva_positivo"] = dados["EVA_limpo"] >= 0
    fig = px.bar(dados, x="ano_str", y="EVA", color="eva_positivo", color_discrete_map={True: COR_OK, False: COR_ALERTA}, title=t("sh.chart.eva"))
    fig.update_layout(showlegend=False, xaxis_title=t("chart.year"), yaxis_title="R$")
    st.plotly_chart(fig, width="stretch", theme="streamlit")


def render_acionistas_dividendos(df: pd.DataFrame, cena: str, ano_sel: str | int) -> None:
    _ = ano_sel
    dados = _financeiro(df, cena)
    destinos = dados[["ano_num", "Dividendos", "Retido"]].rename(columns={"Dividendos": t("sh.div"), "Retido": t("sh.retained")})
    comp = destinos.melt("ano_num", var_name="Destino", value_name="Valor")
    fig = px.bar(comp, x="ano_num", y="Valor", color="Destino", title=t("sh.chart.div"))
    st.plotly_chart(fig, width="stretch", theme="streamlit")
    tabela = dados[["ano_num", "Lucro Líquido", "Dividendos", "Retido", "DY"]].rename(
        columns={
            "ano_num": t("chart.year"),
            "Lucro Líquido": t("ceo.wf.net"),
            "Dividendos": t("sh.div"),
            "Retido": t("sh.retained"),
        }
    )
    render_table(tabela)
