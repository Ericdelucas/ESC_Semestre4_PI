"""Graficos de histograma usados no dashboard."""

from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from src.config import COR, COR_ALERTA, COR_OK, COR_SUAVE, COR_VERMELHO
from src.config.i18n import t
from src.models.formatting import fmt_rs


def figura_histograma_ano(
    fatia: pd.DataFrame,
    coluna: str,
    rotulo: str,
    ano: int,
    *,
    titulo: str | None = None,
) -> go.Figure:
    serie = fatia[coluna].dropna()
    fig = px.histogram(
        fatia,
        x=coluna,
        nbins=40,
        histnorm="probability",
        color_discrete_sequence=[COR_SUAVE],
        title=titulo or t("faixa.dist_title", metric=rotulo) + f" · {t('filter.year_n', n=ano)} ({len(serie):,})",
        labels={coluna: rotulo, "probability": t("chart.prob")},
    )
    fig.update_layout(yaxis_title=t("chart.prob_frac"), bargap=0.05)
    if serie.empty:
        return fig
    median_lbl, mean_lbl, worst_lbl, best_lbl = t("chart.median"), t("chart.mean"), t("chart.worst"), t("chart.best")
    marcas = [
        (float(serie.median()), COR, median_lbl),
        (float(serie.mean()), COR, mean_lbl),
        (float(serie.min()), COR_ALERTA, worst_lbl),
        (float(serie.max()), COR_OK, best_lbl),
    ]
    dash = {median_lbl: "solid", mean_lbl: "dot", worst_lbl: "dash", best_lbl: "dash"}
    for valor, cor, nome in marcas:
        fig.add_vline(
            x=valor,
            line_color=cor,
            line_dash=dash[nome],
            line_width=2,
            annotation_text=f"{nome}: {fmt_rs(valor)}",
            annotation_position="top",
        )
    return fig


def figura_histograma_caixa_final(serie_cx: pd.Series, ano_enc: int, n_cenarios: int) -> go.Figure:
    counts, edges = np.histogram(serie_cx.dropna(), bins=40)
    centros = (edges[:-1] + edges[1:]) / 2
    cores_barras = [COR_VERMELHO if c < 0 else COR_SUAVE for c in centros]
    fig = go.Figure(
        data=[
            go.Bar(
                x=centros,
                y=counts / counts.sum() if counts.sum() else counts,
                marker_color=cores_barras,
                width=(edges[1] - edges[0]) * 0.92 if len(edges) > 1 else None,
                hovertemplate=t("chart.cash_hover"),
                name=t("chart.dist"),
            )
        ]
    )
    fig.add_vline(x=0, line_dash="dash", line_color=COR_VERMELHO, annotation_text=t("cmp.cfo.zero"))
    if not serie_cx.dropna().empty:
        fig.add_vline(x=float(serie_cx.median()), line_color=COR, annotation_text=t("chart.median"))
    fig.update_layout(
        title=t("dist.hist_title", ano=ano_enc, n=f"{n_cenarios:,}"),
        xaxis_title=t("dist.box_y"),
        yaxis_title=t("dist.prob_axis"),
        showlegend=False,
        bargap=0.05,
    )
    return fig
