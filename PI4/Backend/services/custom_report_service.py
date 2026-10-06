"""Servico de relatorio executivo customizavel por blocos."""

from __future__ import annotations

from datetime import datetime
from io import BytesIO
from typing import Any

import pandas as pd
import plotly.graph_objects as go
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from Backend.metrics import calculate_ltv_cac, summarize_ltv_cac
from Backend.metrics.financial_kpis import build_break_even, build_dre
from Backend.services.report_generator import (
    GRAPHITE,
    _add_chart,
    _break_even_figure,
    _clean_text,
    _dre_figure,
    _esc_mark,
    _ltv_cac_figure,
    _money,
    _pct,
    _series,
    _styles,
    _table,
)


BLOCKS: dict[str, str] = {
    "cover": "Bloco 1: Capa & Resumo Executivo",
    "financial_dre": "Bloco 2: Visao Financeira & DRE",
    "break_even": "Bloco 3: Ponto de Equilibrio & Margens",
    "commercial": "Bloco 4: Eficiencia Comercial",
    "operational_tech": "Bloco 5: Visao Operacional & Tech",
    "scenario_comparison": "Bloco 6: Comparativo de Cenarios",
}


class NumberedCanvas(Canvas):
    """Canvas com rodape Pagina X de Y."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states: list[dict[str, Any]] = []

    def showPage(self) -> None:  # noqa: N802 - API ReportLab
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self) -> None:
        page_count = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self._draw_page_number(page_count)
            super().showPage()
        super().save()

    def _draw_page_number(self, page_count: int) -> None:
        width, _height = A4
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#4B5563"))
        self.drawString(1.6 * cm, 0.8 * cm, "Grupo ESC | Relatorio Executivo")
        self.drawRightString(width - 1.6 * cm, 0.8 * cm, f"Pagina {self._pageNumber} de {page_count}")
        self.restoreState()


def block_options() -> dict[str, str]:
    """Retorna blocos disponiveis para o builder."""
    return BLOCKS.copy()


def _safe_mean(series: pd.Series) -> float:
    value = pd.to_numeric(series, errors="coerce").mean()
    return 0.0 if pd.isna(value) else float(value)


def _metric_mean(df: pd.DataFrame, *aliases: str) -> float:
    return _safe_mean(_series(df, *aliases)) if not df.empty else 0.0


def _net_income_mean(dre: pd.DataFrame) -> float:
    """Evita Lucro Liquido zerado quando a conta consolidada vem ausente."""
    if dre.empty:
        return 0.0
    lucro = _series(dre, "Lucro Liquido", "Lucro Liquido")
    if pd.to_numeric(lucro, errors="coerce").abs().sum() > 0:
        return _safe_mean(lucro)
    ebt = _series(dre, "EBT")
    if pd.to_numeric(ebt, errors="coerce").abs().sum() > 0:
        return _safe_mean(ebt + _series(dre, "Imposto de Renda", "IR/CS"))
    return _safe_mean(_series(dre, "EBIT") + _series(dre, "Resultado Financeiro"))


def _normalize_selected_blocks(selected_blocks: list[str]) -> list[str]:
    """Aceita ids tecnicos ou labels visuais sem perder blocos selecionados."""
    label_to_key = {label: key for key, label in BLOCKS.items()}
    normalized: list[str] = []
    for block in selected_blocks:
        key = block if block in BLOCKS else label_to_key.get(block)
        if key and key not in normalized:
            normalized.append(key)
    return normalized


def _kpi_callouts(df: pd.DataFrame, scenario: str) -> Table:
    """Monta callout boxes executivos para a primeira pagina."""
    dre = build_dre(df, scenario)
    be_df = build_break_even(df, scenario)
    ltv_summary = summarize_ltv_cac(df, scenario)
    receita = _metric_mean(dre, "Receita Liquida", "Receita LÃ­quida")
    ebitda = _metric_mean(dre, "EBITDA")
    margem = ebitda / receita if receita else 0.0
    break_even = _metric_mean(be_df, "Break-Even")
    table = Table(
        [
            ["EBITDA", "Margem EBITDA", "Break-Even", "LTV/CAC"],
            [_money(ebitda), _pct(margem), _money(break_even), f"{ltv_summary['ratio']:.1f}x"],
        ],
        colWidths=[3.9 * cm, 3.9 * cm, 3.9 * cm, 3.9 * cm],
        hAlign="LEFT",
    )
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#EAF2FB")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#1F4E79")),
                ("TEXTCOLOR", (0, 1), (-1, 1), GRAPHITE),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTNAME", (0, 1), (-1, 1), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 8),
                ("FONTSIZE", (0, 1), (-1, 1), 13),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("BOX", (0, 0), (-1, -1), 0.35, colors.HexColor("#BCD4EB")),
                ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#BCD4EB")),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    return table


def default_block_notes(df: pd.DataFrame, scenario: str) -> dict[str, str]:
    """Gera sugestoes iniciais de parecer por bloco a partir dos dados."""
    dre = build_dre(df, scenario)
    be_df = build_break_even(df, scenario)
    ltv_summary = summarize_ltv_cac(df, scenario)
    receita = _metric_mean(dre, "Receita Liquida", "Receita LÃ­quida")
    ebitda = _metric_mean(dre, "EBITDA")
    margem = ebitda / receita if receita else 0.0
    break_even = _metric_mean(be_df, "Break-Even")
    return {
        "cover": (
            f"O cenario {scenario} apresenta receita media de {_money(receita)}, EBITDA medio de "
            f"{_money(ebitda)} e margem EBITDA de {_pct(margem)}. O relatorio consolida os pontos "
            "mais relevantes para tomada de decisao executiva."
        ),
        "financial_dre": (
            "A visao financeira destaca a relacao entre receita liquida, estrutura de custos e EBITDA, "
            "permitindo avaliar a consistencia da geracao operacional ao longo do horizonte."
        ),
        "break_even": (
            f"O ponto de equilibrio medio estimado e {_money(break_even)}. A leitura deve ser feita em "
            "conjunto com margem de contribuicao, custos fixos e sensibilidade de demanda."
        ),
        "commercial": (
            f"A eficiencia comercial media medida por LTV/CAC e {ltv_summary['ratio']:.1f}x, "
            "indicando a relacao entre valor economico estimado por cliente e custo de aquisicao."
        ),
        "operational_tech": (
            "A visao operacional e tecnologica observa CapEx, OpEx e composicao de custos, com foco em "
            "sustentabilidade de infraestrutura, escalabilidade e pressao de investimentos."
        ),
        "scenario_comparison": (
            "O comparativo de cenarios permite avaliar resiliencia relativa, dispersao dos resultados e "
            "possiveis pontos de estresse para deliberacao C-Level."
        ),
    }


def _cover_block(story: list[Any], meta: dict[str, Any], text: str) -> None:
    styles = _styles()
    story.append(_esc_mark())
    story.append(Spacer(1, 0.25 * cm))
    story.append(Paragraph("Relatorio Executivo Personalizado", styles["title"]))
    story.append(
        _table(
            [
                ["Campo", "Valor"],
                ["Empresa", meta["company_name"]],
                ["Perfil", meta["profile"]],
                ["Cenario", meta["scenario"]],
                ["Autor", meta["author"]],
                ["Emissao", datetime.now().strftime("%d/%m/%Y %H:%M")],
            ],
            [4.5 * cm, 9 * cm],
        )
    )
    story.append(Spacer(1, 0.35 * cm))
    story.append(Paragraph("Resumo Executivo", styles["h2"]))
    story.append(Paragraph(_clean_text(text), styles["body"]))


def _financial_block(story: list[Any], df: pd.DataFrame, scenario: str, text: str) -> None:
    styles = _styles()
    dre = build_dre(df, scenario)
    story.append(Paragraph("Visao Financeira & DRE", styles["h2"]))
    story.append(Paragraph(_clean_text(text), styles["body"]))
    if dre.empty:
        story.append(Paragraph("Sem dados de DRE para o cenario selecionado.", styles["body"]))
        return
    rows = [
        ["Metrica", "Media"],
        ["Receita Liquida", _money(_metric_mean(dre, "Receita Liquida", "Receita LÃ­quida"))],
        ["EBITDA", _money(_metric_mean(dre, "EBITDA"))],
        ["EBIT", _money(_metric_mean(dre, "EBIT"))],
        ["Lucro Liquido", _money(_net_income_mean(dre))],
    ]
    story.append(_table(rows, [6 * cm, 5 * cm], highlight_labels={"Receita Liquida", "EBITDA"}))
    _add_chart(story, _dre_figure(dre), styles, "Grafico DRE indisponivel: renderizacao Plotly/Kaleido excedeu o timeout.")


def _break_even_block(story: list[Any], df: pd.DataFrame, scenario: str, text: str) -> None:
    styles = _styles()
    be_df = build_break_even(df, scenario)
    story.append(Paragraph("Ponto de Equilibrio & Margens", styles["h2"]))
    story.append(Paragraph(_clean_text(text), styles["body"]))
    if be_df.empty:
        story.append(Paragraph("Sem dados suficientes para Break-Even.", styles["body"]))
        return
    rows = [
        ["Indicador", "Media"],
        ["Break-Even", _money(_metric_mean(be_df, "Break-Even"))],
        ["Margem de Contribuicao", _pct(_metric_mean(be_df, "Margem de Contribuicao (%)", "Margem de ContribuiÃ§Ã£o (%)"))],
        ["Margem de Seguranca", _pct(_metric_mean(be_df, "Margem de Seguranca (%)", "Margem de SeguranÃ§a (%)"))],
    ]
    story.append(_table(rows, [6 * cm, 5 * cm], highlight_labels={"Break-Even"}))
    _add_chart(story, _break_even_figure(be_df), styles, "Grafico Break-Even indisponivel: renderizacao Plotly/Kaleido excedeu o timeout.")


def _commercial_block(story: list[Any], df: pd.DataFrame, scenario: str, text: str) -> None:
    styles = _styles()
    ltv = calculate_ltv_cac(df, scenario)
    story.append(Paragraph("Eficiencia Comercial", styles["h2"]))
    story.append(Paragraph(_clean_text(text), styles["body"]))
    if ltv.empty:
        story.append(Paragraph("Sem dados suficientes para LTV/CAC.", styles["body"]))
        return
    rows = [["Ano", "LTV", "CAC", "LTV/CAC"]]
    for _, row in ltv.head(12).iterrows():
        rows.append([int(row["ano_num"]), _money(row["LTV"]), _money(row["CAC"]), f"{float(row['LTV/CAC']):.1f}x"])
    story.append(_table(rows, [2 * cm, 4.2 * cm, 4.2 * cm, 3 * cm]))
    _add_chart(story, _ltv_cac_figure(ltv), styles, "Grafico LTV/CAC indisponivel: renderizacao Plotly/Kaleido excedeu o timeout.")


def _operational_block(story: list[Any], df: pd.DataFrame, scenario: str, text: str) -> None:
    styles = _styles()
    rows_df = df.loc[df["CENA"].astype(str) == str(scenario)].copy() if "CENA" in df.columns else df.iloc[0:0]
    story.append(Paragraph("Visao Operacional & Tech", styles["h2"]))
    story.append(Paragraph(_clean_text(text), styles["body"]))
    if rows_df.empty:
        story.append(Paragraph("Sem dados operacionais para o cenario selecionado.", styles["body"]))
        return
    rows_df["VALOR"] = pd.to_numeric(rows_df["VALOR"], errors="coerce").fillna(0)
    mask = rows_df["CONTA"].astype(str).str.contains(
        "Custos|Investimentos|OPEX|CAPEX|Deprecia|Depreciacao|Amortiza",
        case=False,
        na=False,
    )
    costs = rows_df[mask]
    if costs.empty:
        costs = rows_df
    summary = costs.groupby("CONTA", as_index=False)["VALOR"].sum().sort_values("VALOR", key=lambda s: s.abs(), ascending=False).head(8)
    rows = [["Conta", "Total"]]
    rows.extend([[str(row["CONTA"]), _money(float(row["VALOR"]))] for _, row in summary.iterrows()])
    story.append(_table(rows, [9 * cm, 4.5 * cm]))


def _comparison_block(story: list[Any], df: pd.DataFrame, scenario: str, comparison_scenarios: list[str], text: str) -> None:
    styles = _styles()
    story.append(Paragraph("Comparativo de Cenarios", styles["h2"]))
    story.append(Paragraph(_clean_text(text), styles["body"]))
    scenarios = [scenario, *[s for s in comparison_scenarios if s != scenario]][:4]
    rows = [["Cenario", "Receita Media", "EBITDA Medio", "Break-Even Medio"]]
    fig = go.Figure()
    for item in scenarios:
        dre = build_dre(df, item)
        be_df = build_break_even(df, item)
        receita = _metric_mean(dre, "Receita Liquida", "Receita LÃ­quida")
        ebitda = _metric_mean(dre, "EBITDA")
        be = _metric_mean(be_df, "Break-Even")
        rows.append([item, _money(receita), _money(ebitda), _money(be)])
        if not dre.empty:
            fig.add_trace(go.Scatter(x=dre["ano_num"], y=_series(dre, "EBITDA"), mode="lines+markers", name=item))
    story.append(_table(rows, [4 * cm, 3.5 * cm, 3.5 * cm, 3.5 * cm], highlight_labels={scenario}))
    if fig.data:
        fig.update_layout(template="plotly_white", title="EBITDA por cenario", xaxis_title="Ano", yaxis_title="R$")
        fig.update_xaxes(tickmode="linear", tick0=1, dtick=1)
        _add_chart(story, fig, styles, "Grafico comparativo indisponivel: renderizacao Plotly/Kaleido excedeu o timeout.")


def generate_custom_report_pdf(
    df: pd.DataFrame,
    *,
    scenario: str,
    selected_blocks: list[str],
    notes: dict[str, str],
    author: str,
    profile: str,
    company_name: str = "Grupo ESC",
    comparison_scenarios: list[str] | None = None,
) -> bytes:
    """Gera PDF personalizado apenas com blocos escolhidos."""
    selected_blocks = _normalize_selected_blocks(selected_blocks)
    styles = _styles()
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=1.6 * cm,
        rightMargin=1.6 * cm,
        topMargin=1.5 * cm,
        bottomMargin=1.4 * cm,
        title="Relatorio Executivo Personalizado ESC",
    )
    meta = {
        "company_name": company_name,
        "profile": profile,
        "scenario": scenario,
        "author": author,
    }
    story: list[Any] = [
        Paragraph("Grupo ESC", styles["h2"]),
        Paragraph("Relatorio corporativo em layout A4, gerado por blocos selecionados pelo usuario.", styles["body"]),
        _kpi_callouts(df, scenario),
        Spacer(1, 0.35 * cm),
    ]

    block_renderers = {
        "cover": lambda: _cover_block(story, meta, notes.get("cover", "")),
        "financial_dre": lambda: _financial_block(story, df, scenario, notes.get("financial_dre", "")),
        "break_even": lambda: _break_even_block(story, df, scenario, notes.get("break_even", "")),
        "commercial": lambda: _commercial_block(story, df, scenario, notes.get("commercial", "")),
        "operational_tech": lambda: _operational_block(story, df, scenario, notes.get("operational_tech", "")),
        "scenario_comparison": lambda: _comparison_block(
            story,
            df,
            scenario,
            comparison_scenarios or [],
            notes.get("scenario_comparison", ""),
        ),
    }
    rendered_count = 0
    for block in selected_blocks:
        renderer = block_renderers.get(block)
        if renderer is None:
            continue
        if rendered_count > 0:
            story.append(PageBreak())
        renderer()
        rendered_count += 1
        story.append(Spacer(1, 0.25 * cm))

    if rendered_count == 0:
        story.append(Paragraph("Nenhum bloco valido foi selecionado para o relatorio.", styles["body"]))

    doc.build(story, canvasmaker=NumberedCanvas)
    return buffer.getvalue()
