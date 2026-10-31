"""Selecao de cenarios/anos e consolidacao anual do dashboard."""
from __future__ import annotations

import pandas as pd

from Backend.metrics.financial_kpis import is_all_scenarios


def media_por_ano(frame: pd.DataFrame) -> pd.DataFrame:
    if frame is None or frame.empty or "ano_num" not in frame.columns:
        return frame.copy() if isinstance(frame, pd.DataFrame) else pd.DataFrame()
    numeric = [c for c in frame.columns if c not in {"CENA", "ano_num"} and pd.api.types.is_numeric_dtype(frame[c])]
    if not numeric:
        return frame.drop_duplicates(subset=["ano_num"]).sort_values("ano_num")
    out = frame.groupby("ano_num", as_index=False)[numeric].mean()
    if "CENA" in frame.columns:
        out["CENA"] = "Todos"
    return out.sort_values("ano_num")


def filtrar_cenario_ano(
    ind: pd.DataFrame,
    *,
    cena_sel: str,
    ano_sel: str | int,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Devolve recortes brutos; as medias de KPIs sao calculadas antes da consolidacao."""
    if ind is None or ind.empty or "CENA" not in ind.columns:
        foco_raw = ind.iloc[0:0].copy() if isinstance(ind, pd.DataFrame) else pd.DataFrame()
    elif is_all_scenarios(cena_sel):
        foco_raw = ind
    else:
        foco_raw = ind.loc[ind["CENA"] == cena_sel]
    if "ano_num" in getattr(foco_raw, "columns", []):
        foco_raw = foco_raw.sort_values("ano_num")
    if ano_sel == "Todos" or "ano_num" not in getattr(foco_raw, "columns", []):
        foco_ano_raw = foco_raw
    else:
        ano_num = int(ano_sel)
        foco_ano_raw = foco_raw.loc[pd.to_numeric(foco_raw["ano_num"], errors="coerce") == ano_num]
    return foco_raw, foco_ano_raw
