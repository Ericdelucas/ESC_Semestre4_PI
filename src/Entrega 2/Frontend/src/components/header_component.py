"""Componentes visuais de cabecalho."""

from __future__ import annotations

from src.controllers.headers import banner_auditoria_filtro


def render_audit_banner(cena_sel: str, ano_sel: str | int) -> None:
    """Renderiza o banner de auditoria do filtro ativo."""
    banner_auditoria_filtro(cena_sel, ano_sel)

