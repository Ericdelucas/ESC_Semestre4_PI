"""Aba Distribuição & Probabilidades."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.components.charts import figura_histograma_caixa_final
from src.components.resilience import resilient_view, safe_render
from src.config import COR, COR_OK, COR_SUAVE, COR_VERMELHO
from src.config.i18n import t
from src.data.formatting import fmt_rs


def _boxplot(serie_cx: pd.Series, qs: pd.Series, ano_enc: int) -> None:
    fig_box = go.Figure()
    fig_box.add_trace(
        go.Box(
            y=serie_cx,
            name=t("dist.box_name", ano=ano_enc),
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
        title=t("dist.box_title"),
        yaxis_title=t("dist.box_y"),
        showlegend=False,
    )
    st.plotly_chart(fig_box, width="stretch", theme="streamlit")


@resilient_view("aba Distribuição & Probabilidades")
def render(ranking: pd.DataFrame, ano_enc: int, n_cenarios: int, p_ruina: float) -> None:
    st.markdown(t("dist.title"))
    st.caption(t("dist.caption"))

    alerta1, alerta2, alerta3 = st.columns(3)
    alerta1.metric(t("dist.prob", ano=ano_enc), f"{p_ruina:.1f}%")
    alerta2.metric(t("dist.ruin"), f"{int((ranking['caixa_ano12'] < 0).sum()):,}")
    alerta3.metric(t("dist.median"), fmt_rs(float(ranking["caixa_ano12"].median())))

    if p_ruina > 10:
        st.error(t("dist.alert_hi", p=p_ruina, ano=ano_enc))
    elif p_ruina > 0:
        st.warning(t("dist.alert_mid", p=p_ruina, ano=ano_enc))
    else:
        st.success(t("dist.alert_ok", ano=ano_enc))

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
    st.caption(t("dist.foot"))
