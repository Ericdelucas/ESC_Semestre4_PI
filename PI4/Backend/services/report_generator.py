"""Geracao de relatorio executivo em PDF (padrao C-Level)."""

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
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import (
    CondPageBreak,
    Flowable,
    Image,
    KeepTogether,
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
NAVY = colors.HexColor("#0A192F")
NAVY_MID = colors.HexColor("#1E3A8A")
SLATE = colors.HexColor("#334155")
GOLD = colors.HexColor("#D97706")
ICE = colors.HexColor("#F8FAFC")
ZEBRA = colors.HexColor("#F1F5F9")
LINE = colors.HexColor("#CBD5E1")
WHITE = colors.white
GRAPHITE = SLATE
ESC_BLUE = NAVY_MID
LIGHT_GREY = ZEBRA
CHART_NAVY = "#0A192F"
CHART_GOLD = "#D97706"
CHART_BLUE = "#93C5FD"
CHART_ICE = "#F8FAFC"
_KALEIDO_AVAILABLE: bool | None = None
_FONTS_READY = False
FONT_SANS = "Helvetica"
FONT_SANS_BOLD = "Helvetica-Bold"
FONT_SERIF = "Helvetica-Bold"


def _register_fonts() -> None:
    global _FONTS_READY, FONT_SANS, FONT_SANS_BOLD, FONT_SERIF
    if _FONTS_READY:
        return
    windir = Path(os_fonts_dir())
    mapping = (
        ("ESCSans", FONT_SANS, ("calibri.ttf", "Calibri.ttf", "arial.ttf", "Arial.ttf")),
        ("ESCSans-Bold", FONT_SANS_BOLD, ("calibrib.ttf", "Calibri-Bold.ttf", "arialbd.ttf", "Arialbd.ttf")),
        ("ESCSerif", FONT_SERIF, ("georgia.ttf", "Georgia.ttf", "times.ttf", "timesbd.ttf")),
    )
    registered: dict[str, str] = {}
    for name, fallback, files in mapping:
        path = next((windir / file for file in files if (windir / file).is_file()), None)
        if path is None:
            registered[name] = fallback
            continue
        try:
            pdfmetrics.registerFont(TTFont(name, str(path)))
            registered[name] = name
        except Exception:
            registered[name] = fallback
    FONT_SANS = registered["ESCSans"]
    FONT_SANS_BOLD = registered["ESCSans-Bold"]
    FONT_SERIF = registered["ESCSerif"]
    _FONTS_READY = True


def os_fonts_dir() -> str:
    win = Path(r"C:\Windows\Fonts")
    if win.is_dir():
        return str(win)
    return "/usr/share/fonts/truetype"


def format_exec_money(value: float | int | None) -> str:
    """Formata valores monetarios em mi/bi sem notacao cientifica."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return "—"
    numero = float(value)
    sinal = "-" if numero < 0 else ""
    absoluto = abs(numero)
    if absoluto >= 1_000_000_000:
        corpo, sufixo = absoluto / 1_000_000_000, " bi"
    elif absoluto >= 1_000_000:
        corpo, sufixo = absoluto / 1_000_000, " mi"
    else:
        corpo, sufixo = absoluto, ""
    casas = 2 if sufixo or absoluto < 1000 else 2
    texto = f"{corpo:,.{casas}f}".replace(",", "_").replace(".", ",").replace("_", ".")
    return f"{sinal}R$ {texto}{sufixo}"


def format_exec_pct(value: float | int | None) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return "—"
    return f"{float(value) * 100:.1f}%".replace(".", ",")


def _money(value: float | int | None) -> str:
    return format_exec_money(value)


def _pct(value: float | int | None) -> str:
    return format_exec_pct(value)


def _clean_text(value: str) -> str:
    return escape(str(value)).replace("\n", "<br/>")


def _series(df: pd.DataFrame, *aliases: str) -> pd.Series:
    return series_by_alias(df, aliases)


def _scale_values(values: list[float] | pd.Series) -> tuple[list[float], str, str]:
    serie = [float(v) for v in pd.to_numeric(pd.Series(values), errors="coerce").fillna(0).tolist()]
    pico = max((abs(v) for v in serie), default=0.0)
    if pico >= 1_000_000_000:
        return [v / 1_000_000_000 for v in serie], "R$ Bilhões", "bi"
    if pico >= 1_000_000:
        return [v / 1_000_000 for v in serie], "R$ Milhões", "mi"
    return serie, "R$", "rs"


def _styles() -> dict[str, ParagraphStyle]:
    _register_fonts()
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "ESCReportTitle",
            parent=base["Title"],
            fontName=FONT_SERIF,
            fontSize=20,
            leading=24,
            textColor=NAVY,
            spaceAfter=10,
            alignment=TA_LEFT,
        ),
        "h2": ParagraphStyle(
            "ESCReportH2",
            parent=base["Heading2"],
            fontName=FONT_SANS_BOLD,
            fontSize=13,
            leading=16,
            textColor=NAVY,
            spaceBefore=4,
            spaceAfter=8,
        ),
        "h3": ParagraphStyle(
            "ESCReportH3",
            parent=base["Heading3"],
            fontName=FONT_SANS_BOLD,
            fontSize=9,
            leading=12,
            textColor=GOLD,
            spaceBefore=2,
            spaceAfter=4,
        ),
        "body": ParagraphStyle(
            "ESCReportBody",
            parent=base["BodyText"],
            fontName=FONT_SANS,
            fontSize=9.5,
            leading=13.5,
            textColor=SLATE,
            alignment=TA_JUSTIFY,
            spaceAfter=8,
        ),
        "insight": ParagraphStyle(
            "ESCReportInsight",
            parent=base["BodyText"],
            fontName=FONT_SANS,
            fontSize=9,
            leading=13,
            textColor=SLATE,
            alignment=TA_JUSTIFY,
            spaceAfter=0,
        ),
        "muted": ParagraphStyle(
            "ESCReportMuted",
            parent=base["BodyText"],
            fontName=FONT_SANS,
            fontSize=8,
            leading=11,
            textColor=SLATE,
        ),
        "center": ParagraphStyle(
            "ESCReportCenter",
            parent=base["BodyText"],
            alignment=TA_CENTER,
            fontName=FONT_SANS_BOLD,
            fontSize=9,
            leading=11,
            textColor=NAVY,
        ),
        "th": ParagraphStyle(
            "ESCTh",
            parent=base["BodyText"],
            fontName=FONT_SANS_BOLD,
            fontSize=8,
            leading=10,
            textColor=WHITE,
        ),
        "td_left": ParagraphStyle(
            "ESCTdLeft",
            parent=base["BodyText"],
            fontName=FONT_SANS,
            fontSize=8,
            leading=10,
            textColor=SLATE,
            alignment=TA_LEFT,
        ),
        "td_right": ParagraphStyle(
            "ESCTdRight",
            parent=base["BodyText"],
            fontName=FONT_SANS,
            fontSize=8,
            leading=10,
            textColor=NAVY,
            alignment=TA_RIGHT,
        ),
        "td_right_bold": ParagraphStyle(
            "ESCTdRightBold",
            parent=base["BodyText"],
            fontName=FONT_SANS_BOLD,
            fontSize=8,
            leading=10,
            textColor=NAVY,
            alignment=TA_RIGHT,
        ),
    }


class ExecutiveCanvas(Canvas):
    """Cabecalho/rodape dinamicos com Pagina X de Y e selo de confidencialidade."""

    report_meta: dict[str, str] = {}

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
            self._draw_chrome(page_count)
            super().showPage()
        super().save()

    def _draw_chrome(self, page_count: int) -> None:
        _register_fonts()
        meta = getattr(self, "report_meta", {}) or {}
        scenario = str(meta.get("scenario") or "")
        confidential = str(meta.get("confidential") or "Confidencial — Uso Interno")
        self.saveState()
        if self._pageNumber == 1:
            self.setFillColor(NAVY)
            self.rect(0, 0, 1.15 * cm, PAGE_HEIGHT, fill=1, stroke=0)
            self.setFillColor(GOLD)
            self.rect(1.15 * cm, 0, 0.09 * cm, PAGE_HEIGHT, fill=1, stroke=0)
            self.setFillColor(NAVY)
            self.rect(0, 0, PAGE_WIDTH, 1.15 * cm, fill=1, stroke=0)
            self.setFillColor(GOLD)
            self.rect(0, 1.15 * cm, PAGE_WIDTH, 0.06 * cm, fill=1, stroke=0)
            self.setFillColor(WHITE)
            self.setFont(FONT_SANS, 7.5)
            self.drawString(1.6 * cm, 0.48 * cm, confidential.upper())
            self.drawRightString(PAGE_WIDTH - 1.4 * cm, 0.48 * cm, f"Página {self._pageNumber} de {page_count}")
            self.restoreState()
            return
        self.setFillColor(NAVY)
        self.rect(0, PAGE_HEIGHT - 1.15 * cm, PAGE_WIDTH, 1.15 * cm, fill=1, stroke=0)
        self.setFillColor(GOLD)
        self.rect(0, PAGE_HEIGHT - 1.21 * cm, PAGE_WIDTH, 0.06 * cm, fill=1, stroke=0)
        self.setFillColor(WHITE)
        self.setFont(FONT_SANS_BOLD, 8)
        self.drawString(1.6 * cm, PAGE_HEIGHT - 0.72 * cm, "Grupo ESC")
        self.setFont(FONT_SANS, 8)
        self.drawRightString(PAGE_WIDTH - 1.6 * cm, PAGE_HEIGHT - 0.72 * cm, scenario)
        self.setStrokeColor(LINE)
        self.setLineWidth(0.4)
        self.line(1.6 * cm, 1.15 * cm, PAGE_WIDTH - 1.6 * cm, 1.15 * cm)
        self.setFillColor(SLATE)
        self.setFont(FONT_SANS, 7.5)
        self.drawString(1.6 * cm, 0.72 * cm, confidential)
        self.drawCentredString(PAGE_WIDTH / 2, 0.72 * cm, scenario)
        self.drawRightString(PAGE_WIDTH - 1.6 * cm, 0.72 * cm, f"Página {self._pageNumber} de {page_count}")
        self.restoreState()


def executive_canvas_factory(meta: dict[str, str]):
    class BoundCanvas(ExecutiveCanvas):
        report_meta = dict(meta)

    return BoundCanvas


class CoverPage(Flowable):
    """Capa executiva A4 com marca, titulo, cenario e metadados."""

    def __init__(self, meta: dict[str, str]):
        super().__init__()
        self.meta = meta

    def wrap(self, availWidth, availHeight):
        self.width = availWidth
        self.height = max(availHeight - 0.2 * cm, 18 * cm)
        return self.width, self.height

    def draw(self) -> None:
        _register_fonts()
        c = self.canv
        w, h = self.width, self.height
        issued = self.meta.get("issued_at") or datetime.now().strftime("%d/%m/%Y %H:%M")
        c.setFillColor(NAVY)
        c.roundRect(0, h - 1.65 * cm, 1.65 * cm, 1.65 * cm, 3, fill=1, stroke=0)
        c.setFillColor(WHITE)
        c.setFont(FONT_SANS_BOLD, 12)
        c.drawCentredString(0.825 * cm, h - 1.0 * cm, "ESC")
        c.setFillColor(GOLD)
        c.setFont(FONT_SANS_BOLD, 9)
        c.drawString(2.0 * cm, h - 0.65 * cm, self.meta.get("company_name") or "Grupo ESC")
        c.setFillColor(SLATE)
        c.setFont(FONT_SANS, 8)
        c.drawString(2.0 * cm, h - 1.15 * cm, "Corporate Intelligence  ·  Dashboard CTI")
        c.setStrokeColor(GOLD)
        c.setLineWidth(1.6)
        c.line(0, h - 2.15 * cm, w * 0.42, h - 2.15 * cm)
        c.setFillColor(GOLD)
        c.setFont(FONT_SANS, 8)
        c.drawString(0, h - 3.05 * cm, "RELATÓRIO EXECUTIVO")
        c.setFillColor(NAVY)
        c.setFont(FONT_SERIF, 22)
        c.drawString(0, h - 4.25 * cm, "Desempenho Financeiro")
        c.setFont(FONT_SERIF, 20)
        c.drawString(0, h - 5.15 * cm, "e Leitura de Cenário")
        c.setFillColor(GOLD)
        c.setFont(FONT_SANS_BOLD, 11)
        c.drawString(0, h - 6.25 * cm, str(self.meta.get("scenario") or ""))
        c.setFillColor(SLATE)
        c.setFont(FONT_SANS, 9)
        c.drawString(0, h - 7.05 * cm, self.meta.get("title") or "Relatório personalizado para apresentação C-Level")
        y = 4.8 * cm
        rows = (
            ("Perfil destinatário", self.meta.get("profile") or "—"),
            ("Autor", self.meta.get("author") or "—"),
            ("Emissão", issued),
            ("Classificação", self.meta.get("confidential") or "Confidencial — Uso Interno"),
        )
        c.setStrokeColor(LINE)
        c.setLineWidth(0.4)
        c.line(0, y + 1.55 * cm, w, y + 1.55 * cm)
        for label, value in rows:
            c.setFillColor(GOLD)
            c.setFont(FONT_SANS_BOLD, 7.5)
            c.drawString(0, y, label.upper())
            c.setFillColor(NAVY)
            c.setFont(FONT_SANS, 10)
            c.drawString(4.4 * cm, y, str(value))
            y -= 0.85 * cm


def _header_footer(canvas, doc) -> None:
    """Compatibilidade com o gerador legado; o canvas executivo assume o chrome."""
    _ = canvas, doc


def _esc_mark() -> Table:
    mark = Table([["ESC"]], colWidths=[1.55 * cm], rowHeights=[1.55 * cm])
    mark.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), NAVY),
                ("TEXTCOLOR", (0, 0), (-1, -1), WHITE),
                ("FONTNAME", (0, 0), (-1, -1), FONT_SANS_BOLD),
                ("FONTSIZE", (0, 0), (-1, -1), 13),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )
    return mark


def _looks_numeric(value: Any) -> bool:
    texto = str(value)
    return any(token in texto for token in ("R$", "%", "x", "bi", "mi")) or texto.replace(".", "").replace(",", "").replace("-", "").replace("—", "").isdigit()


def _table(rows: list[list[Any]], widths: list[float] | None = None, *, highlight_labels: set[str] | None = None) -> Table:
    styles = _styles()
    highlight_labels = highlight_labels or set()
    formatted: list[list[Any]] = []
    for row_idx, row in enumerate(rows):
        formatted_row = []
        for col_idx, cell in enumerate(row):
            if row_idx == 0:
                formatted_row.append(Paragraph(_clean_text(cell), styles["th"]))
                continue
            numeric = col_idx > 0 or _looks_numeric(cell)
            highlight = str(row[0]) in highlight_labels
            style = styles["td_right_bold"] if numeric and highlight else styles["td_right"] if numeric else styles["td_left"]
            formatted_row.append(Paragraph(_clean_text(cell), style))
        formatted.append(formatted_row)
    table = Table(formatted, colWidths=widths, hAlign="LEFT", repeatRows=1)
    commands = [
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("FONTNAME", (0, 0), (-1, 0), FONT_SANS_BOLD),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LINEBELOW", (0, 0), (-1, 0), 1.1, GOLD),
        ("BOX", (0, 0), (-1, -1), 0.25, LINE),
        ("ALIGN", (0, 0), (0, -1), "LEFT"),
    ]
    if formatted and len(formatted[0]) > 1:
        commands.append(("ALIGN", (1, 0), (-1, -1), "RIGHT"))
    for row_idx in range(1, len(formatted)):
        bg = ICE if row_idx % 2 else ZEBRA
        commands.append(("BACKGROUND", (0, row_idx), (-1, row_idx), bg))
        if rows[row_idx] and str(rows[row_idx][0]) in highlight_labels:
            commands.append(("BACKGROUND", (0, row_idx), (-1, row_idx), colors.HexColor("#E2E8F0")))
    table.setStyle(TableStyle(commands))
    return table


def insight_card(title: str, text: str) -> Table:
    styles = _styles()
    card = Table(
        [
            [Paragraph(_clean_text(title), styles["h3"])],
            [Paragraph(_clean_text(text), styles["insight"])],
        ],
        colWidths=[16.4 * cm],
    )
    card.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), ICE),
                ("BOX", (0, 0), (-1, -1), 0.4, LINE),
                ("LINEBEFORE", (0, 0), (0, -1), 3.2, GOLD),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, 0), 8),
                ("BOTTOMPADDING", (0, -1), (-1, -1), 10),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )
    return card


def section_block(title: str, insight: str, *flowables: Any) -> list[Any]:
    styles = _styles()
    heading = [Paragraph(title, styles["h2"])]
    if insight.strip():
        heading.append(insight_card("Diagnostic & Insights — Assistente CTI", insight))
        heading.append(Spacer(1, 0.25 * cm))
    pieces: list[Any] = [KeepTogether(heading)]
    for item in flowables:
        if item is None:
            continue
        pieces.append(KeepTogether([item, Spacer(1, 0.18 * cm)]))
    return [CondPageBreak(7.2 * cm), *pieces]


def _apply_chart_theme(fig: go.Figure, *, x_title: str, y_title: str, title: str) -> go.Figure:
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor=CHART_NAVY,
        plot_bgcolor="#102033",
        font={"color": CHART_ICE, "family": "Calibri, Arial, sans-serif", "size": 12},
        title={"text": title, "font": {"size": 15, "color": CHART_ICE}},
        legend={"orientation": "h", "y": -0.18, "font": {"size": 11}},
        margin={"l": 64, "r": 28, "t": 56, "b": 72},
        xaxis_title=x_title,
        yaxis_title=y_title,
    )
    fig.update_xaxes(
        gridcolor="rgba(248,250,252,0.08)",
        zeroline=False,
        tickfont={"size": 11},
        title_font={"size": 12},
        separatethousands=True,
        exponentformat="none",
        showexponent="none",
    )
    fig.update_yaxes(
        gridcolor="rgba(248,250,252,0.12)",
        zeroline=False,
        tickformat=".1f",
        separatethousands=True,
        exponentformat="none",
        showexponent="none",
        tickfont={"size": 11},
        title_font={"size": 12},
    )
    return fig


def _fig_to_image(fig: go.Figure, width: int = 980, height: int = 430):
    """Renderiza Plotly em PNG de alta resolucao (scale=2 ~ 300 DPI em 16,5 cm)."""
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
                timeout=12,
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
        return Image(BytesIO(png_path.read_bytes()), width=16.5 * cm, height=7.2 * cm)


def _fig_to_matplotlib_image(fig: go.Figure):
    """Fallback local em 300 DPI quando Kaleido nao esta operacional."""
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from matplotlib.ticker import FuncFormatter
    except Exception:
        return None

    data = fig.to_dict().get("data", [])
    if not data:
        return None
    layout = fig.to_dict().get("layout", {})
    title = layout.get("title", {}).get("text", "") if isinstance(layout.get("title"), dict) else layout.get("title", "")
    x_title = layout.get("xaxis", {}).get("title", {}).get("text", "") if isinstance(layout.get("xaxis", {}).get("title"), dict) else ""
    y_title = layout.get("yaxis", {}).get("title", {}).get("text", "") if isinstance(layout.get("yaxis", {}).get("title"), dict) else ""

    fig_mpl, ax = plt.subplots(figsize=(8.6, 3.7), dpi=300)
    fig_mpl.patch.set_facecolor(CHART_NAVY)
    ax.set_facecolor("#102033")
    plotted = False
    palette = [CHART_ICE, CHART_GOLD, CHART_BLUE, "#FBBF24"]
    for idx, trace in enumerate(data):
        x = trace.get("x", [])
        y = trace.get("y", [])
        name = trace.get("name") or ""
        if len(x) == 0 or len(y) == 0:
            continue
        color = palette[idx % len(palette)]
        if trace.get("type") == "bar":
            ax.bar(x, y, label=name, color=color, alpha=0.88)
        else:
            ax.plot(x, y, marker="o", linewidth=2.1, markersize=4, label=name, color=color)
        plotted = True
    if not plotted:
        plt.close(fig_mpl)
        return None
    ax.set_title(title or "Gráfico", fontsize=11, fontweight="bold", color=CHART_ICE, loc="left")
    ax.set_xlabel(x_title or "", color=CHART_ICE)
    ax.set_ylabel(y_title or "", color=CHART_ICE)
    ax.tick_params(colors=CHART_ICE, labelsize=8)
    ax.grid(True, axis="y", alpha=0.18, color=CHART_ICE)
    for spine in ax.spines.values():
        spine.set_color("#1E3A8A")
    ax.yaxis.set_major_formatter(FuncFormatter(lambda val, _pos: f"{val:,.1f}".replace(",", "X").replace(".", ",").replace("X", ".")))
    try:
        ax.ticklabel_format(style="plain", axis="x", useOffset=False)
    except Exception:
        pass
    if len(data) > 1:
        legend = ax.legend(loc="upper left", fontsize=7, frameon=False)
        for text in legend.get_texts():
            text.set_color(CHART_ICE)
    fig_mpl.tight_layout()
    buffer = BytesIO()
    fig_mpl.savefig(buffer, format="png", dpi=300, facecolor=fig_mpl.get_facecolor())
    plt.close(fig_mpl)
    buffer.seek(0)
    return Image(buffer, width=16.5 * cm, height=7.2 * cm)


def _dre_figure(dre: pd.DataFrame) -> go.Figure:
    years = pd.to_numeric(dre["ano_num"], errors="coerce").astype(int)
    receita = _series(dre, "Receita Líquida", "Receita Liquida")
    ebitda = _series(dre, "EBITDA")
    pico = max(abs(float(receita.max() or 0)), abs(float(ebitda.max() or 0)))
    divisor = 1_000_000_000 if pico >= 1_000_000_000 else 1_000_000 if pico >= 1_000_000 else 1
    unidade = "Receita e EBITDA em R$ Bilhões" if divisor == 1_000_000_000 else "Receita e EBITDA em R$ Milhões" if divisor == 1_000_000 else "Receita e EBITDA em R$"
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=years, y=receita / divisor, mode="lines+markers", name="Receita Líquida", line={"color": CHART_ICE, "width": 3}))
    fig.add_trace(go.Scatter(x=years, y=ebitda / divisor, mode="lines+markers", name="EBITDA", line={"color": CHART_GOLD, "width": 3}))
    fig.update_xaxes(tickmode="linear", tick0=1, dtick=1)
    return _apply_chart_theme(fig, x_title="Ano do horizonte", y_title=unidade, title="Receita Líquida vs EBITDA")


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
    pico = max(abs(float(chart["Receita Total"].max())), abs(float(chart["Custos Totais"].max())), abs(be))
    divisor = 1_000_000_000 if pico >= 1_000_000_000 else 1_000_000 if pico >= 1_000_000 else 1
    unidade = "R$ Bilhões" if divisor == 1_000_000_000 else "R$ Milhões" if divisor == 1_000_000 else "R$"
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=chart["Receita"] / divisor, y=chart["Receita Total"] / divisor, mode="lines+markers", name="Receita Total", line={"color": CHART_ICE, "width": 3}))
    fig.add_trace(go.Scatter(x=chart["Receita"] / divisor, y=chart["Custos Totais"] / divisor, mode="lines+markers", name="Custos Totais", line={"color": CHART_GOLD, "width": 3}))
    fig.add_vline(x=be / divisor, line_dash="dash", line_color=CHART_BLUE, annotation_text=f"Break-even {_money(be)}", annotation_font_color=CHART_ICE)
    return _apply_chart_theme(fig, x_title=f"Receita em {unidade}", y_title=f"Resultado em {unidade}", title="Ponto de Equilíbrio")


def _ltv_cac_figure(ltv: pd.DataFrame) -> go.Figure:
    years = pd.to_numeric(ltv["ano_num"], errors="coerce").astype(int)
    ltv_s, unidade, _ = _scale_values(ltv["LTV"])
    cac_s, unidade_cac, _ = _scale_values(ltv["CAC"])
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_bar(x=years, y=ltv_s, name="LTV", marker_color="#1E3A8A")
    fig.add_scatter(x=years, y=cac_s, name="CAC", mode="lines+markers", line={"color": CHART_GOLD, "width": 3}, secondary_y=True)
    fig.update_xaxes(tickmode="linear", tick0=1, dtick=1)
    fig = _apply_chart_theme(fig, x_title="Ano do horizonte", y_title=f"LTV em {unidade}", title="LTV vs CAC por Ano")
    fig.update_yaxes(title_text=f"LTV em {unidade}", tickformat=".1f", exponentformat="none", showexponent="none", secondary_y=False)
    fig.update_yaxes(title_text=f"CAC em {unidade_cac}", tickformat=".1f", exponentformat="none", showexponent="none", secondary_y=True)
    return fig


def _add_chart(story: list[Any], fig: go.Figure, styles: dict[str, ParagraphStyle], fallback: str) -> None:
    image = _fig_to_image(fig)
    if image is None:
        story.append(Paragraph(fallback, styles["body"]))
        return
    story.append(KeepTogether([image, Spacer(1, 0.2 * cm)]))


def generate_executive_pdf(
    df: pd.DataFrame,
    *,
    scenario: str,
    year_filter: str | int = "Todos",
    company_name: str = "Grupo ESC",
    notes: dict[str, str] | None = None,
) -> bytes:
    """Gera um relatorio executivo A4 em PDF."""
    from Backend.services.report_insights import build_block_insights, merge_notes_with_insights

    notes = merge_notes_with_insights(notes, build_block_insights(df, scenario))
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
    meta = {
        "company_name": company_name,
        "profile": "CEO",
        "scenario": str(scenario),
        "author": "Assistente CTI",
        "issued_at": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "confidential": "Confidencial — Uso Interno",
        "title": f"Recorte: {year_filter}",
    }
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=1.7 * cm,
        rightMargin=1.7 * cm,
        topMargin=1.7 * cm,
        bottomMargin=1.6 * cm,
        title="Relatório Executivo ESC",
    )
    story: list[Any] = [CoverPage(meta), PageBreak()]
    kpis = _table(
        [
            ["Indicador", "Valor"],
            ["Receita Líquida Média", _money(receita)],
            ["EBITDA Médio", _money(ebitda)],
            ["Margem EBITDA", _pct(margem_ebitda)],
            ["Break-Even Médio", _money(break_even)],
            ["LTV/CAC Médio", f"{ltv_summary['ratio']:.1f}x"],
        ],
        [8.2 * cm, 8.2 * cm],
        highlight_labels={"EBITDA Médio", "Margem EBITDA"},
    )
    story.extend(section_block("Resumo Executivo", notes.get("cover", ""), kpis))
    dre_chart = _fig_to_image(_dre_figure(dre)) if not dre.empty else Paragraph("Sem dados de DRE para o cenário.", styles["body"])
    story.extend(section_block("Análise de EBITDA & DRE", notes.get("financial_dre") or notes.get("dre_analysis", ""), dre_chart))
    be_chart = _fig_to_image(_break_even_figure(be_df)) if not be_df.empty else Paragraph("Sem dados de break-even.", styles["body"])
    story.extend(section_block("Ponto de Equilíbrio & Risco", notes.get("break_even", ""), be_chart))
    ltv_bits: list[Any] = []
    if not ltv.empty:
        ltv_bits.append(_fig_to_image(_ltv_cac_figure(ltv)))
        rows = [["Ano", "LTV", "CAC", "LTV/CAC"]]
        for _, row in ltv.head(12).iterrows():
            rows.append([int(row["ano_num"]), _money(row["LTV"]), _money(row["CAC"]), f"{float(row['LTV/CAC']):.1f}x"])
        ltv_bits.append(_table(rows, [2.4 * cm, 4.6 * cm, 4.6 * cm, 4.8 * cm]))
    story.extend(section_block("Eficiência Comercial", notes.get("commercial") or notes.get("ltv_cac", ""), *ltv_bits))
    doc.build(story, canvasmaker=executive_canvas_factory(meta))
    return buffer.getvalue()
