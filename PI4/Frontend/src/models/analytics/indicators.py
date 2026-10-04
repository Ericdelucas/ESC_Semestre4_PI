"""Compatibilidade: indicadores financeiros agora vivem no Backend."""

from __future__ import annotations

import sys
from pathlib import Path


PI4_ROOT = Path(__file__).resolve().parents[4]
if str(PI4_ROOT) not in sys.path:
    sys.path.insert(0, str(PI4_ROOT))

from Backend.metrics.financial_kpis import (  # noqa: E402
    compactar_indicadores as _compactar_indicadores,
    mapa_contas as _mapa_contas,
    montar_indicadores,
)

__all__ = ["_compactar_indicadores", "_mapa_contas", "montar_indicadores"]
