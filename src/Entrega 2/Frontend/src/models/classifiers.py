"""Compatibilidade: classificacao de cenarios agora vive no Backend."""

from __future__ import annotations

import sys
from pathlib import Path


PI4_ROOT = Path(__file__).resolve().parents[3]
if str(PI4_ROOT) not in sys.path:
    sys.path.insert(0, str(PI4_ROOT))

from Backend.metrics.financial_kpis import classificar_cenarios  # noqa: E402

__all__ = ["classificar_cenarios"]
