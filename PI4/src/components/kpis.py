"""Cards de KPI e selos de negócio."""

from __future__ import annotations

import numpy as np
import pandas as pd
import streamlit as st

from src.config import COR, CORES_SELO
from src.config.i18n import t, translate_selo
from src.data.formatting import fmt_dias, fmt_pct, fmt_rs


def card_selo_html(nome: str, qtd: int, ativo: bool) -> str:
    cor = CORES_SELO.get(nome, COR)
    borda = "3px solid #111" if ativo else f"1px solid {cor}"
    fundo = f"{cor}22" if not ativo else f"{cor}44"
    rotulo = translate_selo(nome)
    return f"""
<div style="
    border:{borda};
    background:{fundo};
    border-radius:10px;
    padding:0.65rem 0.75rem;
    min-height:4.6rem;
">
  <div style="font-size:0.78rem;font-weight:700;color:{cor};line-height:1.25;">{rotulo}</div>
  <div style="font-size:1.15rem;font-weight:700;margin-top:0.35rem;">{t("map.scenarios_n", n=qtd)}</div>
</div>
"""


def kpis_por_persona(persona: str, k: pd.Series, ranking: pd.DataFrame) -> list[tuple[str, str]]:
    n = ranking.shape[0]
    p_ruina = float((ranking["caixa_ano12"] < 0).mean() * 100) if n else 0.0
    if persona == "cfo":
        return [
            (t("kpi.ncg"), fmt_rs(k["NCG"])),
            (t("kpi.treasury"), fmt_rs(k["Saldo_Tesouraria"])),
            (t("kpi.risk"), fmt_pct(k["risco"]) if pd.notna(k["risco"]) else "—"),
            (t("kpi.ruin_prob"), f"{p_ruina:.1f}%"),
        ]
    if persona == "acionistas":
        resultado = k["resultado"] if "resultado" in k.index else np.nan
        return [
            (t("kpi.profitability"), fmt_pct(k["rentabilidade"]) if pd.notna(k["rentabilidade"]) else "—"),
            (t("kpi.result"), fmt_rs(resultado) if pd.notna(resultado) else "—"),
            (t("kpi.cycle"), fmt_dias(k["Ciclo_Financeiro"])),
            (t("kpi.liquidity"), f"{k['liquidez']:.2f}x" if pd.notna(k["liquidez"]) else "—"),
        ]
    if persona == "concedente":
        return [
            (t("kpi.treasury"), fmt_rs(k["Saldo_Tesouraria"])),
            (t("kpi.cycle"), fmt_dias(k["Ciclo_Financeiro"])),
            (t("kpi.liquidity"), f"{k['liquidez']:.2f}x" if pd.notna(k["liquidez"]) else "—"),
            (t("kpi.ruin_prob"), f"{p_ruina:.1f}%"),
        ]
    return [
        (t("kpi.ncg"), fmt_rs(k["NCG"])),
        (t("kpi.treasury"), fmt_rs(k["Saldo_Tesouraria"])),
        (t("kpi.cycle"), fmt_dias(k["Ciclo_Financeiro"])),
        (t("kpi.liquidity"), f"{k['liquidez']:.2f}x" if pd.notna(k["liquidez"]) else "—"),
    ]


def render_kpi_row(itens: list[tuple[str, str]]) -> None:
    cols = st.columns(4)
    for col_ui, (rotulo, valor) in zip(cols, itens, strict=True):
        col_ui.metric(rotulo, valor)
