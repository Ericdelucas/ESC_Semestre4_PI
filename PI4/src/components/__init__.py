"""Componentes de UI do painel CTI."""

from src.components.charts import (
    ancorar_ano_temporal,
    figura_envelope,
    figura_histograma_ano,
    figura_histograma_caixa_final,
    recorte_label,
    titulo_filtro,
)
from src.components.headers import banner_auditoria_filtro, expander_auditoria_base, render_titulo
from src.components.kpis import card_selo_html, kpis_por_persona, render_kpi_row
from src.components.resilience import safe_render
from src.components.sidebar import render_persona, render_sidebar

__all__ = [
    "ancorar_ano_temporal",
    "banner_auditoria_filtro",
    "card_selo_html",
    "expander_auditoria_base",
    "figura_envelope",
    "figura_histograma_ano",
    "figura_histograma_caixa_final",
    "kpis_por_persona",
    "recorte_label",
    "render_kpi_row",
    "render_persona",
    "render_sidebar",
    "render_titulo",
    "safe_render",
    "titulo_filtro",
]
