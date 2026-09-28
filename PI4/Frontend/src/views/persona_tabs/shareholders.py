"""Sub-abas da persona Acionistas."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from src.config import COR_ALERTA, COR_OK

from .common import _financeiro


def render_acionistas_retorno(df: pd.DataFrame, cena: str, ano_sel: str | int) -> None:
    _ = ano_sel
    dados = _financeiro(df, cena)
    fig = px.line(dados.melt("ano_num", value_vars=["ROIC", "ROE", "WACC"], var_name="Indicador", value_name="Valor"), x="ano_num", y="Valor", color="Indicador", markers=True, title="ROIC vs ROE vs WACC")
    fig.update_layout(yaxis_tickformat=".1%", xaxis_title="Ano")
    st.plotly_chart(fig, width="stretch", theme="streamlit")


def render_acionistas_eva(df: pd.DataFrame, cena: str, ano_sel: str | int) -> None:
    _ = ano_sel
    dados = _financeiro(df, cena)
    dados["ano_str"] = "Ano " + dados["ano_num"].astype(str)
    dados["EVA_limpo"] = dados["EVA"].fillna(0)
    dados["eva_positivo"] = dados["EVA_limpo"] >= 0
    fig = px.bar(dados, x="ano_str", y="EVA", color="eva_positivo", color_discrete_map={True: COR_OK, False: COR_ALERTA}, title="EVA ano a ano")
    fig.update_layout(showlegend=False, xaxis_title="Ano", yaxis_title="R$")
    st.plotly_chart(fig, width="stretch", theme="streamlit")


def render_acionistas_dividendos(df: pd.DataFrame, cena: str, ano_sel: str | int) -> None:
    _ = ano_sel
    dados = _financeiro(df, cena)
    comp = dados[["ano_num", "Dividendos", "Retido"]].melt("ano_num", var_name="Destino", value_name="Valor")
    fig = px.bar(comp, x="ano_num", y="Valor", color="Destino", title="Lucro líquido: dividendos vs reinvestimento")
    st.plotly_chart(fig, width="stretch", theme="streamlit")
    tabela = dados[["ano_num", "Lucro Líquido", "Dividendos", "Retido", "DY"]].copy()
    st.dataframe(tabela, width="stretch", hide_index=True)
