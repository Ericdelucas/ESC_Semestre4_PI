"""Cards de KPI e selos de negócio."""

from __future__ import annotations

import numpy as np
import pandas as pd
import streamlit as st

from src.config import COR, CORES_SELO
from src.data.formatting import fmt_dias, fmt_pct, fmt_rs


def card_selo_html(nome: str, qtd: int, ativo: bool) -> str:
    cor = CORES_SELO.get(nome, COR)
    borda = "3px solid #111" if ativo else f"1px solid {cor}"
    fundo = f"{cor}22" if not ativo else f"{cor}44"
    return f"""
<div style="
    border:{borda};
    background:{fundo};
    border-radius:10px;
    padding:0.65rem 0.75rem;
    min-height:4.6rem;
">
  <div style="font-size:0.78rem;font-weight:700;color:{cor};line-height:1.25;">{nome}</div>
  <div style="font-size:1.15rem;font-weight:700;margin-top:0.35rem;">{qtd} cenários</div>
</div>
"""


def kpis_por_persona(persona: str, k: pd.Series, ranking: pd.DataFrame) -> list[tuple[str, str]]:
    n = ranking.shape[0]
    p_ruina = float((ranking["caixa_ano12"] < 0).mean() * 100) if n else 0.0
    if persona == "CFO & Credores":
        return [
            ("NCG", fmt_rs(k["NCG"])),
            ("Saldo de Tesouraria", fmt_rs(k["Saldo_Tesouraria"])),
            ("Risco (Passivo/Ativo)", fmt_pct(k["risco"]) if pd.notna(k["risco"]) else "—"),
            ("Prob. caixa negativo Ano 12", f"{p_ruina:.1f}%"),
        ]
    if persona == "Acionistas":
        resultado = k["resultado"] if "resultado" in k.index else np.nan
        return [
            ("Rentabilidade", fmt_pct(k["rentabilidade"]) if pd.notna(k["rentabilidade"]) else "—"),
            ("Resultado líquido (média)", fmt_rs(resultado) if pd.notna(resultado) else "—"),
            ("Ciclo Financeiro", fmt_dias(k["Ciclo_Financeiro"])),
            ("Liquidez corrente", f"{k['liquidez']:.2f}x" if pd.notna(k["liquidez"]) else "—"),
        ]
    if persona == "Poder Concedente":
        return [
            ("Saldo de Tesouraria", fmt_rs(k["Saldo_Tesouraria"])),
            ("Ciclo Financeiro", fmt_dias(k["Ciclo_Financeiro"])),
            ("Liquidez corrente", f"{k['liquidez']:.2f}x" if pd.notna(k["liquidez"]) else "—"),
            ("Prob. caixa negativo Ano 12", f"{p_ruina:.1f}%"),
        ]
    return [
        ("NCG", fmt_rs(k["NCG"])),
        ("Saldo de Tesouraria", fmt_rs(k["Saldo_Tesouraria"])),
        ("Ciclo Financeiro", fmt_dias(k["Ciclo_Financeiro"])),
        ("Liquidez corrente", f"{k['liquidez']:.2f}x" if pd.notna(k["liquidez"]) else "—"),
    ]


def render_kpi_row(itens: list[tuple[str, str]]) -> None:
    cols = st.columns(4)
    for col_ui, (rotulo, valor) in zip(cols, itens, strict=True):
        col_ui.metric(rotulo, valor)
