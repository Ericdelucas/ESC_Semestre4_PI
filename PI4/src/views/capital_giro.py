"""Aba Capital de giro."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from src.components.charts import ancorar_ano_temporal, titulo_filtro
from src.components.resilience import safe_render
from src.config import COR, COR_ALERTA, COR_SUAVE
from src.data.formatting import fmt_rs


def _grafico_evolucao(foco: pd.DataFrame, cena_sel: str, ano_sel: str | int) -> None:
    fig_ncg = px.line(
        foco,
        x="ano_num",
        y=["NCG", "Saldo_Tesouraria"],
        markers=True,
        labels={"ano_num": "Ano", "value": "R$", "variable": "Indicador"},
        color_discrete_map={"NCG": COR, "Saldo_Tesouraria": COR_SUAVE},
        title=titulo_filtro("Evolução Temporal", cena_sel, ano_sel),
    )
    fig_ncg.update_layout(legend_title_text="", hovermode="x unified")
    fig_ncg = ancorar_ano_temporal(fig_ncg, foco, ["NCG", "Saldo_Tesouraria"], ano_sel)
    st.plotly_chart(fig_ncg, width="stretch", theme="streamlit")


def _grafico_composicao(foco_ano: pd.DataFrame, cena_sel: str, ano_sel: str | int) -> None:
    decomp = foco_ano[["ACO", "PCO", "NCG"]].mean()
    decomp_df = pd.DataFrame(
        {
            "Componente": [
                "Ativo circulante operacional (receber + estoques + créditos)",
                "Passivo circulante operacional (fornecedores + encargos + tributos)",
                "NCG (= ACO − PCO)",
            ],
            "Valor": [decomp["ACO"], decomp["PCO"], decomp["NCG"]],
        }
    )
    fig_bar = px.bar(
        decomp_df,
        x="Componente",
        y="Valor",
        text=[fmt_rs(v) for v in decomp_df["Valor"]],
        color="Componente",
        color_discrete_sequence=[COR_SUAVE, COR_ALERTA, COR],
        title=titulo_filtro("Composição da NCG", cena_sel, ano_sel),
    )
    fig_bar.update_layout(showlegend=False, xaxis_title="", yaxis_title="R$")
    fig_bar.update_traces(textposition="outside")
    st.plotly_chart(fig_bar, width="stretch", theme="streamlit")


def render(foco: pd.DataFrame, foco_ano: pd.DataFrame, cena_sel: str, ano_sel: str | int) -> None:
    st.markdown("#### Evolução no tempo (cenário selecionado)")
    safe_render("gráfico de evolução NCG × Tesouraria", _grafico_evolucao, foco, cena_sel, ano_sel)
    st.markdown("#### De onde vem a NCG")
    safe_render("composição da NCG", _grafico_composicao, foco_ano, cena_sel, ano_sel)
