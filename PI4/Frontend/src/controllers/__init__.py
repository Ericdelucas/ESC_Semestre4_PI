"""Componentes de UI do painel CTI — imports sob demanda (evita ciclo no hot-reload)."""

from __future__ import annotations

__all__ = [
    "ancorar_ano_temporal",
    "banner_auditoria_filtro",
    "card_selo_html",
    "expander_auditoria_base",
    "heading_with_help",
    "figura_envelope",
    "figura_histograma_ano",
    "figura_histograma_caixa_final",
    "kpis_por_persona",
    "recorte_label",
    "render_kpi_row",
    "render_metric_card",
    "render_persona",
    "render_sidebar",
    "safe_render",
    "titulo_filtro",
    "render_ai_layout",
]


def __getattr__(name: str):
    if name in {
        "ancorar_ano_temporal",
        "figura_envelope",
        "figura_histograma_ano",
        "figura_histograma_caixa_final",
        "recorte_label",
        "titulo_filtro",
    }:
        from src.controllers import charts as mod

        return getattr(mod, name)
    if name in {"banner_auditoria_filtro", "expander_auditoria_base", "heading_with_help"}:
        from src.controllers import headers as mod

        return getattr(mod, name)
    if name in {"card_selo_html", "kpis_por_persona", "render_kpi_row", "render_metric_card"}:
        from src.controllers import kpis as mod

        return getattr(mod, name)
    if name == "safe_render":
        from src.controllers.resilience import safe_render

        return safe_render
    if name in {"render_persona", "render_sidebar"}:
        from src.controllers import sidebar as mod

        return getattr(mod, name)
    if name == "render_ai_layout":
        from src.controllers.ai_sidebar_right import render_ai_layout

        return render_ai_layout
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
