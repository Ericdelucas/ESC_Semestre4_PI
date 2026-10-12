"""Primitivas compartilhadas de formatacao."""

from __future__ import annotations

from typing import Any


def is_na(x: Any) -> bool:
    if x is None:
        return True
    try:
        return x != x  # NaN
    except Exception:
        return False


def fmt_number_pt(v: float, decimals: int) -> str:
    if decimals == 0:
        raw = f"{v:,.0f}"
    else:
        raw = f"{v:,.{decimals}f}"
    return raw.replace(",", "X").replace(".", ",").replace("X", ".")


def fmt_number_en(v: float, decimals: int) -> str:
    if decimals == 0:
        return f"{v:,.0f}"
    return f"{v:,.{decimals}f}"
