"""Compatibilidade visual para dados financeiros calculados no Backend."""

from __future__ import annotations

import sys
from pathlib import Path


PI4_ROOT = Path(__file__).resolve().parents[4]
if str(PI4_ROOT) not in sys.path:
    sys.path.insert(0, str(PI4_ROOT))

from Backend.metrics.financial_kpis import (  # noqa: E402
    ALIQUOTA_IR_FALLBACK,
    PAYOUT,
    WACC,
    _balanco_fluxo,
    _conta,
    build_break_even as _break_even_df,
    build_dre as _dre,
    build_financial_statement as _financeiro,
    safe_div as _safe_div,
)

__all__ = [
    "ALIQUOTA_IR_FALLBACK",
    "PAYOUT",
    "WACC",
    "_break_even_df",
    "_balanco_fluxo",
    "_conta",
    "_dre",
    "_financeiro",
    "_safe_div",
]
