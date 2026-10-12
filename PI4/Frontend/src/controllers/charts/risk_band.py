"""Graficos de envelope/faixa de risco."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

from src.config import COR, COR_ALERTA, COR_ANCORA, COR_OK, COR_SUAVE
from src.config.i18n import t
from src.models.analytics import resumo_envelope


def envelope_series_labels() -> dict[str, str]:
    return {
        "all": t("faixa.series.all"),
        "band": t("faixa.series.band"),
        "median": t("faixa.series.median"),
        "mean": t("faixa.series.mean"),
        "pess": t("faixa.series.pess"),
        "opt": t("faixa.series.opt"),
    }


def default_envelope_visible() -> set[str]:
    labels = envelope_series_labels()
    return {labels["band"], labels["median"], labels["mean"], labels["pess"], labels["opt"]}


def figura_envelope(
    ind: pd.DataFrame,
    coluna: str,
    rotulo: str,
    maior_e_melhor: bool,
    *,
    titulo: str | None = None,
    ano_destaque: int | None = None,
    cena_destaque: str | None = None,
    series_visiveis: set[str] | None = None,
) -> go.Figure:
    env = resumo_envelope(ind, coluna, maior_e_melhor)
    labels = envelope_series_labels()
    visible = series_visiveis or default_envelope_visible()
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=ind["ano_num"],
            y=ind[coluna],
            mode="markers",
            marker={"size": 5, "color": COR_SUAVE, "opacity": 0.07},
            name=labels["all"],
            hoverinfo="skip",
        )
    )
    if labels["band"] in visible:
        fig.add_trace(go.Scatter(x=env["ano_num"], y=env["p95"], mode="lines", line={"width": 0}, showlegend=False, hoverinfo="skip"))
        fig.add_trace(
            go.Scatter(
                x=env["ano_num"],
                y=env["p5"],
                mode="lines",
                line={"width": 0},
                fill="tonexty",
                fillcolor="rgba(31, 78, 69, 0.18)",
                name=labels["band"],
                hoverinfo="skip",
            )
        )
    if labels["median"] in visible:
        fig.add_trace(go.Scatter(x=env["ano_num"], y=env["mediana"], mode="lines+markers", line={"color": COR, "width": 3}, name=labels["median"]))
    if labels["mean"] in visible:
        fig.add_trace(go.Scatter(x=env["ano_num"], y=env["media"], mode="lines", line={"color": COR, "width": 1.5, "dash": "dot"}, name=labels["mean"]))
    if labels["pess"] in visible:
        fig.add_trace(go.Scatter(x=env["ano_num"], y=env["pessimista"], mode="lines+markers", line={"color": COR_ALERTA, "width": 2}, name=labels["pess"]))
    if labels["opt"] in visible:
        fig.add_trace(go.Scatter(x=env["ano_num"], y=env["otimista"], mode="lines+markers", line={"color": COR_OK, "width": 2}, name=labels["opt"]))
    fig.update_layout(
        title=titulo or t("faixa.fallback_title", metric=rotulo, n=f"{ind['CENA'].nunique():,}"),
        xaxis_title=t("chart.year"),
        yaxis_title=rotulo,
        hovermode="x unified",
        legend_title_text="",
    )
    if ano_destaque is not None:
        year_label = t("filter.year_n", n=ano_destaque)
        fig.add_vline(
            x=ano_destaque,
            line_dash="dash",
            line_color=COR_ANCORA,
            line_width=2,
            annotation_text=t("chart.filter_year", label=year_label),
            annotation_position="top",
            annotation_font={"color": COR_ANCORA, "size": 12},
        )
        if cena_destaque is not None:
            ancora = ind.loc[(ind["CENA"] == cena_destaque) & (ind["ano_num"] == ano_destaque)]
            if not ancora.empty:
                fig.add_trace(
                    go.Scatter(
                        x=ancora["ano_num"],
                        y=ancora[coluna],
                        mode="markers",
                        marker={"size": 16, "color": COR_ANCORA, "symbol": "diamond", "line": {"width": 2, "color": "#111111"}},
                        name=t("faixa.anchor", cena=cena_destaque, label=year_label),
                        hovertemplate=f"{cena_destaque}<br>{year_label}: %{{y}}<extra></extra>",
                    )
                )
    return fig
