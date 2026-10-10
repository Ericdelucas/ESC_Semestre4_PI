"""Aba Capital de giro."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from src.controllers.charts import ancorar_ano_temporal, serie_temporal_plotavel, titulo_filtro
from src.controllers.headers import heading_with_help
from src.controllers.resilience import resilient_view, safe_render
from src.config import COR, COR_ALERTA, COR_SUAVE
from src.config.i18n import t
from src.models.formatting import fmt_rs


def _grafico_evolucao(foco: pd.DataFrame, cena_sel: str, ano_sel: str | int) -> None:
    plot_df = serie_temporal_plotavel(foco, ["NCG", "Saldo_Tesouraria"])
    ncg_lbl, tes_lbl = t("kpi.ncg"), t("kpi.treasury")
    plot_df = plot_df.rename(columns={"NCG": ncg_lbl, "Saldo_Tesouraria": tes_lbl})
    available_lines = [ncg_lbl, tes_lbl]
    selected_lines = st.multiselect(
        t("ui.select_lines"),
        options=available_lines,
        default=available_lines,
        key="capital_giro_linhas_evolucao",
    )
    if not selected_lines:
        st.info(t("ui.select_one_line"))
        return
    fig_ncg = px.line(
        plot_df,
        x="ano_num",
        y=selected_lines,
        markers=True,
        labels={
            "ano_num": t("chart.year"),
            "value": "R$",
            "variable": t("chart.indicator"),
        },
        color_discrete_map={ncg_lbl: COR, tes_lbl: COR_SUAVE},
        title=titulo_filtro(t("chart.evolution"), cena_sel, ano_sel),
    )
    fig_ncg.update_layout(legend_title_text="", hovermode="x unified")
    fig_ncg = ancorar_ano_temporal(fig_ncg, plot_df, selected_lines, ano_sel)
    st.plotly_chart(fig_ncg, width="stretch", theme="streamlit")


def _grafico_composicao(foco_ano: pd.DataFrame, cena_sel: str, ano_sel: str | int) -> None:
    faltando = [c for c in ("ACO", "PCO", "NCG") if c not in foco_ano.columns]
    if faltando:
        raise KeyError(t("cap.err.missing", cols=faltando))
    if foco_ano.empty:
        raise ValueError(t("cap.err.empty"))

    decomp = foco_ano[["ACO", "PCO", "NCG"]].apply(pd.to_numeric, errors="coerce").mean()
    if decomp.isna().all():
        raise ValueError(t("cap.err.na"))

    decomp_df = pd.DataFrame(
        {
            "Componente": [t("comp.aco"), t("comp.pco"), t("comp.ncg")],
            "Valor": [float(decomp["ACO"]), float(decomp["PCO"]), float(decomp["NCG"])],
        }
    )
    fig_bar = px.bar(
        decomp_df,
        x="Componente",
        y="Valor",
        text=[fmt_rs(v) for v in decomp_df["Valor"]],
        color="Componente",
        color_discrete_sequence=[COR_SUAVE, COR_ALERTA, COR],
        title=titulo_filtro(t("chart.ncg_comp"), cena_sel, ano_sel),
    )
    fig_bar.update_layout(showlegend=False, xaxis_title="", yaxis_title="R$")
    fig_bar.update_traces(textposition="outside")
    fig_bar.update_xaxes(tickangle=-15)
    st.plotly_chart(fig_bar, width="stretch", theme="streamlit")


@resilient_view("aba Capital de giro")
def render(foco: pd.DataFrame, foco_ano: pd.DataFrame, cena_sel: str, ano_sel: str | int) -> None:
    heading_with_help(t("cap.evolution"), "ncg_treasury")
    safe_render("gráfico de evolução NCG × Tesouraria", _grafico_evolucao, foco, cena_sel, ano_sel)
    heading_with_help(t("cap.ncg_source"), "ncg_composition")
    safe_render("composição da NCG", _grafico_composicao, foco_ano, cena_sel, ano_sel)
