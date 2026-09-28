"""Sub-abas da persona CEO."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.config import COR_ALERTA
from src.models.formatting import fmt_rs

from .common import _break_even_df, _dre


def render_ceo_visao_geral(df: pd.DataFrame, cena: str, ano_sel: str | int) -> None:
    _ = ano_sel
    dados = _dre(df, cena)
    if dados.empty:
        st.info("Sem dados de DRE para este cenário.")
        return
    medias = dados.mean(numeric_only=True)
    waterfall = go.Figure(
        go.Waterfall(
            name="DRE média",
            orientation="v",
            measure=["relative", "relative", "relative", "relative", "relative", "relative", "total"],
            x=["Receita Líquida", "Custos", "OPEX", "Depreciação", "Resultado Financeiro", "IR/CS", "Lucro Líquido"],
            y=[
                medias["Receita Líquida"],
                medias["Custos"],
                medias["OPEX"],
                medias["Depreciação"],
                medias["Resultado Financeiro"],
                medias["DRE - Imposto de Renda e Contribuição Social"],
                medias["Lucro Líquido"],
            ],
        )
    )
    waterfall.update_layout(title="Cascata média da DRE", yaxis_title="R$")
    st.plotly_chart(waterfall, width="stretch", theme="streamlit")

    evol = dados[["ano_num", "Receita Líquida", "EBITDA"]].melt("ano_num", var_name="Indicador", value_name="Valor")
    fig = px.line(evol, x="ano_num", y="Valor", color="Indicador", markers=True, title="Receita Líquida vs EBITDA")
    fig.update_layout(xaxis_title="Ano", yaxis_title="R$", hovermode="x unified")
    st.plotly_chart(fig, width="stretch", theme="streamlit")


def render_ceo_dre_operacional(df: pd.DataFrame, cena: str, ano_sel: str | int) -> None:
    _ = ano_sel
    dados = _dre(df, cena)
    if dados.empty:
        st.info("Sem dados de DRE operacional para este cenário.")
        return
    receita = dados["Receita Líquida"].replace(0, pd.NA)
    dados["Margem Bruta (%)"] = dados["Margem Bruta"] / receita
    dados["Margem EBITDA (%)"] = dados["EBITDA"] / receita
    dados["Margem EBIT (%)"] = dados["EBIT"] / receita
    dados["YoY OPEX (%)"] = dados["OPEX"].abs().pct_change()
    comp = pd.DataFrame(
        {
            "ano_num": dados["ano_num"],
            "Custos": dados["Custos"].abs() / receita,
            "OPEX": dados["OPEX"].abs() / receita,
            "Depreciação": dados["Depreciação"].abs() / receita,
        }
    ).melt("ano_num", var_name="Conta", value_name="% Receita Líquida")
    fig = px.bar(comp, x="ano_num", y="% Receita Líquida", color="Conta", title="Composição operacional sobre Receita Líquida")
    fig.update_layout(barmode="stack", yaxis_tickformat=".0%", xaxis_title="Ano")
    st.plotly_chart(fig, width="stretch", theme="streamlit")
    tabela = dados[["ano_num", "Receita Líquida", "Custos", "OPEX", "EBITDA", "EBIT", "Lucro Líquido", "Margem Bruta (%)", "Margem EBITDA (%)", "Margem EBIT (%)", "YoY OPEX (%)"]].copy()
    st.dataframe(tabela, width="stretch", hide_index=True)


def render_ceo_break_even(df: pd.DataFrame, cena: str, ano_sel: str | int) -> None:
    _ = ano_sel
    dados = _break_even_df(df, cena)
    if dados.empty:
        st.info("Sem dados suficientes para Break-Even.")
        return
    media = dados.mean(numeric_only=True)
    eixo = pd.Series([0, media["Break-Even"], media["Receita Líquida"]]).dropna()
    chart = pd.DataFrame({"Receita": eixo})
    chart["Receita Total"] = chart["Receita"]
    chart["Custos Totais"] = media["Custos Fixos"] + (chart["Receita"] * (1 - media["Margem de Contribuição (%)"]))
    fig = px.line(chart.melt("Receita", var_name="Linha", value_name="Valor"), x="Receita", y="Valor", color="Linha", markers=True, title="Ponto de equilíbrio médio")
    fig.add_vline(x=media["Break-Even"], line_dash="dash", line_color=COR_ALERTA, annotation_text="Break-Even")
    st.plotly_chart(fig, width="stretch", theme="streamlit")
    fig_area = px.area(dados, x="ano_num", y="Margem de Segurança (%)", title="Margem de segurança ao longo do horizonte")
    fig_area.update_layout(yaxis_tickformat=".1%")
    st.plotly_chart(fig_area, width="stretch", theme="streamlit")


def render_ceo_ltv_cac(df: pd.DataFrame, cena: str, ano_sel: str | int) -> None:
    _ = ano_sel
    dados = _break_even_df(df, cena)
    if dados.empty:
        st.info("Sem dados suficientes para LTV/CAC.")
        return
    ticket = 4_500.0
    retencao = 10.0
    investimento = 100_000.0
    novos = 1_000.0
    dados["CAC"] = investimento / novos
    dados["LTV"] = ticket * dados["Margem de Contribuição (%)"].fillna(0) * retencao
    dados["LTV/CAC"] = dados["LTV"] / dados["CAC"].replace(0, pd.NA)
    c1, c2, c3 = st.columns(3)
    c1.metric("LTV médio", fmt_rs(float(dados["LTV"].mean())))
    c2.metric("CAC médio", fmt_rs(float(dados["CAC"].mean())))
    c3.metric("Razão LTV/CAC", f"{float(dados['LTV/CAC'].mean()):.1f}x")
    comp = dados[["ano_num", "LTV", "CAC"]].melt("ano_num", var_name="Indicador", value_name="Valor")
    fig = px.bar(comp, x="ano_num", y="Valor", color="Indicador", barmode="group", title="LTV vs CAC por ano")
    st.plotly_chart(fig, width="stretch", theme="streamlit")
