"""Diagnostic & Insights do Assistente CTI para o relatorio executivo."""

from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FuturesTimeout
from typing import Any

import pandas as pd

from Backend.metrics import calculate_ltv_cac, summarize_ltv_cac
from Backend.metrics.column_resolver import series_by_alias
from Backend.metrics.financial_kpis import build_break_even, build_dre


def _mean(df: pd.DataFrame, *aliases: str) -> float:
    if df.empty:
        return 0.0
    serie = pd.to_numeric(series_by_alias(df, aliases), errors="coerce")
    value = float(serie.mean()) if not serie.empty else 0.0
    return 0.0 if pd.isna(value) else value


def _money(value: float) -> str:
    from Backend.services.report_generator import format_exec_money

    return format_exec_money(value)


def _pct(value: float) -> str:
    from Backend.services.report_generator import format_exec_pct

    return format_exec_pct(value)


def collect_scenario_metrics(df: pd.DataFrame, scenario: str) -> dict[str, float]:
    dre = build_dre(df, scenario)
    be_df = build_break_even(df, scenario)
    ltv = summarize_ltv_cac(df, scenario)
    receita = _mean(dre, "Receita Líquida", "Receita Liquida")
    ebitda = _mean(dre, "EBITDA")
    ebit = _mean(dre, "EBIT")
    lucro = _mean(dre, "Lucro Líquido", "Lucro Liquido")
    if abs(lucro) < 1e-9:
        lucro = _mean(dre, "EBT") + _mean(dre, "Imposto de Renda", "IR/CS")
    margem_ebitda = ebitda / receita if receita else 0.0
    return {
        "receita": receita,
        "ebitda": ebitda,
        "ebit": ebit,
        "lucro": lucro,
        "margem_ebitda": margem_ebitda,
        "break_even": _mean(be_df, "Break-Even"),
        "margem_contrib": _mean(be_df, "Margem de Contribuição (%)", "Margem de Contribuicao (%)"),
        "margem_seg": _mean(be_df, "Margem de Segurança (%)", "Margem de Seguranca (%)"),
        "ltv": float(ltv.get("ltv") or 0.0),
        "cac": float(ltv.get("cac") or 0.0),
        "ltv_cac": float(ltv.get("ratio") or 0.0),
    }


def _rule_cover(scenario: str, m: dict[str, float]) -> str:
    if m["margem_ebitda"] >= 0.20 and m["margem_seg"] >= 0.15 and m["ltv_cac"] >= 3:
        leitura = "o recorte indica folga operacional e economia unitaria saudavel"
    elif m["margem_ebitda"] >= 0.10 or m["margem_seg"] >= 0.05:
        leitura = "o recorte e intermediario: ha geracao operacional, porem com pontos de atencao para o Board"
    else:
        leitura = "o recorte sinaliza pressao conjunta de margem e caixa, exigindo pauta de mitigacao"
    return (
        f"Parecer do Assistente CTI sobre o cenario {scenario}: receita media de {_money(m['receita'])}, "
        f"EBITDA medio de {_money(m['ebitda'])} ({_pct(m['margem_ebitda'])} de margem) e lucro medio de "
        f"{_money(m['lucro'])}. Na leitura consolidada, {leitura}. "
        f"O ponto de equilibrio medio esta em {_money(m['break_even'])}, com margem de seguranca de "
        f"{_pct(m['margem_seg'])}."
    )


def _rule_dre(m: dict[str, float]) -> str:
    alavanca = "positiva" if m["ebitda"] > 0 and m["receita"] > 0 else "sob estresse"
    if m["margem_ebitda"] >= 0.25:
        margem = "elevada, com ampla conversao de receita em caixa operacional"
    elif m["margem_ebitda"] >= 0.12:
        margem = "aderente a um perfil de concessao madura, ainda sensivel a custos"
    else:
        margem = "comprimida, sugerindo revisao de OPEX, mix ou precificacao"
    ebit_vs_ebitda = m["ebit"] / m["ebitda"] if m["ebitda"] else 0.0
    depreciacao = (
        "A distancia entre EBITDA e EBIT indica carga relevante de depreciacao/amortizacao."
        if ebit_vs_ebitda < 0.7 and m["ebitda"]
        else "EBITDA e EBIT caminham proximos, com menor pressao de nao-caixa."
    )
    return (
        f"A DRE media mostra receita de {_money(m['receita'])} e EBITDA de {_money(m['ebitda'])}, "
        f"equivalente a margem {_pct(m['margem_ebitda'])} — leitura {margem}. "
        f"O EBIT medio de {_money(m['ebit'])} confirma alavancagem operacional {alavanca}. {depreciacao}"
    )


def _rule_break_even(m: dict[str, float]) -> str:
    if m["margem_seg"] >= 0.25:
        risco = "folga confortavel frente ao ponto de equilibrio"
    elif m["margem_seg"] >= 0.08:
        risco = "colchao moderado: um choque de demanda ou custo ja reduz a folga"
    elif m["margem_seg"] >= 0:
        risco = "proximidade do equilibrio; o cenario e sensivel a desvios de volume"
    else:
        risco = "receita media abaixo do break-even, com risco de operacao no vermelho"
    return (
        f"O break-even medio estimado e {_money(m['break_even'])}, com margem de contribuicao de "
        f"{_pct(m['margem_contrib'])} e margem de seguranca de {_pct(m['margem_seg'])}. "
        f"Diagnostico: {risco}. A pauta executiva deve cruzar esse ponto com a trajetoria de custos fixos."
    )


def _rule_commercial(m: dict[str, float]) -> str:
    ratio = m["ltv_cac"]
    if ratio >= 3:
        veredito = "o LTV/CAC esta no intervalo considerado eficiente para reinvestimento comercial"
    elif ratio >= 1:
        veredito = "o retorno por cliente ainda cobre o CAC, mas o payback e longo para o padrao de board"
    else:
        veredito = "o custo de aquisicao consome o valor estimado do cliente e pede revisao de funnel ou ticket"
    return (
        f"LTV medio de {_money(m['ltv'])} contra CAC de {_money(m['cac'])}, razao {ratio:.1f}x. "
        f"Na otica de eficiencia comercial, {veredito}."
    )


def _rule_operational(m: dict[str, float]) -> str:
    return (
        f"A leitura operacional deve ser feita contra a geracao media de {_money(m['ebitda'])} de EBITDA. "
        "CapEx, OpEx e depreciação definem se a infraestrutura da concessao escala sem corroer a folga de caixa."
    )


def _rule_comparison(scenario: str, m: dict[str, float]) -> str:
    return (
        f"O cenario-base {scenario} entra no comparativo com margem EBITDA de {_pct(m['margem_ebitda'])} "
        f"e LTV/CAC de {m['ltv_cac']:.1f}x. A dispersao entre cenarios deve ser lida como mapa de resiliencia, "
        "nao como ranking estatico."
    )


def _facts_block(section: str, scenario: str, m: dict[str, float]) -> str:
    return (
        f"cenario={scenario}; secao={section}; "
        f"receita={_money(m['receita'])}; ebitda={_money(m['ebitda'])}; "
        f"margem_ebitda={_pct(m['margem_ebitda'])}; ebit={_money(m['ebit'])}; "
        f"lucro={_money(m['lucro'])}; break_even={_money(m['break_even'])}; "
        f"margem_contrib={_pct(m['margem_contrib'])}; margem_seguranca={_pct(m['margem_seg'])}; "
        f"ltv={_money(m['ltv'])}; cac={_money(m['cac'])}; ltv_cac={m['ltv_cac']:.1f}x"
    )


def _llm_paragraph(section: str, facts: str) -> str | None:
    api_key = (os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY") or "").strip()
    if not api_key:
        return None
    try:
        from google import genai
        from google.genai import types
    except ImportError:
        return None

    prompt = (
        "Voce e o Assistente CTI. Escreva 2 ou 3 frases em portugues, tom de memo para Board "
        "(McKinsey/Goldman). Interprete SOMENTE os fatos numericos abaixo. Nao invente valores, "
        "nao use notacao cientifica, nao faca pergunta final, nao use markdown.\n\n"
        f"{facts}"
    )

    def _call() -> str:
        client = genai.Client(api_key=api_key)
        for modelo in ("gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash"):
            try:
                resp = client.models.generate_content(
                    model=modelo,
                    contents=prompt,
                    config=types.GenerateContentConfig(temperature=0.2, max_output_tokens=220),
                )
                texto = (resp.text or "").strip()
                if texto:
                    return texto
            except Exception:
                continue
        return ""

    try:
        with ThreadPoolExecutor(max_workers=1) as pool:
            return pool.submit(_call).result(timeout=8) or None
    except (FuturesTimeout, Exception):
        return None


def build_block_insights(df: pd.DataFrame, scenario: str, *, use_llm: bool = True) -> dict[str, str]:
    """Gera pareceres qualitativos por bloco a partir dos KPIs reais do cenario."""
    metrics = collect_scenario_metrics(df, scenario)
    fallback = {
        "cover": _rule_cover(scenario, metrics),
        "financial_dre": _rule_dre(metrics),
        "break_even": _rule_break_even(metrics),
        "commercial": _rule_commercial(metrics),
        "operational_tech": _rule_operational(metrics),
        "scenario_comparison": _rule_comparison(scenario, metrics),
    }
    if use_llm:
        llm = _llm_paragraph("cover", _facts_block("cover", scenario, metrics))
        if llm:
            fallback["cover"] = llm
    return fallback


def merge_notes_with_insights(notes: dict[str, str] | None, insights: dict[str, str]) -> dict[str, str]:
    """Usa o texto do usuario quando ele acrescenta parecer; senão, o insight do Assistente CTI."""
    notes = notes or {}
    merged: dict[str, str] = {}
    for key, insight in insights.items():
        user = str(notes.get(key) or "").strip()
        if not user or user == insight:
            merged[key] = insight
            continue
        if user in insight or insight in user:
            merged[key] = user
            continue
        merged[key] = f"{user}\n\n{insight}"
    for key, user in notes.items():
        merged.setdefault(key, str(user))
    return merged


def insight_payload(df: pd.DataFrame, scenario: str) -> dict[str, Any]:
    metrics = collect_scenario_metrics(df, scenario)
    insights = build_block_insights(df, scenario)
    return {"metrics": metrics, "insights": insights}
