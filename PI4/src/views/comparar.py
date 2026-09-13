"""Aba Comparar cenários."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from src.components.charts import ancorar_ano_temporal, titulo_filtro
from src.components.resilience import safe_render
from src.config import CORES_COMPARA, METRICAS_NUVEM
from src.data.analytics import cenas_padrao_comparacao
from src.data.formatting import fmt_dias, fmt_pct, fmt_rs


def render(ind: pd.DataFrame, cenas: list[str], cena_sel: str, ano_sel: str | int) -> None:
    st.markdown("#### Comparador lado a lado")
    st.caption("Escolha **2 ou 3** cenários para ver a mesma métrica no horizonte e os KPIs na mesma tela.")
    padrao_comp = [c for c in cenas_padrao_comparacao(cenas) if c in cenas]
    escolhidos = st.multiselect(
        "Cenários para comparar",
        options=cenas,
        default=padrao_comp,
        max_selections=3,
        key="cenas_comparar",
    )
    if len(escolhidos) < 2:
        st.info("Selecione pelo menos dois cenários (máximo três).")
        return

    rotulo_comp = st.selectbox(
        "Métrica do gráfico",
        options=list(METRICAS_NUVEM.keys()),
        index=0,
        key="metrica_comparar",
    )
    col_comp, _maior = METRICAS_NUVEM[rotulo_comp]
    trilhas = ind[ind["CENA"].isin(escolhidos)].sort_values(["CENA", "ano_num"])

    def _linha() -> None:
        fig_comp = px.line(
            trilhas,
            x="ano_num",
            y=col_comp,
            color="CENA",
            markers=True,
            color_discrete_sequence=CORES_COMPARA,
            labels={"ano_num": "Ano", col_comp: rotulo_comp, "CENA": "Cenário"},
            title=titulo_filtro(f"{rotulo_comp}: comparação no horizonte", cena_sel, ano_sel),
        )
        fig_comp.update_layout(hovermode="x unified", legend_title_text="")
        fig_comp = ancorar_ano_temporal(fig_comp, trilhas, [col_comp], ano_sel)
        st.plotly_chart(fig_comp, width="stretch", theme="streamlit")

    safe_render("comparação temporal de cenários", _linha)

    try:
        cols_kpi = st.columns(len(escolhidos))
        for col_ui, cena in zip(cols_kpi, escolhidos, strict=True):
            recorte = trilhas[trilhas["CENA"] == cena]
            if ano_sel != "Todos":
                recorte = recorte[recorte["ano_num"] == ano_sel]
            m = recorte[
                ["NCG", "Saldo_Tesouraria", "liquidez", "Ciclo_Financeiro", "disponivel", "geracao_caixa"]
            ].mean(numeric_only=True)
            col_ui.markdown(f"**`{cena}`**")
            col_ui.metric("Caixa disponível", fmt_rs(m["disponivel"]))
            col_ui.metric("Geração de caixa", fmt_rs(m["geracao_caixa"]))
            col_ui.metric("NCG", fmt_rs(m["NCG"]))
            col_ui.metric("Saldo de tesouraria", fmt_rs(m["Saldo_Tesouraria"]))
            col_ui.metric("Liquidez corrente", f"{m['liquidez']:.2f}x" if pd.notna(m["liquidez"]) else "—")
            col_ui.metric("Ciclo financeiro", fmt_dias(m["Ciclo_Financeiro"]))

        resumo_comp = (
            trilhas.groupby("CENA", as_index=False)
            .agg(
                caixa=("disponivel", "mean"),
                geracao_caixa=("geracao_caixa", "mean"),
                NCG=("NCG", "mean"),
                tesouraria=("Saldo_Tesouraria", "mean"),
                liquidez=("liquidez", "mean"),
                ciclo=("Ciclo_Financeiro", "mean"),
                rentabilidade=("rentabilidade", "mean"),
            )
            .set_index("CENA")
            .reindex(escolhidos)
        )
        linhas_fmt = {
            "Caixa disponível": resumo_comp["caixa"].map(fmt_rs),
            "Geração de caixa": resumo_comp["geracao_caixa"].map(fmt_rs),
            "NCG": resumo_comp["NCG"].map(fmt_rs),
            "Saldo de tesouraria": resumo_comp["tesouraria"].map(fmt_rs),
            "Liquidez corrente": resumo_comp["liquidez"].map(lambda x: f"{x:.2f}x" if pd.notna(x) else "—"),
            "Ciclo financeiro": resumo_comp["ciclo"].map(fmt_dias),
            "Rentabilidade": resumo_comp["rentabilidade"].map(fmt_pct),
        }
        st.dataframe(pd.DataFrame(linhas_fmt).T, width="stretch")
    except Exception as exc:  # noqa: BLE001
        st.error("Não foi possível carregar a tabela comparativa no momento.")
        st.caption(f"{type(exc).__name__}: {exc}")
