"""Componentes visuais para cartoes de KPI."""

from __future__ import annotations

from collections.abc import Sequence

from src.controllers.kpis.rendering import KpiItem, render_kpi_row


def render_kpi_cards(items: Sequence[KpiItem]) -> None:
    """Renderiza uma linha de cards de KPI."""
    render_kpi_row(list(items))

