"""Servico de relatorio executivo customizavel por blocos."""

from __future__ import annotations

from datetime import datetime
from io import BytesIO
from typing import Any
import time

import pandas as pd
import plotly.graph_objects as go

from Backend.metrics import calculate_ltv_cac, summarize_ltv_cac
from Backend.metrics.financial_kpis import build_break_even, build_dre, is_all_scenarios
from Backend.services.report_generator import (
    CHART_GOLD,
    CHART_ICE,
    _add_chart,
    _apply_chart_theme,
    _break_even_figure,
    _clean_text,
    _dre_figure,
    _ltv_cac_figure,
    _money,
    _pct,
    _series,
    _styles,
    _table,
    executive_canvas_factory,
    masthead,
    section_block,
    side_by_side,
)
from Backend.services.report_insights import insights_from_tables, merge_notes_with_insights
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Table, TableStyle


BLOCKS: dict[str, str] = {
    "cover": "Bloco 1: Capa & Resumo Executivo",
    "financial_dre": "Bloco 2: Visao Financeira & DRE",
    "break_even": "Bloco 3: Ponto de Equilibrio & Margens",
    "commercial": "Bloco 4: Eficiencia Comercial",
    "operational_tech": "Bloco 5: Visao Operacional & Tech",
    "scenario_comparison": "Bloco 6: Comparativo de Cenarios",
}


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
    lucro = _series(dre, "Lucro Líquido", "Lucro Liquido")
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


def _log(msg: str) -> None:
    from Backend.diag import log_relatorio

    log_relatorio(msg)


def _memo_frames(
    df: pd.DataFrame,
    scenario: str,
    dre: pd.DataFrame | None = None,
    be: pd.DataFrame | None = None,
    ltv: pd.DataFrame | None = None,
    extra_frames: dict[str, dict[str, pd.DataFrame]] | None = None,
):
    store: dict[tuple[str, str], pd.DataFrame] = {}
    if dre is not None:
        store[("dre", str(scenario))] = dre
    if be is not None:
        store[("be", str(scenario))] = be
    if ltv is not None:
        store[("ltv", str(scenario))] = ltv
    for extra_cena, frames in (extra_frames or {}).items():
        if frames.get("dre") is not None:
            store[("dre", str(extra_cena))] = frames["dre"]
        if frames.get("be") is not None:
            store[("be", str(extra_cena))] = frames["be"]
        if frames.get("ltv") is not None:
            store[("ltv", str(extra_cena))] = frames["ltv"]

    def dre_of(scena: str) -> pd.DataFrame:
        key = ("dre", str(scena))
        if key not in store:
            t0 = time.time()
            _log(f"build_dre cenario={scena} linhas={len(df)}")
            store[key] = build_dre(df, scena)
            _log(f"build_dre OK linhas={len(store[key])} em {time.time() - t0:.2f}s")
        return store[key]

    def be_of(scena: str) -> pd.DataFrame:
        key = ("be", str(scena))
        if key not in store:
            t0 = time.time()
            _log(f"build_break_even cenario={scena}")
            store[key] = build_break_even(df, scena)
            _log(f"build_break_even OK em {time.time() - t0:.2f}s")
        return store[key]

    def ltv_of(scena: str) -> pd.DataFrame:
        key = ("ltv", str(scena))
        if key not in store:
            t0 = time.time()
            _log(f"calculate_ltv_cac cenario={scena}")
            store[key] = calculate_ltv_cac(df, scena)
            _log(f"calculate_ltv_cac OK em {time.time() - t0:.2f}s")
        return store[key]

    return dre_of, be_of, ltv_of


def _kpi_callouts(df: pd.DataFrame, scenario: str, dre_of=None, be_of=None, ltv_of=None) -> Table:
    """Monta callouts executivos da primeira pagina de conteudo."""
    dre = dre_of(scenario) if dre_of else build_dre(df, scenario)
    be_df = be_of(scenario) if be_of else build_break_even(df, scenario)
    if ltv_of:
        ltv_df = ltv_of(scenario)
        if ltv_df.empty or "LTV/CAC" not in ltv_df.columns:
            ltv_summary = {"ratio": 0.0}
        else:
            ratio = float(pd.to_numeric(ltv_df["LTV/CAC"], errors="coerce").mean())
            ltv_summary = {"ratio": 0.0 if pd.isna(ratio) else ratio}
    else:
        ltv_summary = summarize_ltv_cac(df, scenario)
    receita = _metric_mean(dre, "Receita Líquida", "Receita Liquida")
    ebitda = _metric_mean(dre, "EBITDA")
    margem = ebitda / receita if receita else 0.0
    break_even = _metric_mean(be_df, "Break-Even")
    from Backend.services.report_generator import FONT_SANS_BOLD, GOLD, NAVY, WHITE, _register_fonts
    from reportlab.lib import colors

    _register_fonts()

    table = Table(
        [
            ["EBITDA", "Margem EBITDA", "Break-Even", "LTV/CAC"],
            [_money(ebitda), _pct(margem), _money(break_even), f"{ltv_summary['ratio']:.1f}x"],
        ],
        colWidths=[4.1 * cm, 4.1 * cm, 4.1 * cm, 4.1 * cm],
        hAlign="LEFT",
    )
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), NAVY),
                ("BACKGROUND", (0, 1), (-1, 1), colors.HexColor("#F8FAFC")),
                ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
                ("TEXTCOLOR", (0, 1), (-1, 1), NAVY),
                ("FONTNAME", (0, 0), (-1, 0), FONT_SANS_BOLD),
                ("FONTNAME", (0, 1), (-1, 1), FONT_SANS_BOLD),
                ("FONTSIZE", (0, 0), (-1, 0), 8),
                ("FONTSIZE", (0, 1), (-1, 1), 11),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LINEBELOW", (0, 0), (-1, 0), 1.2, GOLD),
                ("BOX", (0, 0), (-1, -1), 0.3, colors.HexColor("#CBD5E1")),
                ("INNERGRID", (0, 0), (-1, -1), 0.2, colors.HexColor("#E2E8F0")),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    return table


def default_block_notes(df: pd.DataFrame | None = None, scenario: str = "Todos") -> dict[str, str]:
    """Parecer inicial por bloco. Nao varre a base de 1M ao abrir o modal."""
    if df is None or getattr(df, "empty", True) or len(df) > 80_000:
        return {key: "" for key in BLOCKS}
    return build_block_insights(df, scenario, use_llm=False)


def _cover_block(story: list[Any], df: pd.DataFrame, scenario: str, text: str, dre_of=None, be_of=None, ltv_of=None) -> None:
    styles = _styles()
    kpis = _kpi_callouts(df, scenario, dre_of=dre_of, be_of=be_of, ltv_of=ltv_of)
    story.extend(section_block("Resumo Executivo", text, kpis))
    story.append(Paragraph(_clean_text("Os indicadores acima sao medias do horizonte do cenario selecionado."), styles["muted"]))


def _financial_block(story: list[Any], df: pd.DataFrame, scenario: str, text: str, dre_of=None) -> None:
    styles = _styles()
    dre = dre_of(scenario) if dre_of else build_dre(df, scenario)
    if dre.empty:
        story.extend(section_block("Análise de EBITDA & DRE", text, Paragraph("Sem dados de DRE para o cenario selecionado.", styles["body"])))
        return
    rows = [
        ["Métrica", "Média do horizonte"],
        ["Receita Líquida", _money(_metric_mean(dre, "Receita Líquida", "Receita Liquida"))],
        ["EBITDA", _money(_metric_mean(dre, "EBITDA"))],
        ["EBIT", _money(_metric_mean(dre, "EBIT"))],
        ["Lucro Líquido", _money(_net_income_mean(dre))],
    ]
    table = _table(rows, [4.05 * cm, 4.05 * cm], highlight_labels={"Receita Líquida", "EBITDA"})
    chart = []
    _add_chart(chart, _dre_figure(dre), styles, "Grafico DRE indisponivel: renderizacao Plotly/Kaleido excedeu o timeout.")
    story.extend(section_block("Análise de EBITDA & DRE", text, table, *chart))


def _break_even_block(story: list[Any], df: pd.DataFrame, scenario: str, text: str, be_of=None) -> None:
    styles = _styles()
    be_df = be_of(scenario) if be_of else build_break_even(df, scenario)
    if be_df.empty:
        story.extend(section_block("Ponto de Equilíbrio & Risco", text, Paragraph("Sem dados suficientes para Break-Even.", styles["body"])))
        return
    rows = [
        ["Indicador", "Média do horizonte"],
        ["Break-Even", _money(_metric_mean(be_df, "Break-Even"))],
        ["Margem de Contribuição", _pct(_metric_mean(be_df, "Margem de Contribuição (%)", "Margem de Contribuicao (%)"))],
        ["Margem de Segurança", _pct(_metric_mean(be_df, "Margem de Segurança (%)", "Margem de Seguranca (%)"))],
    ]
    table = _table(rows, [4.05 * cm, 4.05 * cm], highlight_labels={"Break-Even"})
    chart = []
    _add_chart(chart, _break_even_figure(be_df), styles, "Grafico Break-Even indisponivel: renderizacao Plotly/Kaleido excedeu o timeout.")
    story.extend(section_block("Ponto de Equilíbrio & Risco", text, table, *chart))


def _commercial_block(story: list[Any], df: pd.DataFrame, scenario: str, text: str, ltv_of=None) -> None:
    styles = _styles()
    ltv = ltv_of(scenario) if ltv_of else calculate_ltv_cac(df, scenario)
    if ltv.empty:
        story.extend(section_block("Eficiência Comercial", text, Paragraph("Sem dados suficientes para LTV/CAC.", styles["body"])))
        return
    rows = [["Ano", "LTV", "CAC", "LTV/CAC"]]
    for _, row in ltv.head(6).iterrows():
        rows.append([int(row["ano_num"]), _money(row["LTV"]), _money(row["CAC"]), f"{float(row['LTV/CAC']):.1f}x"])
    table = _table(rows, [2.2 * cm, 4.8 * cm, 4.8 * cm, 4.8 * cm])
    chart = []
    _add_chart(chart, _ltv_cac_figure(ltv), styles, "Grafico LTV/CAC indisponivel: renderizacao Plotly/Kaleido excedeu o timeout.")
    story.extend(section_block("Eficiência Comercial", text, table, *chart))


def _operational_block(story: list[Any], df: pd.DataFrame, scenario: str, text: str) -> None:
    styles = _styles()
    if df is None or df.empty:
        story.extend(section_block("Visão Operacional & Tech", text, Paragraph("Sem dados operacionais para o cenario selecionado.", styles["body"])))
        return
    if is_all_scenarios(scenario) and len(df) > 80_000:
        _log("bloco operacional saltado — Todos sobre base longa")
        story.extend(
            section_block(
                "Visão Operacional & Tech",
                text,
                Paragraph("No recorte Todos a tabela operacional e omitida para nao varrer a base completa.", styles["body"]),
            )
        )
        return
    rows_df = df.loc[df["CENA"].astype(str) == str(scenario)].copy() if "CENA" in df.columns else df.iloc[0:0]
    if rows_df.empty:
        story.extend(section_block("Visão Operacional & Tech", text, Paragraph("Sem dados operacionais para o cenario selecionado.", styles["body"])))
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
    story.extend(section_block("Visão Operacional & Tech", text, _table(rows, [11.4 * cm, 5 * cm])))


def _comparison_block(
    story: list[Any],
    df: pd.DataFrame,
    scenario: str,
    comparison_scenarios: list[str],
    text: str,
    dre_of=None,
    be_of=None,
) -> None:
    styles = _styles()
    scenarios = [scenario, *[item for item in comparison_scenarios if item != scenario]][:4]
    rows = [["Cenário", "Receita Média", "EBITDA Médio", "Break-Even Médio"]]
    fig = go.Figure()
    scaled_series: list[pd.Series] = []
    for item in scenarios:
        dre = dre_of(item) if dre_of else build_dre(df, item)
        be_df = be_of(item) if be_of else build_break_even(df, item)
        receita = _metric_mean(dre, "Receita Líquida", "Receita Liquida")
        ebitda = _metric_mean(dre, "EBITDA")
        be = _metric_mean(be_df, "Break-Even")
        rows.append([item, _money(receita), _money(ebitda), _money(be)])
        if not dre.empty:
            scaled_series.append(_series(dre, "EBITDA"))
    pico = max((float(serie.abs().max()) for serie in scaled_series), default=0.0)
    divisor = 1_000_000_000 if pico >= 1_000_000_000 else 1_000_000 if pico >= 1_000_000 else 1
    unidade = "EBITDA em R$ Bilhões" if divisor == 1_000_000_000 else "EBITDA em R$ Milhões" if divisor == 1_000_000 else "EBITDA em R$"
    palette = [CHART_ICE, CHART_GOLD, "#93C5FD", "#FBBF24"]
    for idx, item in enumerate(scenarios):
        dre = dre_of(item) if dre_of else build_dre(df, item)
        if dre.empty:
            continue
        fig.add_trace(
            go.Scatter(
                x=dre["ano_num"],
                y=_series(dre, "EBITDA") / divisor,
                mode="lines+markers",
                name=item,
                line={"color": palette[idx % len(palette)], "width": 3},
            )
        )
    extras: list[Any] = [_table(rows, [4.4 * cm, 4 * cm, 4 * cm, 4 * cm], highlight_labels={scenario})]
    if fig.data:
        fig.update_xaxes(tickmode="linear", tick0=1, dtick=1)
        _apply_chart_theme(fig, x_title="Ano do horizonte", y_title=unidade, title="EBITDA por cenário")
        chart: list[Any] = []
        _add_chart(chart, fig, styles, "Grafico comparativo indisponivel: renderizacao Plotly/Kaleido excedeu o timeout.")
        extras.extend(chart)
    story.extend(section_block("Comparativo de Cenários", text, *extras))


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
    dre: pd.DataFrame | None = None,
    be: pd.DataFrame | None = None,
    ltv: pd.DataFrame | None = None,
    skip_charts: bool = True,
    use_llm: bool = False,
    extra_frames: dict[str, dict[str, pd.DataFrame]] | None = None,
) -> bytes:
    """Gera PDF personalizado no padrao executivo C-Level."""
    import Backend.services.report_generator as report_generator

    t0 = time.time()
    selected_blocks = _normalize_selected_blocks(selected_blocks)
    _log(
        f"generate_custom_report_pdf cenario={scenario} blocos={selected_blocks} "
        f"linhas={0 if df is None else len(df)} skip_charts={skip_charts} use_llm={use_llm}"
    )
    report_generator._SKIP_CHARTS = bool(skip_charts)
    dre_of, be_of, ltv_of = _memo_frames(
        df, scenario, dre=dre, be=be, ltv=ltv, extra_frames=extra_frames
    )
    _ = use_llm
    try:
        insights = insights_from_tables(scenario, dre_of(scenario), be_of(scenario), ltv_of(scenario))
        _log("insights montados a partir das tabelas cacheadas")
    except Exception as exc:  # noqa: BLE001
        _log(f"insights saltados ({type(exc).__name__}: {exc}) — a usar notas do formulario")
        insights = {key: "" for key in BLOCKS}
    notes = merge_notes_with_insights(notes, insights)
    buffer = BytesIO()
    issued = datetime.now().strftime("%d/%m/%Y %H:%M")
    meta = {
        "company_name": company_name,
        "profile": profile,
        "scenario": str(scenario),
        "author": author,
        "issued_at": issued,
        "confidential": "Confidencial — Uso Interno",
        "title": "Relatório personalizado para apresentação C-Level",
    }
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=1.5 * cm,
        rightMargin=1.5 * cm,
        topMargin=1.45 * cm,
        bottomMargin=1.35 * cm,
        title="Relatório Executivo Personalizado ESC",
        allowSplitting=1,
    )
    doc.pageBreakQuick = 0
    story: list[Any] = [masthead(meta)]
    selecionados = set(selected_blocks)
    rendered_count = 0

    if "cover" in selecionados:
        _log("bloco INICIO cover")
        _cover_block(story, df, scenario, notes.get("cover", ""), dre_of=dre_of, be_of=be_of, ltv_of=ltv_of)
        rendered_count += 1
        _log("bloco FIM cover")

    fin_story: list[Any] = []
    be_story: list[Any] = []
    if "financial_dre" in selecionados:
        _financial_block(fin_story, df, scenario, notes.get("financial_dre", ""), dre_of=dre_of)
        rendered_count += 1
    if "break_even" in selecionados:
        _break_even_block(be_story, df, scenario, notes.get("break_even", ""), be_of=be_of)
        rendered_count += 1
    if fin_story and be_story:
        story.append(side_by_side(fin_story, be_story))
    else:
        story.extend(fin_story)
        story.extend(be_story)

    if "commercial" in selecionados:
        _log("bloco INICIO commercial")
        _commercial_block(story, df, scenario, notes.get("commercial", ""), ltv_of=ltv_of)
        rendered_count += 1
        _log("bloco FIM commercial")
    if "operational_tech" in selecionados:
        _operational_block(story, df, scenario, notes.get("operational_tech", ""))
        rendered_count += 1
    if "scenario_comparison" in selecionados:
        _comparison_block(
            story,
            df,
            scenario,
            comparison_scenarios or [],
            notes.get("scenario_comparison", ""),
            dre_of=dre_of,
            be_of=be_of,
        )
        rendered_count += 1

    if rendered_count == 0:
        styles = _styles()
        story.extend(
            section_block(
                "Resumo Executivo",
                notes.get("cover", ""),
                _kpi_callouts(df, scenario, dre_of=dre_of, be_of=be_of, ltv_of=ltv_of),
            )
        )
        story.append(Paragraph("Nenhum bloco adicional foi selecionado.", styles["body"]))

    _log(f"doc.build a gravar PDF blocos={rendered_count}")
    doc.build(story, canvasmaker=executive_canvas_factory(meta))
    _log(f"PDF pronto bytes={buffer.tell()} em {time.time() - t0:.2f}s")
    return buffer.getvalue()
