"""Aba Prazos e ciclo."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from src.controllers.charts import ancorar_ano_temporal, serie_temporal_plotavel, titulo_filtro
from src.controllers.headers import heading_with_help
from src.controllers.kpis import render_metric_card
from src.controllers.resilience import resilient_view, safe_render
from src.config.glossary import help_text
from src.config.i18n import t
from src.models.formatting import fmt_dias


def _grafico_prazos(foco: pd.DataFrame, cena_sel: str, ano_sel: str | int) -> None:
    raw_cols = ["PMR", "PME", "PMP", "Ciclo_Financeiro"]
    plot_df = serie_temporal_plotavel(foco, raw_cols)
    rename = {
        "PMR": t("prazos.pmr"),
        "PME": t("prazos.pme"),
        "PMP": t("prazos.pmp"),
        "Ciclo_Financeiro": t("prazos.cycle"),
    }
    plot_df = plot_df.rename(columns=rename)
    y_cols = [rename[c] for c in raw_cols]
    selected_cols = st.multiselect(
        "Exibir no gráfico:",
        options=y_cols,
        default=y_cols,
        key="prazos_linhas_trajetoria",
    )
    if not selected_cols:
        st.info("Selecione ao menos uma métrica de prazo para exibir o gráfico.")
        return
    fig = px.line(
        plot_df,
        x="ano_num",
        y=selected_cols,
        markers=True,
        labels={
            "ano_num": t("chart.year"),
            "value": t("prazos.days"),
            "variable": t("prazos.term"),
        },
        title=titulo_filtro(t("prazos.chart"), cena_sel, ano_sel),
    )
    fig.update_layout(legend_title_text="", hovermode="x unified")
    fig = ancorar_ano_temporal(fig, plot_df, selected_cols, ano_sel)
    st.plotly_chart(fig, width="stretch", theme="streamlit")


@resilient_view("aba Prazos e ciclo")
def render(foco: pd.DataFrame, k: pd.Series, cena_sel: str, ano_sel: str | int) -> None:
    heading_with_help(t("prazos.title"), "prazos")
    p1, p2, p3, p4 = st.columns(4)
    with p1:
        render_metric_card(t("prazos.pmr"), fmt_dias(k["PMR"]), help_text("pmr"))
    with p2:
        render_metric_card(t("prazos.pme"), fmt_dias(k["PME"]), help_text("pme"))
    with p3:
        render_metric_card(t("prazos.pmp"), fmt_dias(k["PMP"]), help_text("pmp"))
    with p4:
        render_metric_card(t("prazos.cycle"), fmt_dias(k["Ciclo_Financeiro"]), help_text("cycle"))
    safe_render("trajetória dos prazos médios", _grafico_prazos, foco, cena_sel, ano_sel)
    st.markdown(t("prazos.help"))
