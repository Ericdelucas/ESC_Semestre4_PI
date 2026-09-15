"""Aba Comparar cenários."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from src.components.charts import ancorar_ano_temporal, titulo_filtro
from src.components.resilience import resilient_view, safe_render
from src.config import CORES_COMPARA, METRICAS_NUVEM
from src.config.i18n import get_lang, t
from src.data.formatting import cenas_padrao_comparacao, cena_rotulo, fmt_dias, fmt_pct, fmt_rs


@resilient_view("aba Comparar cenários")
def render(ind: pd.DataFrame, cenas: list[str], cena_sel: str, ano_sel: str | int) -> None:
    st.markdown(t("cmp.title"))
    st.caption(t("cmp.caption"))
    padrao_comp = [c for c in cenas_padrao_comparacao(cenas) if c in cenas]
    escolhidos = st.multiselect(
        t("cmp.select"),
        options=cenas,
        default=padrao_comp,
        max_selections=3,
        format_func=cena_rotulo,
        key=f"cenas_comparar_{get_lang()}",
    )
    if len(escolhidos) < 2:
        st.info(t("cmp.need2"))
        return

    metric_keys = list(METRICAS_NUVEM.keys())
    metric_labels = [t(k) for k in metric_keys]
    label_to_key = dict(zip(metric_labels, metric_keys, strict=True))
    escolhido = st.selectbox(
        t("cmp.metric"),
        options=metric_labels,
        index=0,
        key=f"metrica_comparar_{get_lang()}",
    )
    metric_key = label_to_key[escolhido]
    col_comp, _maior = METRICAS_NUVEM[metric_key]
    rotulo_comp = t(metric_key)
    trilhas = ind[ind["CENA"].isin(escolhidos)].sort_values(["CENA", "ano_num"]).copy()
    trilhas["rótulo"] = trilhas["CENA"].map(cena_rotulo)

    def _linha() -> None:
        fig_comp = px.line(
            trilhas,
            x="ano_num",
            y=col_comp,
            color="rótulo",
            markers=True,
            color_discrete_sequence=CORES_COMPARA,
            labels={
                "ano_num": t("chart.year"),
                col_comp: rotulo_comp,
                "rótulo": t("scenario.prefix"),
            },
            title=titulo_filtro(t("cmp.chart", metric=rotulo_comp), cena_sel, ano_sel),
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
            col_ui.markdown(f"**{cena_rotulo(cena)}**")
            col_ui.metric(t("cmp.row.cash"), fmt_rs(m["disponivel"]))
            col_ui.metric(t("cmp.row.gen"), fmt_rs(m["geracao_caixa"]))
            col_ui.metric(t("cmp.row.ncg"), fmt_rs(m["NCG"]))
            col_ui.metric(t("cmp.row.treasury"), fmt_rs(m["Saldo_Tesouraria"]))
            col_ui.metric(t("cmp.row.liq"), f"{m['liquidez']:.2f}x" if pd.notna(m["liquidez"]) else "—")
            col_ui.metric(t("cmp.row.cycle"), fmt_dias(m["Ciclo_Financeiro"]))

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
            t("cmp.row.cash"): resumo_comp["caixa"].map(fmt_rs),
            t("cmp.row.gen"): resumo_comp["geracao_caixa"].map(fmt_rs),
            t("cmp.row.ncg"): resumo_comp["NCG"].map(fmt_rs),
            t("cmp.row.treasury"): resumo_comp["tesouraria"].map(fmt_rs),
            t("cmp.row.liq"): resumo_comp["liquidez"].map(lambda x: f"{x:.2f}x" if pd.notna(x) else "—"),
            t("cmp.row.cycle"): resumo_comp["ciclo"].map(fmt_dias),
            t("cmp.row.profit"): resumo_comp["rentabilidade"].map(fmt_pct),
        }
        st.dataframe(pd.DataFrame(linhas_fmt).T, width="stretch")
    except Exception as exc:  # noqa: BLE001
        st.error(str(exc))
