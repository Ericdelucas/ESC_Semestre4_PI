"""Utilitarios numericos das metricas financeiras."""

from __future__ import annotations

import pandas as pd


def _safe_div(num: pd.Series, den: pd.Series) -> pd.Series:
    return pd.to_numeric(num, errors="coerce") / pd.to_numeric(den, errors="coerce").replace(0, pd.NA)


def _to_number(series: pd.Series) -> pd.Series:
    if pd.api.types.is_numeric_dtype(series):
        return pd.to_numeric(series, errors="coerce")
    texto = series.astype(str).str.strip()
    br = texto.str.contains(",", regex=False)
    normalizado = texto.where(~br, texto.str.replace(".", "", regex=False).str.replace(",", ".", regex=False))
    normalizado = normalizado.str.replace("R$", "", regex=False).str.replace("x", "", regex=False).str.strip()
    return pd.to_numeric(normalizado, errors="coerce")


def _normalizar_aliases(wide: pd.DataFrame) -> pd.DataFrame:
    if (
        "BAL  - Patrimônio Líquido" in wide.columns
        and "BAL - Patrimônio Líquido" in wide.columns
        and wide["BAL - Patrimônio Líquido"].fillna(0).eq(0).all()
    ):
        wide["BAL - Patrimônio Líquido"] = wide["BAL  - Patrimônio Líquido"]
    if (
        "BAL - Patrimônio Líquido" in wide.columns
        and "BAL  - Patrimônio Líquido" in wide.columns
        and wide["BAL  - Patrimônio Líquido"].fillna(0).eq(0).all()
    ):
        wide["BAL  - Patrimônio Líquido"] = wide["BAL - Patrimônio Líquido"]
    if (
        "DRE - Despesas Financeiras" in wide.columns
        and "FLU - Despesas Financeiras" in wide.columns
        and wide["FLU - Despesas Financeiras"].fillna(0).eq(0).all()
    ):
        wide["FLU - Despesas Financeiras"] = wide["DRE - Despesas Financeiras"]
    return wide
