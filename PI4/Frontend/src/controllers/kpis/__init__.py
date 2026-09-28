"""Compatibilidade publica dos KPIs e cards do dashboard."""

from .constants import (
    ALIQUOTA_IR_FALLBACK,
    CEO_LTV_CAC_FALLBACK,
    CONTA_ATIVO_CIRCULANTE,
    CONTA_CUSTOS,
    CONTA_DISPONIVEL,
    CONTA_EBITDA,
    CONTA_EMPRESTIMOS,
    CONTA_EXIGIVEL_LP,
    CONTA_FLU_INVESTIMENTOS,
    CONTA_IR_CS,
    CONTA_OUTROS_RESULTADOS,
    CONTA_PASSIVO_CIRCULANTE,
    CONTA_PATRIMONIO_LIQUIDO,
    CONTA_RECEITA,
    CONTA_REALIZAVEL_LP,
    CONTA_RESULTADO_LIQUIDO,
    CONTA_RESULTADO_OPERACIONAL,
    CONTA_TOTAL_ATIVO,
    CONTA_TRIBUTOS,
    KpiItem,
    WACC_FALLBACK,
)
from .ceo import _kpis_ceo
from .concession import _kpis_poder_concedente
from .helpers import _safe_div, _valor_conta_raw, _valor_premissa_comercial
from .personas import kpis_por_persona
from .rendering import _garantir_css_metricas, card_selo_html, render_kpi_row, render_metric_card
from .shareholders import _kpis_acionistas

__all__ = [
    "ALIQUOTA_IR_FALLBACK",
    "CEO_LTV_CAC_FALLBACK",
    "CONTA_ATIVO_CIRCULANTE",
    "CONTA_CUSTOS",
    "CONTA_DISPONIVEL",
    "CONTA_EBITDA",
    "CONTA_EMPRESTIMOS",
    "CONTA_EXIGIVEL_LP",
    "CONTA_FLU_INVESTIMENTOS",
    "CONTA_IR_CS",
    "CONTA_OUTROS_RESULTADOS",
    "CONTA_PASSIVO_CIRCULANTE",
    "CONTA_PATRIMONIO_LIQUIDO",
    "CONTA_RECEITA",
    "CONTA_REALIZAVEL_LP",
    "CONTA_RESULTADO_LIQUIDO",
    "CONTA_RESULTADO_OPERACIONAL",
    "CONTA_TOTAL_ATIVO",
    "CONTA_TRIBUTOS",
    "KpiItem",
    "WACC_FALLBACK",
    "_garantir_css_metricas",
    "_kpis_acionistas",
    "_kpis_ceo",
    "_kpis_poder_concedente",
    "_safe_div",
    "_valor_conta_raw",
    "_valor_premissa_comercial",
    "card_selo_html",
    "kpis_por_persona",
    "render_kpi_row",
    "render_metric_card",
]
