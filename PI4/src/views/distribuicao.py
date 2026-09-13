"""Aba Distribuição & Probabilidades."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.components.charts import figura_histograma_caixa_final
from src.components.resilience import safe_render
from src.config import COR, COR_OK, COR_SUAVE, COR_VERMELHO
from src.data.formatting import fmt_rs


def _boxplot(serie_cx: pd.Series, qs: pd.Series, ano_enc: int) -> None:
    fig_box = go.Figure()
    fig_box.add_trace(
        go.Box(
            y=serie_cx,
            name=f"Caixa Ano {ano_enc}",
            marker_color=COR_SUAVE,
            boxmean=True,
            hovertemplate="%{y}<extra></extra>",
        )
    )
    for q, nome, cor in [(0.05, "P5", COR_VERMELHO), (0.50, "P50", COR), (0.95, "P95", COR_OK)]:
        fig_box.add_hline(
            y=float(qs[q]),
            line_dash="dot",
            line_color=cor,
            annotation_text=nome,
            annotation_position="right",
        )
    fig_box.update_layout(
        title="Boxplot / percentis — cauda de risco do caixa final",
        yaxis_title="Caixa de encerramento (R$)",
        showlegend=False,
    )
    st.plotly_chart(fig_box, width="stretch", theme="streamlit")


def render(ranking: pd.DataFrame, ano_enc: int, n_cenarios: int, p_ruina: float) -> None:
    st.markdown("### Distribuição & Probabilidades")
    st.caption("Leitura de cauda de risco para credores e concessão — foco no encerramento do horizonte.")

    alerta1, alerta2, alerta3 = st.columns(3)
    alerta1.metric(
        f"Probabilidade de caixa negativo no Ano {ano_enc}",
        f"{p_ruina:.1f}%",
        help="Fração dos cenários com saldo de caixa de encerramento negativo.",
    )
    alerta2.metric("Cenários em ruína de caixa", f"{int((ranking['caixa_ano12'] < 0).sum()):,}")
    alerta3.metric("Mediana do caixa no Ano 12", fmt_rs(float(ranking["caixa_ano12"].median())))

    if p_ruina > 10:
        st.error(f"Alerta de liquidez: {p_ruina:.1f}% dos cenários encerram o Ano {ano_enc} com caixa insuficiente.")
    elif p_ruina > 0:
        st.warning(f"Há cauda de risco: {p_ruina:.1f}% dos cenários terminam com caixa negativo no Ano {ano_enc}.")
    else:
        st.success(f"Nenhum cenário encerra o Ano {ano_enc} com caixa negativo nesta base.")

    serie_cx = ranking["caixa_ano12"].dropna()

    def _hist() -> None:
        st.plotly_chart(
            figura_histograma_caixa_final(serie_cx, ano_enc, n_cenarios),
            width="stretch",
            theme="streamlit",
        )

    safe_render("histograma de liquidez final", _hist)

    qs = serie_cx.quantile([0.05, 0.25, 0.50, 0.75, 0.95])
    pcols = st.columns(5)
    for col_ui, (q, nome) in zip(
        pcols,
        [(0.05, "P5"), (0.25, "P25"), (0.50, "P50"), (0.75, "P75"), (0.95, "P95")],
        strict=True,
    ):
        col_ui.metric(nome, fmt_rs(float(qs[q])))

    safe_render("boxplot de percentis", _boxplot, serie_cx, qs, ano_enc)
    st.caption("P5/P95 ajudam credores a ler extremos: quanto de caixa resta nos piores e melhores 5% dos cenários.")
