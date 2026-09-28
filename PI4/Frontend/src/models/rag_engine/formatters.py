"""Formatadores locais usados no contexto RAG."""

from __future__ import annotations

import pandas as pd


def rs(x: float) -> str:
    if pd.isna(x):
        return "—"
    v = float(x)
    sinal = "-" if v < 0 else ""
    a = abs(v)
    if a >= 1e9:
        return f"{sinal}R$ {a / 1e9:.2f} bi"
    if a >= 1e6:
        return f"{sinal}R$ {a / 1e6:.2f} mi"
    return f"{sinal}R$ {a:,.0f}"


def pct(x: float) -> str:
    if pd.isna(x):
        return "—"
    return f"{float(x) * 100:.2f}%"


def dias(x: float) -> str:
    if pd.isna(x):
        return "—"
    return f"{float(x):.1f} dias"
