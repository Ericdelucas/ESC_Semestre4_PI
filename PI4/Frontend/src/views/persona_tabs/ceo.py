"""Sub-abas da persona CEO."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from Backend.metrics import calculate_ltv_cac, summarize_ltv_cac
from Backend.metrics.column_resolver import series_by_alias
from src.config import COR, COR_ALERTA, COR_OK, COR_SUAVE, COR_VERMELHO
from src.config.i18n import t
from src.models.formatting import fmt_rs
from src.models.formatting.tables import render_table

from .common import _break_even_df, _dre


def _s(dados: pd.DataFrame, *aliases: str) -> pd.Series:
    return series_by_alias(dados, aliases)


def _ano_axis(fig: go.Figure) -> None:
    fig.update_xaxes(title_text=t("chart.year"), tickmode="linear", tick0=1, dtick=1)


def render_ceo_visao_geral(df: pd.DataFrame, cena: str, ano_sel: str | int) -> None:
    """Renderiza cascata media da DRE e evolucao de receita/EBITDA."""
    _ = ano_sel
    dados = _dre(df, cena)
    if dados.empty:
        st.info(t("ceo.empty.dre"))
        return

    medias = dados.mean(numeric_only=True)
    receita = float(_s(medias.to_frame().T, "Receita Líquida", "Receita Liquida").iloc[0])
    custos = float(_s(medias.to_frame().T, "Custos").iloc[0])
    opex = float(_s(medias.to_frame().T, "OPEX").iloc[0])
    dep = float(_s(medias.to_frame().T, "Depreciação", "Depreciacao").iloc[0])
    resultado_fin = float(_s(medias.to_frame().T, "Resultado Financeiro").iloc[0])
    ir_cs = float(_s(medias.to_frame().T, "DRE - Imposto de Renda e Contribuição Social").iloc[0])
    lucro = float(_s(medias.to_frame().T, "Lucro Líquido", "Lucro Liquido").iloc[0])

    custos_delta = -abs(custos)
    opex_delta = -abs(opex)
    dep_delta = -abs(dep)
    labels = [
        t("ceo.wf.revenue"),
        t("ceo.wf.costs"),
        t("ceo.wf.opex"),
        t("ceo.wf.ebitda"),
        t("ceo.wf.da"),
        t("ceo.wf.fin"),
        t("ceo.wf.tax"),
        t("ceo.wf.net"),
    ]
    values = [receita, custos_delta, opex_delta, float(_s(medias.to_frame().T, "EBITDA").iloc[0]), dep_delta, resultado_fin, ir_cs, lucro]
    text = [fmt_rs(v) if v else "" for v in values]
    waterfall = go.Figure(
        go.Waterfall(
            name=t("ceo.chart.waterfall_name"),
            orientation="v",
            measure=["relative", "relative", "relative", "total", "relative", "relative", "relative", "total"],
            x=labels,
            y=values,
            text=text,
            textposition="outside",
            cliponaxis=False,
            connector={"line": {"color": "rgba(90,90,90,0.45)"}},
            increasing={"marker": {"color": COR_OK}},
            decreasing={"marker": {"color": COR_VERMELHO}},
            totals={"marker": {"color": COR}},
        )
    )
    waterfall.update_layout(
        title=t("ceo.chart.waterfall"),
        yaxis_title="R$",
        uniformtext_minsize=10,
        uniformtext_mode="show",
        margin={"t": 70, "b": 90},
    )
    st.plotly_chart(waterfall, width="stretch", theme="streamlit")

    evol = pd.DataFrame(
        {
            t("chart.year"): pd.to_numeric(dados["ano_num"], errors="coerce").astype(int),
            t("ceo.wf.revenue"): _s(dados, "Receita Líquida", "Receita Liquida"),
            t("ceo.wf.ebitda"): _s(dados, "EBITDA"),
        }
    ).melt(t("chart.year"), var_name="Indicador", value_name="Valor")
    fig = px.line(evol, x=t("chart.year"), y="Valor", color="Indicador", markers=True, title=t("ceo.chart.rev_ebitda"))
    fig.update_layout(yaxis_title="R$", hovermode="x unified")
    _ano_axis(fig)
    st.plotly_chart(fig, width="stretch", theme="streamlit")


def render_ceo_dre_operacional(df: pd.DataFrame, cena: str, ano_sel: str | int) -> None:
    """Renderiza margens e composicao operacional."""
    _ = ano_sel
    dados = _dre(df, cena)
    if dados.empty:
        st.info(t("ceo.empty.dre_op"))
        return

    receita = _s(dados, "Receita Líquida", "Receita Liquida").replace(0, pd.NA)
    dados["Margem Bruta (%)"] = _s(dados, "Margem Bruta") / receita
    dados["Margem EBITDA (%)"] = _s(dados, "EBITDA") / receita
    dados["Margem EBIT (%)"] = _s(dados, "EBIT") / receita
    dados["YoY OPEX (%)"] = _s(dados, "OPEX").abs().pct_change()

    comp = pd.DataFrame(
        {
            t("chart.year"): pd.to_numeric(dados["ano_num"], errors="coerce").astype(int),
            t("ceo.comp.costs"): _s(dados, "Custos").abs() / receita,
            t("ceo.comp.opex"): _s(dados, "OPEX").abs() / receita,
            t("ceo.comp.da"): _s(dados, "Depreciação", "Depreciacao").abs() / receita,
        }
    ).melt(t("chart.year"), var_name="Conta", value_name=t("ceo.comp.share"))
    comp = comp.dropna(subset=[t("ceo.comp.share")])
    fig = px.bar(
        comp,
        x=t("chart.year"),
        y=t("ceo.comp.share"),
        color="Conta",
        title=t("ceo.chart.composition"),
        color_discrete_map={t("ceo.comp.costs"): COR_VERMELHO, t("ceo.comp.opex"): COR_ALERTA, t("ceo.comp.da"): COR_SUAVE},
    )
    fig.update_traces(opacity=0.9)
    fig.update_layout(barmode="stack", yaxis_tickformat=".0%")
    _ano_axis(fig)
    st.plotly_chart(fig, width="stretch", theme="streamlit")

    tabela = pd.DataFrame(
        {
            t("chart.year"): pd.to_numeric(dados["ano_num"], errors="coerce").astype(int),
            t("ceo.wf.revenue"): _s(dados, "Receita Líquida", "Receita Liquida"),
            t("ceo.wf.costs"): _s(dados, "Custos"),
            t("ceo.wf.opex"): _s(dados, "OPEX"),
            t("ceo.wf.ebitda"): _s(dados, "EBITDA"),
            "EBIT": _s(dados, "EBIT"),
            t("ceo.wf.net"): _s(dados, "Lucro Líquido", "Lucro Liquido"),
            t("ceo.tbl.gross"): dados["Margem Bruta (%)"],
            t("ceo.tbl.mebitda"): dados["Margem EBITDA (%)"],
            t("ceo.tbl.mebit"): dados["Margem EBIT (%)"],
            t("ceo.tbl.yoy"): dados["YoY OPEX (%)"],
        }
    )
    render_table(tabela)


def render_ceo_break_even(df: pd.DataFrame, cena: str, ano_sel: str | int) -> None:
    """Renderiza ponto de equilibrio com intersecao igual ao KPI consolidado."""
    _ = ano_sel
    dados = _break_even_df(df, cena)
    if dados.empty:
        st.info(t("ceo.empty.be"))
        return
    be = float(_s(dados, "Break-Even").mean())
    margem = float(_s(dados, "Margem de Contribuição (%)", "Margem de Contribuicao (%)").mean())
    receita_media = float(_s(dados, "Receita Líquida", "Receita Liquida").mean())
    margem = 0.0 if pd.isna(margem) else margem
    be = 0.0 if pd.isna(be) else be
    receita_media = 0.0 if pd.isna(receita_media) else receita_media
    custo_fixo = be * margem
    eixo = pd.Series([0.0, be, max(receita_media, be * 1.15)]).dropna().drop_duplicates().sort_values()
    chart = pd.DataFrame({"Receita": eixo})
    chart[t("ceo.line.revenue")] = chart["Receita"]
    chart[t("ceo.line.costs")] = custo_fixo + (chart["Receita"] * (1 - margem))
    fig = px.line(
        chart.melt("Receita", var_name="Linha", value_name="Valor"),
        x="Receita",
        y="Valor",
        color="Linha",
        markers=True,
        title=t("ceo.chart.be"),
    )
    fig.add_vline(x=be, line_dash="dash", line_color=COR_ALERTA, annotation_text=f"Break-Even {fmt_rs(be)}")
    fig.update_layout(xaxis_title=t("ceo.axis.revenue"), yaxis_title="R$")
    st.plotly_chart(fig, width="stretch", theme="streamlit")

    fig_area = px.area(
        pd.DataFrame(
            {
                t("chart.year"): pd.to_numeric(dados["ano_num"], errors="coerce").astype(int),
                t("ceo.tbl.safety"): _s(dados, "Margem de Segurança (%)", "Margem de Seguranca (%)"),
            }
        ),
        x=t("chart.year"),
        y=t("ceo.tbl.safety"),
        title=t("ceo.chart.safety"),
    )
    fig_area.update_layout(yaxis_tickformat=".1%")
    _ano_axis(fig_area)
    st.plotly_chart(fig_area, width="stretch", theme="streamlit")


def render_ceo_ltv_cac(df: pd.DataFrame, cena: str, ano_sel: str | int) -> None:
    """Renderiza LTV/CAC calculado no backend."""
    _ = ano_sel
    dados = calculate_ltv_cac(df, cena)
    if dados.empty:
        st.info(t("ceo.empty.ltv"))
        return
    resumo = summarize_ltv_cac(df, cena, ano_sel)
    c1, c2, c3 = st.columns(3)
    c1.metric(t("ceo.metric.ltv"), fmt_rs(resumo["ltv"]))
    c2.metric(t("ceo.metric.cac"), fmt_rs(resumo["cac"]))
    c3.metric(t("ceo.metric.ratio"), f"{resumo['ratio']:.1f}x")

    fig = make_subplots(specs=[[{"secondary_y": True}]])
    anos = pd.to_numeric(dados["ano_num"], errors="coerce").astype(int)
    fig.add_bar(x=anos, y=dados["LTV"], name="LTV", marker_color=COR, text=dados["LTV"].map(fmt_rs), textposition="outside")
    fig.add_scatter(
        x=anos,
        y=dados["CAC"],
        name="CAC",
        mode="lines+markers+text",
        line={"color": COR_ALERTA, "width": 3},
        text=dados["CAC"].map(fmt_rs),
        textposition="top center",
        secondary_y=True,
    )
    fig.update_layout(title=t("ceo.chart.ltv_cac"), hovermode="x unified", margin={"t": 70})
    fig.update_xaxes(title_text=t("chart.year"), tickmode="linear", tick0=1, dtick=1)
    fig.update_yaxes(title_text="LTV (R$)", secondary_y=False)
    fig.update_yaxes(title_text="CAC (R$)", secondary_y=True)
    st.plotly_chart(fig, width="stretch", theme="streamlit")
