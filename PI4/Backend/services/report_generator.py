"""Geracao de relatorio executivo em PDF."""

from __future__ import annotations

from datetime import datetime
from io import BytesIO
from pathlib import Path
import subprocess
import sys
import tempfile
from typing import Any
from xml.sax.saxutils import escape

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    Image,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from Backend.metrics import calculate_ltv_cac, summarize_ltv_cac
from Backend.metrics.column_resolver import series_by_alias
from Backend.metrics.financial_kpis import build_break_even, build_dre


PAGE_WIDTH, PAGE_HEIGHT = A4
ESC_BLUE = colors.HexColor("#1F4E79")
GRAPHITE = colors.HexColor("#161B26")
LIGHT_GREY = colors.HexColor("#F3F5F8")
_KALEIDO_AVAILABLE: bool | None = None


def _money(value: float | int | None) -> str:
    if value is None or pd.isna(value):
        return "-"
    return f"R$ {float(value):,.2f}".replace(",", "_").replace(".", ",").replace("_", ".")


def _pct(value: float | int | None) -> str:
    if value is None or pd.isna(value):
        return "-"
    return f"{float(value) * 100:.1f}%".replace(".", ",")


def _clean_text(value: str) -> str:
    return escape(str(value)).replace("\n", "<br/>")


def _series(df: pd.DataFrame, *aliases: str) -> pd.Series:
    return series_by_alias(df, aliases)


def _styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "ESCReportTitle",
            parent=base["Title"],
            fontName="Helvetica-Bold",
            fontSize=18,
            leading=22,
            textColor=GRAPHITE,
            spaceAfter=12,
        ),
        "h2": ParagraphStyle(
            "ESCReportH2",
            parent=base["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=12,
            leading=15,
            textColor=ESC_BLUE,
            spaceBefore=10,
            spaceAfter=6,
        ),
        "body": ParagraphStyle(
            "ESCReportBody",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=9,
            leading=13,
            textColor=colors.HexColor("#222222"),
            spaceAfter=7,
        ),
        "center": ParagraphStyle(
            "ESCReportCenter",
            parent=base["BodyText"],
            alignment=TA_CENTER,
            fontName="Helvetica-Bold",
            fontSize=9,
            leading=11,
        ),
    }


def _header_footer(canvas, doc) -> None:
    canvas.saveState()
    canvas.setStrokeColor(colors.HexColor("#D6DAE0"))
    canvas.line(1.6 * cm, PAGE_HEIGHT - 1.35 * cm, PAGE_WIDTH - 1.6 * cm, PAGE_HEIGHT - 1.35 * cm)
    canvas.setFont("Helvetica-Bold", 9)
    canvas.setFillColor(GRAPHITE)
    canvas.drawString(1.6 * cm, PAGE_HEIGHT - 1.05 * cm, "ESC | Relatorio Executivo")
    canvas.setFont("Helvetica", 8)
    canvas.drawRightString(PAGE_WIDTH - 1.6 * cm, PAGE_HEIGHT - 1.05 * cm, datetime.now().strftime("%d/%m/%Y %H:%M"))
    canvas.line(1.6 * cm, 1.2 * cm, PAGE_WIDTH - 1.6 * cm, 1.2 * cm)
    canvas.drawString(1.6 * cm, 0.8 * cm, "Dashboard CTI - Grupo ESC")
    canvas.drawRightString(PAGE_WIDTH - 1.6 * cm, 0.8 * cm, f"Pagina {doc.page}")
    canvas.restoreState()


def _esc_mark() -> Table:
    mark = Table([["ESC"]], colWidths=[1.55 * cm], rowHeights=[1.55 * cm])
    mark.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), ESC_BLUE),
                ("TEXTCOLOR", (0, 0), (-1, -1), colors.white),
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 14),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("BOX", (0, 0), (-1, -1), 0.25, ESC_BLUE),
            ]
        )
    )
    return mark


def _table(rows: list[list[Any]], widths: list[float] | None = None, *, highlight_labels: set[str] | None = None) -> Table:
    highlight_labels = highlight_labels or set()
    table = Table(rows, colWidths=widths, hAlign="LEFT")
    style_commands = [
        ("BACKGROUND", (0, 0), (-1, 0), GRAPHITE),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#D8DDE5")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]
    for row_idx in range(1, len(rows)):
        bg = colors.white if row_idx % 2 else LIGHT_GREY
        style_commands.append(("BACKGROUND", (0, row_idx), (-1, row_idx), bg))
        if rows[row_idx] and str(rows[row_idx][0]) in highlight_labels:
            style_commands.extend(
                [
                    ("FONTNAME", (0, row_idx), (-1, row_idx), "Helvetica-Bold"),
                    ("BACKGROUND", (0, row_idx), (-1, row_idx), colors.HexColor("#E8F1FA")),
                    ("TEXTCOLOR", (0, row_idx), (-1, row_idx), GRAPHITE),
                ]
            )
    table.setStyle(TableStyle(style_commands))
    return table


def _fig_to_image(fig: go.Figure, width: int = 840, height: int = 360):
    """Renderiza Plotly em PNG num subprocesso com timeout para evitar travas."""
    global _KALEIDO_AVAILABLE
    if _KALEIDO_AVAILABLE is False:
        return _fig_to_matplotlib_image(fig)
    with tempfile.TemporaryDirectory() as tmpdir:
        fig_path = Path(tmpdir) / "figure.json"
        png_path = Path(tmpdir) / "figure.png"
        fig_path.write_text(fig.to_json(), encoding="utf-8")
        code = (
            "from pathlib import Path; "
            "import plotly.io as pio; "
            "fig=pio.from_json(Path(r'%s').read_text(encoding='utf-8')); "
            "fig.write_image(r'%s', format='png', width=%d, height=%d, scale=2)"
            % (fig_path, png_path, width, height)
        )
        try:
            subprocess.run(
                [sys.executable, "-c", code],
                check=True,
                timeout=10,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except Exception:
            _KALEIDO_AVAILABLE = False
            return _fig_to_matplotlib_image(fig)
        if not png_path.exists():
            _KALEIDO_AVAILABLE = False
            return _fig_to_matplotlib_image(fig)
        _KALEIDO_AVAILABLE = True
        return Image(BytesIO(png_path.read_bytes()), width=16.5 * cm, height=7.1 * cm)


def _fig_to_matplotlib_image(fig: go.Figure):
    """Fallback local para PNG quando Kaleido trava/nao esta operacional."""
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception:
        return None

    data = fig.to_dict().get("data", [])
    if not data:
        return None
    layout = fig.to_dict().get("layout", {})
    title = layout.get("title", {}).get("text", "") if isinstance(layout.get("title"), dict) else layout.get("title", "")
    x_title = layout.get("xaxis", {}).get("title", {}).get("text", "")
    y_title = layout.get("yaxis", {}).get("title", {}).get("text", "")

    fig_mpl, ax = plt.subplots(figsize=(8.4, 3.6), dpi=160)
    ax.set_facecolor("#FFFFFF")
    fig_mpl.patch.set_facecolor("#FFFFFF")
    plotted = False
    for trace in data:
        x = trace.get("x", [])
        y = trace.get("y", [])
        name = trace.get("name") or ""
        if len(x) == 0 or len(y) == 0:
            continue
        trace_type = trace.get("type", "scatter")
        marker_color = trace.get("marker", {}).get("color", "#1F4E79")
        line_color = trace.get("line", {}).get("color", marker_color)
        if trace_type == "bar":
            ax.bar(x, y, label=name, color=marker_color, alpha=0.82)
        else:
            ax.plot(x, y, marker="o", linewidth=2.2, label=name, color=line_color)
        plotted = True
    if not plotted:
        plt.close(fig_mpl)
        return None
    ax.set_title(title or "Grafico", fontsize=10, fontweight="bold", color="#161B26")
    ax.set_xlabel(x_title or "")
    ax.set_ylabel(y_title or "")
    ax.grid(True, axis="y", alpha=0.25)
    if len(data) > 1:
        ax.legend(loc="best", fontsize=7)
    fig_mpl.tight_layout()
    buffer = BytesIO()
    fig_mpl.savefig(buffer, format="png", bbox_inches="tight")
    plt.close(fig_mpl)
    buffer.seek(0)
    return Image(buffer, width=16.5 * cm, height=7.1 * cm)


def _dre_figure(dre: pd.DataFrame) -> go.Figure:
    years = pd.to_numeric(dre["ano_num"], errors="coerce").astype(int)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=years, y=_series(dre, "Receita Líquida", "Receita Liquida"), mode="lines+markers", name="Receita Liquida"))
    fig.add_trace(go.Scatter(x=years, y=_series(dre, "EBITDA"), mode="lines+markers", name="EBITDA"))
    fig.update_layout(template="plotly_white", title="Receita Liquida vs EBITDA", xaxis_title="Ano", yaxis_title="R$")
    fig.update_xaxes(tickmode="linear", tick0=1, dtick=1)
    return fig


def _break_even_figure(be_df: pd.DataFrame) -> go.Figure:
    be = float(_series(be_df, "Break-Even").mean())
    margem = float(_series(be_df, "Margem de Contribuição (%)", "Margem de Contribuicao (%)").mean())
    receita = float(_series(be_df, "Receita Líquida", "Receita Liquida").mean())
    margem = 0.0 if pd.isna(margem) else margem
    be = 0.0 if pd.isna(be) else be
    receita = 0.0 if pd.isna(receita) else receita
    custo_fixo = be * margem
    eixo = pd.Series([0.0, be, max(receita, be * 1.15)]).drop_duplicates().sort_values()
    chart = pd.DataFrame({"Receita": eixo})
    chart["Receita Total"] = chart["Receita"]
    chart["Custos Totais"] = custo_fixo + chart["Receita"] * (1 - margem)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=chart["Receita"], y=chart["Receita Total"], mode="lines+markers", name="Receita Total"))
    fig.add_trace(go.Scatter(x=chart["Receita"], y=chart["Custos Totais"], mode="lines+markers", name="Custos Totais"))
    fig.add_vline(x=be, line_dash="dash", annotation_text=f"Break-Even {_money(be)}")
    fig.update_layout(template="plotly_white", title="Ponto de Equilibrio", xaxis_title="Receita", yaxis_title="R$")
    return fig


def _ltv_cac_figure(ltv: pd.DataFrame) -> go.Figure:
    years = pd.to_numeric(ltv["ano_num"], errors="coerce").astype(int)
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_bar(x=years, y=ltv["LTV"], name="LTV", marker_color="#1F4E79")
    fig.add_scatter(x=years, y=ltv["CAC"], name="CAC", mode="lines+markers", line={"color": "#A65D3F", "width": 3}, secondary_y=True)
    fig.update_layout(template="plotly_white", title="LTV vs CAC por Ano", xaxis_title="Ano")
    fig.update_xaxes(tickmode="linear", tick0=1, dtick=1)
    fig.update_yaxes(title_text="LTV (R$)", secondary_y=False)
    fig.update_yaxes(title_text="CAC (R$)", secondary_y=True)
    return fig


def _add_chart(story: list[Any], fig: go.Figure, styles: dict[str, ParagraphStyle], fallback: str) -> None:
    image = _fig_to_image(fig)
    if image is None:
        story.append(Paragraph(fallback, styles["body"]))
    else:
        story.append(image)
    story.append(Spacer(1, 0.25 * cm))


def generate_executive_pdf(
    df: pd.DataFrame,
    *,
    scenario: str,
    year_filter: str | int = "Todos",
    company_name: str = "Grupo ESC",
    notes: dict[str, str] | None = None,
) -> bytes:
    """Gera um relatorio executivo A4 em PDF."""
    notes = notes or {}
    styles = _styles()
    dre = build_dre(df, scenario)
    be_df = build_break_even(df, scenario)
    ltv = calculate_ltv_cac(df, scenario)
    ltv_summary = summarize_ltv_cac(df, scenario, year_filter)

    receita = float(_series(dre, "Receita Líquida", "Receita Liquida").mean()) if not dre.empty else 0.0
    ebitda = float(_series(dre, "EBITDA").mean()) if not dre.empty else 0.0
    margem_ebitda = ebitda / receita if receita else 0.0
    break_even = float(_series(be_df, "Break-Even").mean()) if not be_df.empty else 0.0

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=1.6 * cm,
        rightMargin=1.6 * cm,
        topMargin=1.7 * cm,
        bottomMargin=1.5 * cm,
        title="Relatorio Executivo ESC",
    )
    story: list[Any] = []

    story.append(Table([[_esc_mark(), Paragraph("Relatorio Executivo de Desempenho Financeiro", styles["title"])]], colWidths=[2 * cm, 14 * cm]))
    story.append(Paragraph(_clean_text(f"Empresa: {company_name} | Cenario: {scenario} | Recorte: {year_filter}"), styles["body"]))
    story.append(Spacer(1, 0.25 * cm))

    story.append(Paragraph("Resumo Executivo", styles["h2"]))
    story.append(Paragraph(_clean_text(notes.get("executive_summary") or "Este relatorio consolida os principais indicadores economico-financeiros do cenario selecionado, com foco em DRE, EBITDA, ponto de equilibrio e eficiencia comercial."), styles["body"]))
    story.append(
        _table(
            [
                ["Indicador", "Valor"],
                ["Receita Liquida Media", _money(receita)],
                ["EBITDA Medio", _money(ebitda)],
                ["Margem EBITDA", _pct(margem_ebitda)],
                ["Break-Even Medio", _money(break_even)],
                ["LTV/CAC Medio", f"{ltv_summary['ratio']:.1f}x"],
            ],
            [7 * cm, 6 * cm],
        )
    )

    story.append(Paragraph("Analise da DRE e EBITDA", styles["h2"]))
    story.append(Paragraph(_clean_text(notes.get("dre_analysis") or "A DRE evidencia a trajetoria de receita, custos e resultado operacional. A leitura do EBITDA permite avaliar geracao operacional antes de efeitos financeiros e nao caixa."), styles["body"]))
    if not dre.empty:
        _add_chart(story, _dre_figure(dre), styles, "Grafico DRE indisponivel: instale kaleido para renderizar Plotly em PNG.")

    story.append(PageBreak())
    story.append(Paragraph("Break-Even", styles["h2"]))
    story.append(Paragraph(_clean_text(notes.get("break_even") or "O ponto de equilibrio representa o faturamento minimo necessario para cobrir a estrutura de custos fixos e variaveis no recorte medio."), styles["body"]))
    if not be_df.empty:
        _add_chart(story, _break_even_figure(be_df), styles, "Grafico Break-Even indisponivel: instale kaleido para renderizar Plotly em PNG.")

    story.append(Paragraph("Eficiencia Comercial LTV/CAC", styles["h2"]))
    story.append(Paragraph(_clean_text(notes.get("ltv_cac") or "A relacao LTV/CAC compara o valor economico estimado por cliente com o custo medio de aquisicao, apoiando a leitura de eficiencia comercial."), styles["body"]))
    if not ltv.empty:
        _add_chart(story, _ltv_cac_figure(ltv), styles, "Grafico LTV/CAC indisponivel: instale kaleido para renderizar Plotly em PNG.")
        rows = [["Ano", "LTV", "CAC", "LTV/CAC"]]
        for _, row in ltv.head(12).iterrows():
            rows.append([int(row["ano_num"]), _money(row["LTV"]), _money(row["CAC"]), f"{float(row['LTV/CAC']):.1f}x"])
        story.append(_table(rows, [2 * cm, 4.2 * cm, 4.2 * cm, 3 * cm]))

    story.append(Paragraph("Parecer Analitico", styles["h2"]))
    story.append(Paragraph(_clean_text(notes.get("scenario_opinion") or "Parecer nao informado. Recomenda-se complementar a leitura com analise de sensibilidade e validacao dos totais de controle."), styles["body"]))

    doc.build(story, onFirstPage=_header_footer, onLaterPages=_header_footer)
    return buffer.getvalue()
