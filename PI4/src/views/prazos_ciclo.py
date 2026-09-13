"""Aba Prazos e ciclo."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from src.components.charts import ancorar_ano_temporal, titulo_filtro
from src.components.resilience import safe_render
from src.data.formatting import fmt_dias


def _grafico_prazos(foco: pd.DataFrame, cena_sel: str, ano_sel: str | int) -> None:
    fig = px.line(
        foco,
        x="ano_num",
        y=["PMR", "PME", "PMP", "Ciclo_Financeiro"],
        markers=True,
        labels={"ano_num": "Ano", "value": "Dias", "variable": "Prazo"},
        title=titulo_filtro("Trajetória dos prazos médios", cena_sel, ano_sel),
    )
    fig.update_layout(legend_title_text="", hovermode="x unified")
    fig = ancorar_ano_temporal(fig, foco, ["PMR", "PME", "PMP", "Ciclo_Financeiro"], ano_sel)
    st.plotly_chart(fig, width="stretch", theme="streamlit")


def render(foco: pd.DataFrame, k: pd.Series, cena_sel: str, ano_sel: str | int) -> None:
    st.markdown("#### Prazos médios (dias)")
    p1, p2, p3, p4 = st.columns(4)
    p1.metric("PMR — receber de clientes", fmt_dias(k["PMR"]))
    p2.metric("PME — giro de estoque", fmt_dias(k["PME"]))
    p3.metric("PMP — pagar fornecedores", fmt_dias(k["PMP"]))
    p4.metric("Ciclo financeiro", fmt_dias(k["Ciclo_Financeiro"]))
    safe_render("trajetória dos prazos médios", _grafico_prazos, foco, cena_sel, ano_sel)
    st.markdown(
        """
**Em linguagem simples**

- **PMR alto** → clientes demoram a pagar → mais caixa preso.
- **PMP alto** → fornecedores dão mais prazo → ajuda o caixa.
- **Ciclo financeiro** = quantos dias a empresa precisa “adiantar” do próprio bolso.
"""
    )
