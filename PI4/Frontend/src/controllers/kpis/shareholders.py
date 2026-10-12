"""KPIs da visao de acionistas."""

from __future__ import annotations

import pandas as pd

from src.config.i18n import t
from src.models.formatting import fmt_pct, fmt_rs

from .constants import (
    ALIQUOTA_IR_FALLBACK,
    CONTA_DISPONIVEL,
    CONTA_EMPRESTIMOS,
    CONTA_IR_CS,
    CONTA_PATRIMONIO_LIQUIDO,
    CONTA_RECEITA,
    CONTA_RESULTADO_LIQUIDO,
    CONTA_RESULTADO_OPERACIONAL,
    CONTA_TOTAL_ATIVO,
    KpiItem,
    WACC_FALLBACK,
)
from .helpers import _safe_div, _valor_conta_raw


def _zero_se_na(valor: float) -> float:
    return 0.0 if pd.isna(valor) else float(valor)


def _kpis_acionistas(df: pd.DataFrame | None, cena: str | None, ano_sel: str | int) -> list[KpiItem]:
    resultado_operacional = _zero_se_na(_valor_conta_raw(df, cena, CONTA_RESULTADO_OPERACIONAL, ano_sel))
    ir_cs = _valor_conta_raw(df, cena, CONTA_IR_CS, ano_sel)
    resultado_liquido = _zero_se_na(_valor_conta_raw(df, cena, CONTA_RESULTADO_LIQUIDO, ano_sel))
    receita = _valor_conta_raw(df, cena, CONTA_RECEITA, ano_sel)
    patrimonio = abs(_zero_se_na(_valor_conta_raw(df, cena, CONTA_PATRIMONIO_LIQUIDO, ano_sel)))
    divida = abs(_zero_se_na(_valor_conta_raw(df, cena, CONTA_EMPRESTIMOS, ano_sel)))
    caixa = abs(_zero_se_na(_valor_conta_raw(df, cena, CONTA_DISPONIVEL, ano_sel)))
    ativo_total = abs(_zero_se_na(_valor_conta_raw(df, cena, CONTA_TOTAL_ATIVO, ano_sel)))
    divida_liquida = max(divida - caixa, 0)
    capital_investido = patrimonio + divida_liquida
    if capital_investido <= 0 and ativo_total > 0:
        capital_investido = ativo_total

    aliquota_ir = _safe_div(abs(ir_cs), abs(resultado_operacional))
    if pd.isna(aliquota_ir):
        aliquota_ir = ALIQUOTA_IR_FALLBACK
    aliquota_ir = min(max(aliquota_ir, 0), ALIQUOTA_IR_FALLBACK)
    nopat = resultado_operacional * (1 - aliquota_ir)
    roic = _safe_div(nopat, capital_investido)
    if pd.isna(roic):
        roic = 0.0
    eva = nopat - (capital_investido * WACC_FALLBACK)
    margem_liquida = _safe_div(resultado_liquido, receita)
    if pd.isna(margem_liquida):
        margem_liquida = 0.0

    return [
        (
            t("kpi.sh.roic"),
            fmt_pct(roic),
            t("kpi.sh.roic_delta"),
            None,
        ),
        (
            t("kpi.sh.eva"),
            fmt_rs(eva),
            t("kpi.sh.eva_delta"),
            None,
        ),
        (
            t("kpi.sh.net"),
            fmt_rs(resultado_liquido),
            t("kpi.sh.net_delta", pct=margem_liquida * 100),
            None,
        ),
    ]
