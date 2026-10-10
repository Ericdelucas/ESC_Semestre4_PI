"""Analises customizadas do sandbox."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from src.config.i18n import t
from src.models.financial_metrics import FINANCIAL_METRICS_DICT, format_metric_value, metric_label, metric_short_name, metric_timeseries
from src.models.formatting import cena_rotulo
from src.models.formatting.tables import render_table


def render_custom_analysis(df: pd.DataFrame, analysis: dict[str, str], cena: str, ano_sel: str | int) -> None:
    metric_name = analysis["metric"]
    chart_type = analysis["chart_type"]
    metric = FINANCIAL_METRICS_DICT[metric_name]
    serie = metric_timeseries(df, cena, metric_name)
    if serie.empty:
        st.info(t("custom.empty"))
        return

    nome = metric_short_name(metric_name, metric["nome"])
    st.markdown(f"#### {nome}")
    st.caption(f"{metric_label(metric_name)} · {t('custom.scene', cena=cena_rotulo(cena))}")

    serie_view = serie.copy()
    if ano_sel != "Todos":
        serie_view = serie_view.loc[serie_view["ano_num"] == int(ano_sel)]
    valor_ref = float(serie_view["Valor"].mean()) if not serie_view.empty else float("nan")

    if chart_type == "Card KPI":
        st.metric(nome, format_metric_value(metric_name, valor_ref))
        return

    if chart_type == "Tabela":
        tabela = serie.rename(columns={"ano_num": t("chart.year"), "Valor": nome})
        render_table(tabela)
        return

    if chart_type == "Linha":
        fig = px.line(serie, x="ano_num", y="Valor", markers=True, title=nome)
    elif chart_type == "Barra":
        fig = px.bar(serie, x="ano_num", y="Valor", title=nome)
    else:
        fig = px.area(serie, x="ano_num", y="Valor", title=nome)
    fig.update_layout(xaxis_title=t("chart.year"), yaxis_title=nome, hovermode="x unified")
    st.plotly_chart(fig, width="stretch", theme="streamlit")

    c1, c2 = st.columns(2)
    c1.metric(t("custom.slice"), format_metric_value(metric_name, valor_ref))
    c2.metric(t("custom.mean"), format_metric_value(metric_name, float(serie["Valor"].mean())))
