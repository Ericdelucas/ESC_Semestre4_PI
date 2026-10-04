"""Componentes visuais de filtros laterais."""

from __future__ import annotations

import pandas as pd

from src.controllers.sidebar import render_language_selector, render_persona, render_sidebar


def render_language() -> None:
    """Renderiza seletor de idioma."""
    render_language_selector()


def render_persona_selector() -> str:
    """Renderiza seletor de persona."""
    return render_persona()


def render_filters(df: pd.DataFrame, ind: pd.DataFrame, n_cenarios: int) -> tuple[str | int, str, list[int], list[str]]:
    """Renderiza filtros principais da sidebar."""
    return render_sidebar(df, ind, n_cenarios)
