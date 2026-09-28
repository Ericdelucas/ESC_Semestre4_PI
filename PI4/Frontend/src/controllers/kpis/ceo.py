"""KPIs da visao do CEO."""

from __future__ import annotations

import pandas as pd

from src.models.formatting import fmt_rs

from .constants import (
    CEO_LTV_CAC_FALLBACK,
    CONTA_CUSTOS,
    CONTA_EBITDA,
    CONTA_OUTROS_RESULTADOS,
    CONTA_RECEITA,
    CONTA_TRIBUTOS,
    KpiItem,
)
from .helpers import _safe_div, _valor_conta_raw, _valor_premissa_comercial


def _kpis_ceo(df: pd.DataFrame | None, cena: str | None, ano_sel: str | int) -> list[KpiItem]:
    receita = _valor_conta_raw(df, cena, CONTA_RECEITA, ano_sel)
    ebitda = _valor_conta_raw(df, cena, CONTA_EBITDA, ano_sel)
    tributos = _valor_conta_raw(df, cena, CONTA_TRIBUTOS, ano_sel)
    custos = _valor_conta_raw(df, cena, CONTA_CUSTOS, ano_sel)
    outros = _valor_conta_raw(df, cena, CONTA_OUTROS_RESULTADOS, ano_sel)

    margem_ebitda = _safe_div(ebitda, receita)
    margem_contribuicao_rs = (receita - abs(tributos)) - abs(custos)
    margem_contribuicao_pct = _safe_div(margem_contribuicao_rs, receita)
    break_even = _safe_div(abs(outros), margem_contribuicao_pct)

    investimento = _valor_premissa_comercial(
        df,
        cena,
        ["Investimento em Vendas e Mkt (R$)", "Investimento em Vendas e Marketing (R$)"],
        ano_sel,
        CEO_LTV_CAC_FALLBACK["Investimento em Vendas e Mkt (R$)"],
    )
    novos_clientes = _valor_premissa_comercial(
        df,
        cena,
        ["Novos Clientes Adquiridos (un)", "Novos Clientes Adquiridos"],
        ano_sel,
        CEO_LTV_CAC_FALLBACK["Novos Clientes Adquiridos (un)"],
    )
    ticket = _valor_premissa_comercial(
        df,
        cena,
        ["Ticket Médio (R$)", "Ticket Medio (R$)", "Ticket MÃ©dio (R$)"],
        ano_sel,
        CEO_LTV_CAC_FALLBACK["Ticket Médio (R$)"],
    )
    retencao = _valor_premissa_comercial(
        df,
        cena,
        ["Tempo Médio de Retenção (Meses)", "Tempo Medio de Retencao (Meses)", "Tempo MÃ©dio de RetenÃ§Ã£o (Meses)"],
        ano_sel,
        CEO_LTV_CAC_FALLBACK["Tempo Médio de Retenção (Meses)"],
    )
    cac = _safe_div(investimento, novos_clientes)
    ltv_cac = _safe_div(ticket * retencao, cac)

    return [
        (
            "EBITDA Operacional",
            fmt_rs(ebitda),
            f"Margem: {margem_ebitda * 100:.1f}%" if pd.notna(margem_ebitda) else "Margem: —",
            None,
        ),
        (
            "Ponto de Equilíbrio (Break-Even)",
            fmt_rs(break_even),
            "Faturamento mínimo exigido para cobrir despesas fixas",
            None,
        ),
        (
            "Eficiência Comercial (LTV / CAC)",
            f"{ltv_cac:.1f}x" if pd.notna(ltv_cac) else "—",
            "Multiplicador de retorno por cliente atraído",
            None,
        ),
    ]
