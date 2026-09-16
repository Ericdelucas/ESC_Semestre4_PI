"""Cards de KPI e selos de negócio."""

from __future__ import annotations

from html import escape

import numpy as np
import pandas as pd
import streamlit as st

from src.config import COR, CORES_SELO
from src.config.glossary import help_text
from src.config.i18n import t, translate_selo
from src.data.formatting import fmt_dias, fmt_pct, fmt_rs

KpiItem = tuple[str, str, str | None]


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


def kpis_por_persona(persona: str, k: pd.Series, ranking: pd.DataFrame) -> list[KpiItem]:
    n = ranking.shape[0]
    p_ruina = float((ranking["caixa_ano12"] < 0).mean() * 100) if n else 0.0
    if persona == "cfo":
        return [
            (t("kpi.ncg"), fmt_rs(k["NCG"]), help_text("ncg")),
            (t("kpi.treasury"), fmt_rs(k["Saldo_Tesouraria"]), help_text("treasury")),
            (t("kpi.risk"), fmt_pct(k["risco"]) if pd.notna(k["risco"]) else "—", help_text("risk")),
            (t("kpi.ruin_prob"), f"{p_ruina:.1f}%", help_text("ruin_prob")),
        ]
    if persona == "acionistas":
        resultado = k["resultado"] if "resultado" in k.index else np.nan
        return [
            (
                t("kpi.profitability"),
                fmt_pct(k["rentabilidade"]) if pd.notna(k["rentabilidade"]) else "—",
                help_text("profitability"),
            ),
            (t("kpi.result"), fmt_rs(resultado) if pd.notna(resultado) else "—", help_text("result")),
            (t("kpi.cycle"), fmt_dias(k["Ciclo_Financeiro"]), help_text("cycle")),
            (
                t("kpi.liquidity"),
                f"{k['liquidez']:.2f}x" if pd.notna(k["liquidez"]) else "—",
                help_text("liquidity"),
            ),
        ]
    if persona == "concedente":
        return [
            (t("kpi.treasury"), fmt_rs(k["Saldo_Tesouraria"]), help_text("treasury")),
            (t("kpi.cycle"), fmt_dias(k["Ciclo_Financeiro"]), help_text("cycle")),
            (
                t("kpi.liquidity"),
                f"{k['liquidez']:.2f}x" if pd.notna(k["liquidez"]) else "—",
                help_text("liquidity"),
            ),
            (t("kpi.ruin_prob"), f"{p_ruina:.1f}%", help_text("ruin_prob")),
        ]
    return [
        (t("kpi.ncg"), fmt_rs(k["NCG"]), help_text("ncg")),
        (t("kpi.treasury"), fmt_rs(k["Saldo_Tesouraria"]), help_text("treasury")),
        (t("kpi.cycle"), fmt_dias(k["Ciclo_Financeiro"]), help_text("cycle")),
        (
            t("kpi.liquidity"),
            f"{k['liquidez']:.2f}x" if pd.notna(k["liquidez"]) else "—",
            help_text("liquidity"),
        ),
    ]


_KPI_CSS = f"""
<style>
.cti-kpi-row {{
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 1.15rem;
  overflow: visible;
  padding-bottom: 0.35rem;
}}
.cti-kpi {{
  position: relative;
  cursor: help;
  padding: 0.1rem 0.15rem 0.4rem 0;
  overflow: visible;
}}
.cti-kpi-label {{
  font-size: 0.875rem;
  line-height: 1.3;
  color: var(--secondary-text-color, rgba(49, 51, 63, 0.7));
  display: flex;
  align-items: center;
  gap: 0.35rem;
}}
.cti-kpi-info {{
  font-size: 0.78rem;
  opacity: 0.7;
  color: {COR};
}}
.cti-kpi-value {{
  font-size: 1.6rem;
  font-weight: 600;
  line-height: 1.35;
  color: var(--text-color, #31333F);
  font-variant-numeric: tabular-nums;
}}
.cti-kpi-tip {{
  display: none;
  position: absolute;
  z-index: 10000;
  left: 0;
  top: calc(100% + 0.2rem);
  width: max-content;
  max-width: min(22rem, 72vw);
  padding: 0.55rem 0.75rem;
  background: {COR};
  color: #fff;
  font-size: 0.8rem;
  font-weight: 400;
  line-height: 1.4;
  border-radius: 8px;
  box-shadow: 0 8px 20px rgba(31, 78, 69, 0.28);
  pointer-events: none;
}}
.cti-kpi-row .cti-kpi:nth-child(3) .cti-kpi-tip,
.cti-kpi-row .cti-kpi:nth-child(4) .cti-kpi-tip {{
  left: auto;
  right: 0;
}}
.cti-kpi:hover .cti-kpi-tip,
.cti-kpi:focus-within .cti-kpi-tip {{
  display: block;
}}
</style>
"""


def _kpi_card_html(rotulo: str, valor: str, dica: str | None) -> str:
    """Card HTML com ``title`` no rótulo — hover no texto, não só no ícone do Streamlit."""
    label = escape(rotulo)
    val = escape(str(valor))
    if not dica:
        return (
            f'<div class="cti-kpi">'
            f'<div class="cti-kpi-label">{label}</div>'
            f'<div class="cti-kpi-value">{val}</div>'
            f"</div>"
        )
    tip = escape(dica, quote=True)
    tip_body = escape(dica)
    return (
        f'<div class="cti-kpi" tabindex="0" title="{tip}">'
        f'<div class="cti-kpi-label" title="{tip}">'
        f"<span>{label}</span><span class=\"cti-kpi-info\" aria-hidden=\"true\">ⓘ</span>"
        f"</div>"
        f'<div class="cti-kpi-value">{val}</div>'
        f'<div class="cti-kpi-tip">{tip_body}</div>'
        f"</div>"
    )


def render_metric_card(label: str, value: str, dica: str | None = None) -> None:
    """Métrica com tooltip no hover do rótulo (HTML ``title`` + balão CSS)."""
    st.html(_KPI_CSS + _kpi_card_html(label, value, dica))


def render_kpi_row(itens: list[KpiItem]) -> None:
    cards = "".join(_kpi_card_html(rotulo, valor, dica) for rotulo, valor, dica in itens)
    st.html(f'{_KPI_CSS}<div class="cti-kpi-row">{cards}</div>')
