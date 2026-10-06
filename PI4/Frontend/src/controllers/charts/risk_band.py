"""Graficos de envelope/faixa de risco."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

from src.config import COR, COR_ALERTA, COR_ANCORA, COR_OK, COR_SUAVE
from src.models.analytics import resumo_envelope


DEFAULT_ENVELOPE_SERIES = {
    "Otimista (melhor caso)",
    "Pessimista (pior caso)",
    "Média",
    "Mais provável (mediana)",
    "Faixa 5-95%",
}


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
    visible = series_visiveis or DEFAULT_ENVELOPE_SERIES
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=ind["ano_num"],
            y=ind[coluna],
            mode="markers",
            marker={"size": 5, "color": COR_SUAVE, "opacity": 0.07},
            name="Todos os cenários",
            hoverinfo="skip",
        )
    )
    if "Faixa 5-95%" in visible:
        fig.add_trace(go.Scatter(x=env["ano_num"], y=env["p95"], mode="lines", line={"width": 0}, showlegend=False, hoverinfo="skip"))
        fig.add_trace(
            go.Scatter(
                x=env["ano_num"],
                y=env["p5"],
                mode="lines",
                line={"width": 0},
                fill="tonexty",
                fillcolor="rgba(31, 78, 69, 0.18)",
                name="Faixa 5-95%",
                hoverinfo="skip",
            )
        )
    if "Mais provável (mediana)" in visible:
        fig.add_trace(go.Scatter(x=env["ano_num"], y=env["mediana"], mode="lines+markers", line={"color": COR, "width": 3}, name="Mais provável (mediana)"))
    if "Média" in visible:
        fig.add_trace(go.Scatter(x=env["ano_num"], y=env["media"], mode="lines", line={"color": COR, "width": 1.5, "dash": "dot"}, name="Média"))
    if "Pessimista (pior caso)" in visible:
        fig.add_trace(go.Scatter(x=env["ano_num"], y=env["pessimista"], mode="lines+markers", line={"color": COR_ALERTA, "width": 2}, name="Pessimista (pior caso)"))
    if "Otimista (melhor caso)" in visible:
        fig.add_trace(go.Scatter(x=env["ano_num"], y=env["otimista"], mode="lines+markers", line={"color": COR_OK, "width": 2}, name="Otimista (melhor caso)"))
    fig.update_layout(
        title=titulo or f"Faixa de risco - {rotulo} nos 12 anos ({ind['CENA'].nunique():,} cenários)",
        xaxis_title="Ano",
        yaxis_title=rotulo,
        hovermode="x unified",
        legend_title_text="",
    )
    if ano_destaque is not None:
        fig.add_vline(
            x=ano_destaque,
            line_dash="dash",
            line_color=COR_ANCORA,
            line_width=2,
            annotation_text=f"Filtro: Ano {ano_destaque}",
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
                        name=f"Âncora · {cena_destaque} · Ano {ano_destaque}",
                        hovertemplate=f"{cena_destaque}<br>Ano {ano_destaque}: %{{y}}<extra></extra>",
                    )
                )
    return fig
