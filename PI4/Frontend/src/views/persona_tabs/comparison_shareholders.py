"""Comparacao da persona Acionistas."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from src.models.formatting import fmt_pct, fmt_rs

from .common import _financeiro
from .comparison_helpers import _metric_base


def _render_cmp_acionistas(df: pd.DataFrame, cenarios: list[tuple[str, str]]) -> None:
    dados = {rotulo: _financeiro(df, cena) for rotulo, cena in cenarios}
    metricas = {
        rotulo: {"roic": base["ROIC"].mean(), "eva": base["EVA"].sum(), "dividendos": base["Dividendos"].sum(), "risco": base["Lucro Líquido"].std()}
        for rotulo, base in dados.items()
    }
    comp = [rotulo for rotulo, _ in cenarios if rotulo != "A"]

    c1, c2, c3 = st.columns(3)
    with c1:
        _metric_base("ROIC Médio", metricas["A"]["roic"], [(r, metricas[r]["roic"]) for r in comp], fmt_pct)
    with c2:
        _metric_base("EVA Acumulado", metricas["A"]["eva"], [(r, metricas[r]["eva"]) for r in comp], fmt_rs)
    with c3:
        _metric_base("Dividendos Distribuídos", metricas["A"]["dividendos"], [(r, metricas[r]["dividendos"]) for r in comp], fmt_rs)

    eva = pd.concat([pd.DataFrame({"ano_num": base["ano_num"], "Cenário": f"Série {rotulo}", "EVA": base["EVA"]}) for rotulo, base in dados.items()])
    eva["ano_num"] = pd.to_numeric(eva["ano_num"], errors="coerce")
    eva = eva.dropna(subset=["ano_num"]).sort_values(["ano_num", "Cenário"])
    eva["ano_num"] = eva["ano_num"].astype(int)
    eva["Ano_Rotulo"] = "Ano " + eva["ano_num"].astype(str)
    ordem_anos = [f"Ano {ano}" for ano in sorted(eva["ano_num"].unique())]
    fig = px.bar(
        eva,
        x="Ano_Rotulo",
        y="EVA",
        color="Cenário",
        barmode="group",
        category_orders={"Ano_Rotulo": ordem_anos},
        title="EVA ano a ano: cenários selecionados",
    )
    fig.update_layout(xaxis_title="Ano", yaxis_title="EVA (R$)")
    st.plotly_chart(fig, width="stretch", theme="streamlit")

    risco = pd.DataFrame([{"Cenário": f"Série {rotulo}", "Risco": metricas[rotulo]["risco"], "ROIC Médio": metricas[rotulo]["roic"]} for rotulo, _ in cenarios])
    fig2 = px.scatter(risco, x="Risco", y="ROIC Médio", text="Cenário", title="Risco x Retorno")
    fig2.update_traces(textposition="top center", marker={"size": 16})
    fig2.update_layout(yaxis_tickformat=".1%")
    st.plotly_chart(fig2, width="stretch", theme="streamlit")
