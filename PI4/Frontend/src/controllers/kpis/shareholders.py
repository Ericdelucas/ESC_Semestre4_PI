"""KPIs da visao de acionistas."""

from __future__ import annotations

import pandas as pd

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
    KpiItem,
    WACC_FALLBACK,
)
from .helpers import _safe_div, _valor_conta_raw


def _kpis_acionistas(df: pd.DataFrame | None, cena: str | None, ano_sel: str | int) -> list[KpiItem]:
    resultado_operacional = _valor_conta_raw(df, cena, CONTA_RESULTADO_OPERACIONAL, ano_sel)
    ir_cs = _valor_conta_raw(df, cena, CONTA_IR_CS, ano_sel)
    resultado_liquido = _valor_conta_raw(df, cena, CONTA_RESULTADO_LIQUIDO, ano_sel)
    receita = _valor_conta_raw(df, cena, CONTA_RECEITA, ano_sel)
    patrimonio = abs(_valor_conta_raw(df, cena, CONTA_PATRIMONIO_LIQUIDO, ano_sel))
    divida = abs(_valor_conta_raw(df, cena, CONTA_EMPRESTIMOS, ano_sel))
    caixa = abs(_valor_conta_raw(df, cena, CONTA_DISPONIVEL, ano_sel))
    divida_liquida = max(divida - caixa, 0) if pd.notna(divida) and pd.notna(caixa) else float("nan")
    capital_investido = patrimonio + divida_liquida if pd.notna(patrimonio) and pd.notna(divida_liquida) else float("nan")

    aliquota_ir = _safe_div(abs(ir_cs), abs(resultado_operacional))
    if pd.isna(aliquota_ir):
        aliquota_ir = ALIQUOTA_IR_FALLBACK
    aliquota_ir = min(max(aliquota_ir, 0), ALIQUOTA_IR_FALLBACK)
    nopat = resultado_operacional * (1 - aliquota_ir) if pd.notna(resultado_operacional) else float("nan")
    roic = _safe_div(nopat, capital_investido)
    eva = nopat - (capital_investido * WACC_FALLBACK) if pd.notna(nopat) and pd.notna(capital_investido) else float("nan")
    margem_liquida = _safe_div(resultado_liquido, receita)

    return [
        (
            "Retorno sobre o Capital Investido (ROIC %)",
            fmt_pct(roic) if pd.notna(roic) else "—",
            "Retorno gerado sobre o capital total operado",
            None,
        ),
        (
            "Criação de Valor Econômico (EVA)",
            fmt_rs(eva),
            "Lucro econômico acima do custo de capital",
            None,
        ),
        (
            "Lucro Líquido & Margem Líquida (%)",
            fmt_rs(resultado_liquido),
            f"Margem: {margem_liquida * 100:.1f}%" if pd.notna(margem_liquida) else "Margem: —",
            None,
        ),
    ]
