"""KPIs da visao do CEO."""

from __future__ import annotations

import pandas as pd

from Backend.metrics import summarize_ltv_cac
from Backend.metrics.column_resolver import series_by_alias
from Backend.metrics.financial_kpis import build_break_even
from src.config.i18n import t
from src.models.formatting import fmt_rs

from .constants import CONTA_EBITDA, CONTA_RECEITA, KpiItem
from .helpers import _safe_div, _valor_conta_raw


def _zero_se_na(valor: float) -> float:
    return 0.0 if pd.isna(valor) else float(valor)


def _mean_break_even(df: pd.DataFrame, cena: str, ano_sel: str | int) -> float:
    dados = build_break_even(df, cena)
    if dados.empty:
        return 0.0
    if ano_sel != "Todos":
        dados = dados.loc[pd.to_numeric(dados["ano_num"], errors="coerce") == int(ano_sel)]
    value = float(series_by_alias(dados, ["Break-Even"]).mean()) if not dados.empty else 0.0
    return 0.0 if pd.isna(value) else value


def _kpis_ceo(df: pd.DataFrame | None, cena: str | None, ano_sel: str | int) -> list[KpiItem]:
    if df is None:
        return []

    receita = _zero_se_na(_valor_conta_raw(df, cena, CONTA_RECEITA, ano_sel))
    ebitda = _zero_se_na(_valor_conta_raw(df, cena, CONTA_EBITDA, ano_sel))
    margem_ebitda = _safe_div(ebitda, receita)
    if pd.isna(margem_ebitda):
        margem_ebitda = 0.0

    break_even = _mean_break_even(df, cena, ano_sel)
    ltv_cac = summarize_ltv_cac(df, cena, ano_sel)["ratio"]

    return [
        (
            t("kpi.ceo.ebitda"),
            fmt_rs(ebitda),
            t("kpi.ceo.ebitda_delta", pct=margem_ebitda * 100),
            None,
        ),
        (
            t("kpi.ceo.be"),
            fmt_rs(break_even),
            t("kpi.ceo.be_delta"),
            None,
        ),
        (
            t("kpi.ceo.ltv"),
            f"{ltv_cac:.1f}x",
            t("kpi.ceo.ltv_delta"),
            None,
        ),
    ]
