"""Helpers de leitura e calculo para KPIs."""

from __future__ import annotations

import pandas as pd

from src.models.formatting import is_all_scenarios


def _safe_div(numerador: float, denominador: float) -> float:
    if pd.isna(numerador) or pd.isna(denominador) or float(denominador) == 0:
        return float("nan")
    return float(numerador) / float(denominador)


def _valor_conta_raw(df: pd.DataFrame | None, cena: str | None, conta: str, ano_sel: str | int) -> float:
    if df is None or df.empty:
        return float("nan")
    recorte = df.loc[df["CONTA"] == conta]
    if not is_all_scenarios(cena):
        recorte = recorte.loc[recorte["CENA"] == cena]
    if ano_sel != "Todos":
        recorte = recorte.loc[pd.to_numeric(recorte["ano_num"], errors="coerce") == int(ano_sel)]
    if recorte.empty:
        return float("nan")
    return float(pd.to_numeric(recorte["VALOR"], errors="coerce").mean())


def _valor_premissa_comercial(
    df: pd.DataFrame | None,
    cena: str | None,
    nomes: list[str],
    ano_sel: str | int,
    fallback: float,
) -> float:
    if df is None or df.empty:
        return fallback
    recorte = df.loc[df["CONTA"].isin(nomes)]
    if not is_all_scenarios(cena):
        recorte = recorte.loc[recorte["CENA"] == cena]
    if ano_sel != "Todos":
        recorte = recorte.loc[pd.to_numeric(recorte["ano_num"], errors="coerce") == int(ano_sel)]
    if recorte.empty:
        return fallback
    valor = float(pd.to_numeric(recorte["VALOR"], errors="coerce").mean())
    return valor if pd.notna(valor) else fallback
