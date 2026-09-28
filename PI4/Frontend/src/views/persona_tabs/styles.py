"""Estilos compartilhados do comparador de cenarios."""

from __future__ import annotations

from src.config import COR, COR_ALERTA, COR_OK

SERIES_STYLES = {
    "A": {"color": COR, "dash": "solid", "fill": "rgba(31, 78, 69, 0.18)"},
    "B": {"color": COR_ALERTA, "dash": "dash", "fill": "rgba(166, 93, 63, 0.14)"},
    "C": {"color": COR_OK, "dash": "dot", "fill": "rgba(47, 107, 79, 0.10)"},
}
