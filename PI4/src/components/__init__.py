"""Componentes de UI do painel CTI — imports sob demanda (evita ciclo no hot-reload)."""

from __future__ import annotations

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


def __getattr__(name: str):
    if name in {
        "ancorar_ano_temporal",
        "figura_envelope",
        "figura_histograma_ano",
        "figura_histograma_caixa_final",
        "recorte_label",
        "titulo_filtro",
    }:
        from src.components import charts as mod

        return getattr(mod, name)
    if name in {"banner_auditoria_filtro", "expander_auditoria_base", "render_titulo"}:
        from src.components import headers as mod

        return getattr(mod, name)
    if name in {"card_selo_html", "kpis_por_persona", "render_kpi_row"}:
        from src.components import kpis as mod

        return getattr(mod, name)
    if name == "safe_render":
        from src.components.resilience import safe_render

        return safe_render
    if name in {"render_persona", "render_sidebar"}:
        from src.components import sidebar as mod

        return getattr(mod, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
