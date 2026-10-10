"""Helpers de series temporais para Plotly."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

from src.config import COR_ANCORA
from src.config.i18n import t
from src.models.formatting import cena_rotulo


def recorte_label(ano_sel: str | int) -> str:
    return t("filter.all") if ano_sel == "Todos" else t("filter.year_n", n=ano_sel)


def titulo_filtro(assunto: str, cena_sel: str, ano_sel: str | int) -> str:
    return f"{assunto} — {cena_rotulo(cena_sel)} | {recorte_label(ano_sel)}"


def serie_temporal_plotavel(dados: pd.DataFrame, y_cols: list[str]) -> pd.DataFrame:
    """Normaliza ano_num (Int64/NA) e remove linhas invalidas antes do Plotly."""
    faltando = [c for c in ["ano_num", *y_cols] if c not in dados.columns]
    if faltando:
        raise KeyError(t("chart.missing_cols", cols=faltando))
    out = dados.loc[:, ["ano_num", *y_cols]].copy()
    out["ano_num"] = pd.to_numeric(out["ano_num"], errors="coerce")
    out = out.dropna(subset=["ano_num"]).sort_values("ano_num")
    out["ano_num"] = out["ano_num"].astype(int)
    for col in y_cols:
        out[col] = pd.to_numeric(out[col], errors="coerce")
    if out.empty:
        raise ValueError(t("chart.no_points"))
    return out


def ancorar_ano_temporal(
    fig: go.Figure,
    dados: pd.DataFrame,
    y_cols: list[str],
    ano_sel: str | int,
) -> go.Figure:
    if ano_sel == "Todos":
        return fig
    ano = int(ano_sel)
    year_label = t("filter.year_n", n=ano)
    fig.add_vline(
        x=ano,
        line_dash="dash",
        line_color=COR_ANCORA,
        line_width=2,
        annotation_text=t("chart.filter_year", label=year_label),
        annotation_position="top",
        annotation_font={"color": COR_ANCORA, "size": 12},
    )
    ponto = dados.loc[dados["ano_num"] == ano]
    if ponto.empty:
        return fig
    primeira = True
    for col in y_cols:
        fig.add_trace(
            go.Scatter(
                x=ponto["ano_num"],
                y=ponto[col],
                mode="markers",
                marker={
                    "size": 16,
                    "color": COR_ANCORA,
                    "symbol": "diamond",
                    "line": {"width": 2, "color": "#111111"},
                },
                name=t("chart.anchor_name", label=year_label),
                showlegend=primeira,
                hovertemplate=f"{col}<br>{year_label}: %{{y}}<extra></extra>",
            )
        )
        primeira = False
    return fig
