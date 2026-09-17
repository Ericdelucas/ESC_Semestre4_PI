"""Componentes de gráfico reutilizáveis."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from src.config import COR, COR_ALERTA, COR_ANCORA, COR_OK, COR_SUAVE, COR_VERMELHO
from src.config.i18n import t
from src.data.analytics import resumo_envelope
from src.data.formatting import cena_rotulo, fmt_rs


def recorte_label(ano_sel: str | int) -> str:
    return t("filter.all") if ano_sel == "Todos" else t("filter.year_n", n=ano_sel)


def titulo_filtro(assunto: str, cena_sel: str, ano_sel: str | int) -> str:
    return f"{assunto} — {cena_rotulo(cena_sel)} | {recorte_label(ano_sel)}"


def serie_temporal_plotavel(dados: pd.DataFrame, y_cols: list[str]) -> pd.DataFrame:
    """Normaliza ano_num (Int64/NA) e remove linhas inválidas antes do Plotly."""
    faltando = [c for c in ["ano_num", *y_cols] if c not in dados.columns]
    if faltando:
        raise KeyError(f"Colunas ausentes para o gráfico: {faltando}")
    out = dados.loc[:, ["ano_num", *y_cols]].copy()
    out["ano_num"] = pd.to_numeric(out["ano_num"], errors="coerce")
    out = out.dropna(subset=["ano_num"]).sort_values("ano_num")
    out["ano_num"] = out["ano_num"].astype(int)
    for col in y_cols:
        out[col] = pd.to_numeric(out[col], errors="coerce")
    if out.empty:
        raise ValueError("Sem pontos válidos no horizonte para este cenário/recorte.")
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
    fig.add_vline(
        x=ano,
        line_dash="dash",
        line_color=COR_ANCORA,
        line_width=2,
        annotation_text=t("chart.filter", ano=ano),
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
                name=t("chart.anchor", ano=ano),
                showlegend=primeira,
                hovertemplate=f"{t('chart.year')} {ano}: %{{y}}<extra></extra>",
            )
        )
        primeira = False
    return fig


def figura_envelope(
    ind: pd.DataFrame,
    coluna: str,
    rotulo: str,
    maior_e_melhor: bool,
    *,
    titulo: str | None = None,
    ano_destaque: int | None = None,
    cena_destaque: str | None = None,
) -> go.Figure:
    env = resumo_envelope(ind, coluna, maior_e_melhor)
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=ind["ano_num"],
            y=ind[coluna],
            mode="markers",
            marker={"size": 5, "color": COR_SUAVE, "opacity": 0.07},
            name=t("chart.all"),
            hoverinfo="skip",
        )
    )
    fig.add_trace(go.Scatter(x=env["ano_num"], y=env["p95"], mode="lines", line={"width": 0}, showlegend=False, hoverinfo="skip"))
    fig.add_trace(
        go.Scatter(
            x=env["ano_num"],
            y=env["p5"],
            mode="lines",
            line={"width": 0},
            fill="tonexty",
            fillcolor="rgba(31, 78, 69, 0.18)",
            name=t("chart.band"),
            hoverinfo="skip",
        )
    )
    fig.add_trace(go.Scatter(x=env["ano_num"], y=env["mediana"], mode="lines+markers", line={"color": COR, "width": 3}, name=t("chart.median")))
    fig.add_trace(go.Scatter(x=env["ano_num"], y=env["media"], mode="lines", line={"color": COR, "width": 1.5, "dash": "dot"}, name=t("chart.mean")))
    fig.add_trace(go.Scatter(x=env["ano_num"], y=env["pessimista"], mode="lines+markers", line={"color": COR_ALERTA, "width": 2}, name=t("chart.pessimistic")))
    fig.add_trace(go.Scatter(x=env["ano_num"], y=env["otimista"], mode="lines+markers", line={"color": COR_OK, "width": 2}, name=t("chart.optimistic")))
    fig.update_layout(
        title=titulo or f"Faixa de risco — {rotulo} nos 12 anos ({ind['CENA'].nunique():,} cenários)",
        xaxis_title=t("chart.year"),
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
            annotation_text=t("chart.filter", ano=ano_destaque),
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
                        name=f"{cena_rotulo(cena_destaque)} | {t('chart.anchor', ano=ano_destaque)}",
                        hovertemplate=f"{cena_rotulo(cena_destaque)}<br>{t('chart.year')} {ano_destaque}: %{{y}}<extra></extra>",
                    )
                )
    return fig


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
        title=titulo or f"Distribuição de {rotulo} no Ano {ano} ({len(serie):,} cenários)",
        labels={coluna: rotulo, "probability": t("dist.prob_axis")},
    )
    fig.update_layout(yaxis_title=t("chart.probability"), bargap=0.05)
    if serie.empty:
        return fig
    marcas = [
        (float(serie.median()), COR, t("chart.median")),
        (float(serie.mean()), COR, t("chart.mean")),
        (float(serie.min()), COR_ALERTA, t("chart.worst")),
        (float(serie.max()), COR_OK, t("chart.best")),
    ]
    dash = {t("chart.median"): "solid", t("chart.mean"): "dot", t("chart.worst"): "dash", t("chart.best"): "dash"}
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
    import numpy as np

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
                hovertemplate=t("metric.cash_available") + " %{x}<br>" + t("dist.prob_axis") + " %{y:.2%}<extra></extra>",
                name=t("nav.distribuicao"),
            )
        ]
    )
    fig.add_vline(x=0, line_dash="dash", line_color=COR_VERMELHO, annotation_text="Zero")
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
