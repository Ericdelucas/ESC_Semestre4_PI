"""Aba Capital de giro."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from src.components.charts import ancorar_ano_temporal, serie_temporal_plotavel, titulo_filtro
from src.components.resilience import resilient_view, safe_render
from src.config import COR, COR_ALERTA, COR_SUAVE
from src.config.i18n import t
from src.data.formatting import fmt_rs


def _grafico_evolucao(foco: pd.DataFrame, cena_sel: str, ano_sel: str | int) -> None:
    plot_df = serie_temporal_plotavel(foco, ["NCG", "Saldo_Tesouraria"])
    fig_ncg = px.line(
        plot_df,
        x="ano_num",
        y=["NCG", "Saldo_Tesouraria"],
        markers=True,
        labels={
            "ano_num": t("chart.year"),
            "value": "R$",
            "variable": t("chart.indicator"),
        },
        color_discrete_map={"NCG": COR, "Saldo_Tesouraria": COR_SUAVE},
        title=titulo_filtro(t("chart.evolution"), cena_sel, ano_sel),
    )
    fig_ncg.update_layout(legend_title_text="", hovermode="x unified")
    fig_ncg = ancorar_ano_temporal(fig_ncg, plot_df, ["NCG", "Saldo_Tesouraria"], ano_sel)
    st.plotly_chart(fig_ncg, width="stretch", theme="streamlit")


def _grafico_composicao(foco_ano: pd.DataFrame, cena_sel: str, ano_sel: str | int) -> None:
    faltando = [c for c in ("ACO", "PCO", "NCG") if c not in foco_ano.columns]
    if faltando:
        raise KeyError(f"Colunas ausentes na composição da NCG: {faltando}")
    if foco_ano.empty:
        raise ValueError("Recorte sem linhas — escolha outro ano ou cenário.")

    decomp = foco_ano[["ACO", "PCO", "NCG"]].apply(pd.to_numeric, errors="coerce").mean()
    if decomp.isna().all():
        raise ValueError("Valores de ACO/PCO/NCG indisponíveis para este recorte.")

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
    st.markdown(t("cap.evolution"))
    safe_render("gráfico de evolução NCG × Tesouraria", _grafico_evolucao, foco, cena_sel, ano_sel)
    st.markdown(t("cap.ncg_source"))
    safe_render("composição da NCG", _grafico_composicao, foco_ano, cena_sel, ano_sel)
