"""Aba Prazos e ciclo."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from src.components.charts import ancorar_ano_temporal, serie_temporal_plotavel, titulo_filtro
from src.components.resilience import resilient_view, safe_render
from src.config.i18n import t
from src.data.formatting import fmt_dias


def _grafico_prazos(foco: pd.DataFrame, cena_sel: str, ano_sel: str | int) -> None:
    y_cols = ["PMR", "PME", "PMP", "Ciclo_Financeiro"]
    plot_df = serie_temporal_plotavel(foco, y_cols)
    fig = px.line(
        plot_df,
        x="ano_num",
        y=y_cols,
        markers=True,
        labels={
            "ano_num": t("chart.year"),
            "value": t("prazos.days"),
            "variable": t("prazos.term"),
        },
        title=titulo_filtro(t("prazos.chart"), cena_sel, ano_sel),
    )
    fig.update_layout(legend_title_text="", hovermode="x unified")
    fig = ancorar_ano_temporal(fig, plot_df, y_cols, ano_sel)
    st.plotly_chart(fig, width="stretch", theme="streamlit")


@resilient_view("aba Prazos e ciclo")
def render(foco: pd.DataFrame, k: pd.Series, cena_sel: str, ano_sel: str | int) -> None:
    st.markdown(t("prazos.title"))
    p1, p2, p3, p4 = st.columns(4)
    p1.metric(t("prazos.pmr"), fmt_dias(k["PMR"]))
    p2.metric(t("prazos.pme"), fmt_dias(k["PME"]))
    p3.metric(t("prazos.pmp"), fmt_dias(k["PMP"]))
    p4.metric(t("prazos.cycle"), fmt_dias(k["Ciclo_Financeiro"]))
    safe_render("trajetória dos prazos médios", _grafico_prazos, foco, cena_sel, ano_sel)
    st.markdown(t("prazos.help"))
