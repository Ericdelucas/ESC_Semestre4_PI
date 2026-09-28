"""Constantes usadas nos KPIs executivos."""

from __future__ import annotations

from typing import TypeAlias

KpiItem: TypeAlias = tuple[str, str, str | None] | tuple[str, str, str | None, str | None]

CONTA_EBITDA = "DRE - EBITDA"
CONTA_RECEITA = "DRE - Receita"
CONTA_TRIBUTOS = "DRE - Tributos"
CONTA_CUSTOS = "DRE - Custos"
CONTA_OUTROS_RESULTADOS = "DRE - Outros Resultados Operacionais"
CONTA_RESULTADO_OPERACIONAL = "DRE - Resultado Operacional"
CONTA_IR_CS = "DRE - Imposto de Renda e Contribuição Social"
CONTA_RESULTADO_LIQUIDO = "DRE - Resultado Líquido"
CONTA_FLU_INVESTIMENTOS = "FLU - Investimentos"
CONTA_PATRIMONIO_LIQUIDO = "BAL  - Patrimônio Líquido"
CONTA_EMPRESTIMOS = "BAL - Empréstimos"
CONTA_DISPONIVEL = "BAL - Disponível"
CONTA_ATIVO_CIRCULANTE = "BAL - Ativo Circulante"
CONTA_PASSIVO_CIRCULANTE = "BAL - Passivo Circulante"
CONTA_REALIZAVEL_LP = "BAL - Realizável a Longo Prazo"
CONTA_EXIGIVEL_LP = "BAL - Exigível a Longo Prazo"
CONTA_TOTAL_ATIVO = "BAL - Total do Ativo"

WACC_FALLBACK = 0.10
ALIQUOTA_IR_FALLBACK = 0.34

CEO_LTV_CAC_FALLBACK = {
    "Investimento em Vendas e Mkt (R$)": 100_000.0,
    "Novos Clientes Adquiridos (un)": 1_000.0,
    "Ticket Médio (R$)": 4_500.0,
    "Tempo Médio de Retenção (Meses)": 10.0,
}
