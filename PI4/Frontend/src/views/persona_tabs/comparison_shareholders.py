"""Comparacao da persona Acionistas."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from src.config.i18n import t
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
        _metric_base(t("cmp.sh.roic"), metricas["A"]["roic"], [(r, metricas[r]["roic"]) for r in comp], fmt_pct)
    with c2:
        _metric_base(t("cmp.sh.eva_acc"), metricas["A"]["eva"], [(r, metricas[r]["eva"]) for r in comp], fmt_rs)
    with c3:
        _metric_base(t("cmp.sh.div"), metricas["A"]["dividendos"], [(r, metricas[r]["dividendos"]) for r in comp], fmt_rs)

    scene_col = t("cmp.sh.scenario")
    eva = pd.concat([pd.DataFrame({"ano_num": base["ano_num"], scene_col: t("cmp.series", rotulo=rotulo), "EVA": base["EVA"]}) for rotulo, base in dados.items()])
    eva["ano_num"] = pd.to_numeric(eva["ano_num"], errors="coerce")
    eva = eva.dropna(subset=["ano_num"]).sort_values(["ano_num", scene_col])
    eva["ano_num"] = eva["ano_num"].astype(int)
    eva["Ano_Rotulo"] = eva["ano_num"].map(lambda n: t("filter.year_n", n=n))
    ordem_anos = [t("filter.year_n", n=ano) for ano in sorted(eva["ano_num"].unique())]
    fig = px.bar(
        eva,
        x="Ano_Rotulo",
        y="EVA",
        color=scene_col,
        barmode="group",
        category_orders={"Ano_Rotulo": ordem_anos},
        title=t("cmp.sh.eva_title"),
    )
    fig.update_layout(xaxis_title=t("chart.year"), yaxis_title=t("cmp.sh.eva_axis"))
    st.plotly_chart(fig, width="stretch", theme="streamlit")

    risco = pd.DataFrame([{scene_col: t("cmp.series", rotulo=rotulo), t("cmp.sh.risk"): metricas[rotulo]["risco"], t("cmp.sh.roic"): metricas[rotulo]["roic"]} for rotulo, _ in cenarios])
    fig2 = px.scatter(risco, x=t("cmp.sh.risk"), y=t("cmp.sh.roic"), text=scene_col, title=t("cmp.sh.risk_title"))
    fig2.update_traces(textposition="top center", marker={"size": 16})
    fig2.update_layout(yaxis_tickformat=".1%")
    st.plotly_chart(fig2, width="stretch", theme="streamlit")
