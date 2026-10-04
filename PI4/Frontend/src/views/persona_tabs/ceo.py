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
from src.models.formatting import fmt_rs

from .common import _break_even_df, _dre


def _s(dados: pd.DataFrame, *aliases: str) -> pd.Series:
    return series_by_alias(dados, aliases)


def _ano_axis(fig: go.Figure) -> None:
    fig.update_xaxes(title_text="Ano", tickmode="linear", tick0=1, dtick=1)


def render_ceo_visao_geral(df: pd.DataFrame, cena: str, ano_sel: str | int) -> None:
    """Renderiza cascata media da DRE e evolucao de receita/EBITDA."""
    _ = ano_sel
    dados = _dre(df, cena)
    if dados.empty:
        st.info("Sem dados de DRE para este cenario.")
        return

    medias = dados.mean(numeric_only=True)
    receita = float(_s(medias.to_frame().T, "Receita Líquida", "Receita Liquida").iloc[0])
    custos = float(_s(medias.to_frame().T, "Custos").iloc[0])
    opex = float(_s(medias.to_frame().T, "OPEX").iloc[0])
    dep = float(_s(medias.to_frame().T, "Depreciação", "Depreciacao").iloc[0])
    resultado_fin = float(_s(medias.to_frame().T, "Resultado Financeiro").iloc[0])
    ir_cs = float(_s(medias.to_frame().T, "DRE - Imposto de Renda e Contribuição Social").iloc[0])
    lucro = float(_s(medias.to_frame().T, "Lucro Líquido", "Lucro Liquido").iloc[0])

    labels = ["Receita Liquida", "Custos", "OPEX", "EBITDA", "Depreciacao", "Resultado Financeiro", "IR/CS", "Lucro Liquido"]
    values = [receita, custos, opex, 0, dep, resultado_fin, ir_cs, 0]
    text = [fmt_rs(v) if v else "" for v in [receita, custos, opex, receita + custos + opex, dep, resultado_fin, ir_cs, lucro]]
    waterfall = go.Figure(
        go.Waterfall(
            name="DRE media",
            orientation="v",
            measure=["absolute", "relative", "relative", "total", "relative", "relative", "relative", "total"],
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
        title="Cascata media da DRE",
        yaxis_title="R$",
        uniformtext_minsize=10,
        uniformtext_mode="show",
        margin={"t": 70, "b": 90},
    )
    st.plotly_chart(waterfall, width="stretch", theme="streamlit")

    evol = pd.DataFrame(
        {
            "Ano": pd.to_numeric(dados["ano_num"], errors="coerce").astype(int),
            "Receita Liquida": _s(dados, "Receita Líquida", "Receita Liquida"),
            "EBITDA": _s(dados, "EBITDA"),
        }
    ).melt("Ano", var_name="Indicador", value_name="Valor")
    fig = px.line(evol, x="Ano", y="Valor", color="Indicador", markers=True, title="Receita Liquida vs EBITDA")
    fig.update_layout(yaxis_title="R$", hovermode="x unified")
    _ano_axis(fig)
    st.plotly_chart(fig, width="stretch", theme="streamlit")


def render_ceo_dre_operacional(df: pd.DataFrame, cena: str, ano_sel: str | int) -> None:
    """Renderiza margens e composicao operacional."""
    _ = ano_sel
    dados = _dre(df, cena)
    if dados.empty:
        st.info("Sem dados de DRE operacional para este cenario.")
        return

    receita = _s(dados, "Receita Líquida", "Receita Liquida").replace(0, pd.NA)
    dados["Margem Bruta (%)"] = _s(dados, "Margem Bruta") / receita
    dados["Margem EBITDA (%)"] = _s(dados, "EBITDA") / receita
    dados["Margem EBIT (%)"] = _s(dados, "EBIT") / receita
    dados["YoY OPEX (%)"] = _s(dados, "OPEX").abs().pct_change()

    comp = pd.DataFrame(
        {
            "Ano": pd.to_numeric(dados["ano_num"], errors="coerce").astype(int),
            "Custos": _s(dados, "Custos").abs() / receita,
            "OPEX": _s(dados, "OPEX").abs() / receita,
            "Depreciacao": _s(dados, "Depreciação", "Depreciacao").abs() / receita,
        }
    ).melt("Ano", var_name="Conta", value_name="% Receita Liquida")
    comp = comp.dropna(subset=["% Receita Liquida"])
    fig = px.bar(
        comp,
        x="Ano",
        y="% Receita Liquida",
        color="Conta",
        title="Composicao operacional sobre Receita Liquida",
        color_discrete_map={"Custos": COR_VERMELHO, "OPEX": COR_ALERTA, "Depreciacao": COR_SUAVE},
    )
    fig.update_traces(opacity=0.9)
    fig.update_layout(barmode="stack", yaxis_tickformat=".0%")
    _ano_axis(fig)
    st.plotly_chart(fig, width="stretch", theme="streamlit")

    tabela = pd.DataFrame(
        {
            "Ano": pd.to_numeric(dados["ano_num"], errors="coerce").astype(int),
            "Receita Liquida": _s(dados, "Receita Líquida", "Receita Liquida"),
            "Custos": _s(dados, "Custos"),
            "OPEX": _s(dados, "OPEX"),
            "EBITDA": _s(dados, "EBITDA"),
            "EBIT": _s(dados, "EBIT"),
            "Lucro Liquido": _s(dados, "Lucro Líquido", "Lucro Liquido"),
            "Margem Bruta (%)": dados["Margem Bruta (%)"],
            "Margem EBITDA (%)": dados["Margem EBITDA (%)"],
            "Margem EBIT (%)": dados["Margem EBIT (%)"],
            "YoY OPEX (%)": dados["YoY OPEX (%)"],
        }
    )
    st.dataframe(tabela, width="stretch", hide_index=True)


def render_ceo_break_even(df: pd.DataFrame, cena: str, ano_sel: str | int) -> None:
    """Renderiza ponto de equilibrio com intersecao igual ao KPI consolidado."""
    _ = ano_sel
    dados = _break_even_df(df, cena)
    if dados.empty:
        st.info("Sem dados suficientes para Break-Even.")
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
    chart["Receita Total"] = chart["Receita"]
    chart["Custos Totais"] = custo_fixo + (chart["Receita"] * (1 - margem))
    fig = px.line(
        chart.melt("Receita", var_name="Linha", value_name="Valor"),
        x="Receita",
        y="Valor",
        color="Linha",
        markers=True,
        title="Ponto de equilibrio medio",
    )
    fig.add_vline(x=be, line_dash="dash", line_color=COR_ALERTA, annotation_text=f"Break-Even {fmt_rs(be)}")
    fig.update_layout(xaxis_title="Receita", yaxis_title="R$")
    st.plotly_chart(fig, width="stretch", theme="streamlit")

    fig_area = px.area(
        pd.DataFrame(
            {
                "Ano": pd.to_numeric(dados["ano_num"], errors="coerce").astype(int),
                "Margem de Seguranca (%)": _s(dados, "Margem de Segurança (%)", "Margem de Seguranca (%)"),
            }
        ),
        x="Ano",
        y="Margem de Seguranca (%)",
        title="Margem de seguranca ao longo do horizonte",
    )
    fig_area.update_layout(yaxis_tickformat=".1%")
    _ano_axis(fig_area)
    st.plotly_chart(fig_area, width="stretch", theme="streamlit")


def render_ceo_ltv_cac(df: pd.DataFrame, cena: str, ano_sel: str | int) -> None:
    """Renderiza LTV/CAC calculado no backend."""
    _ = ano_sel
    dados = calculate_ltv_cac(df, cena)
    if dados.empty:
        st.info("Sem dados suficientes para LTV/CAC.")
        return
    resumo = summarize_ltv_cac(df, cena, ano_sel)
    c1, c2, c3 = st.columns(3)
    c1.metric("LTV medio", fmt_rs(resumo["ltv"]))
    c2.metric("CAC medio", fmt_rs(resumo["cac"]))
    c3.metric("Razao LTV/CAC", f"{resumo['ratio']:.1f}x")

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
    fig.update_layout(title="LTV vs CAC por ano", hovermode="x unified", margin={"t": 70})
    fig.update_xaxes(title_text="Ano", tickmode="linear", tick0=1, dtick=1)
    fig.update_yaxes(title_text="LTV (R$)", secondary_y=False)
    fig.update_yaxes(title_text="CAC (R$)", secondary_y=True)
    st.plotly_chart(fig, width="stretch", theme="streamlit")
