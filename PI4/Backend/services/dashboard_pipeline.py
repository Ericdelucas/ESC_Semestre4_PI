"""Pipeline de dados pronto para consumo pelo dashboard."""

from __future__ import annotations

import os
from pathlib import Path

import pandas as pd

from Backend.data_loader import load_cti_csv, otimizar_base_cti
from Backend.metrics import calcular_kpis_recorte, montar_indicadores, probabilidade_caixa_negativo
from Backend.metrics.financial_kpis import compactar_indicadores, is_all_scenarios


BACKEND_DIR = Path(__file__).resolve().parents[1]
CACHE_DIR = BACKEND_DIR / "cache"
CSV_PATH = BACKEND_DIR / "Cti.csv"


def prepare_dashboard_data(csv_path: str | Path = CSV_PATH) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Carrega base, indicadores e ranking usando caches frescos quando existem."""
    csv = Path(csv_path)
    CACHE_DIR.mkdir(exist_ok=True)
    ind_path = CACHE_DIR / "indicadores.parquet"
    rank_path = CACHE_DIR / "ranking.parquet"
    raw_path = CACHE_DIR / "cti_limpo.parquet"

    if (
        ind_path.exists()
        and rank_path.exists()
        and raw_path.exists()
        and ind_path.stat().st_mtime >= csv.stat().st_mtime
        and rank_path.stat().st_mtime >= csv.stat().st_mtime
        and raw_path.stat().st_mtime >= csv.stat().st_mtime
    ):
        df = otimizar_base_cti(pd.read_parquet(raw_path))
        ind = compactar_indicadores(pd.read_parquet(ind_path))
        ranking = compactar_indicadores(pd.read_parquet(rank_path)).copy()
        if "selo" in ranking.columns:
            ranking["selo"] = ranking["selo"].astype("category")
        return df, ind, ranking

    if os.environ.get("RENDER"):
        raise RuntimeError(
            "Cache parquet nao encontrado no runtime. "
            "Confirme se o Build Command executa `python scripts/precompute_cache.py` antes do start."
        )

    df = load_cti_csv(csv)
    ind, ranking = montar_indicadores(df)
    ind.to_parquet(ind_path, index=False)
    ranking.to_parquet(rank_path, index=False)
    return df, ind, ranking


def _media_por_ano(frame: pd.DataFrame) -> pd.DataFrame:
    if frame is None or frame.empty or "ano_num" not in frame.columns:
        return frame.copy() if isinstance(frame, pd.DataFrame) else pd.DataFrame()
    numeric = [c for c in frame.columns if c not in {"CENA", "ano_num"} and pd.api.types.is_numeric_dtype(frame[c])]
    if not numeric:
        return frame.drop_duplicates(subset=["ano_num"]).sort_values("ano_num")
    out = frame.groupby("ano_num", as_index=False)[numeric].mean()
    if "CENA" in frame.columns:
        out["CENA"] = "Todos"
    return out.sort_values("ano_num")


def build_context_metrics(
    ind: pd.DataFrame,
    ranking: pd.DataFrame,
    *,
    cena_sel: str,
    ano_sel: str | int,
) -> tuple[int, float, pd.DataFrame, pd.DataFrame, pd.Series]:
    """Calcula dados derivados de contexto para filtros ativos."""
    ano_enc = int(ranking["ano_encerramento"].iloc[0]) if len(ranking) and "ano_encerramento" in ranking.columns else 12
    p_ruina = probabilidade_caixa_negativo(ranking)
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
    kpis = calcular_kpis_recorte(foco_raw, foco_ano_raw)
    if is_all_scenarios(cena_sel):
        return ano_enc, p_ruina, _media_por_ano(foco_raw), _media_por_ano(foco_ano_raw), kpis
    return ano_enc, p_ruina, foco_raw, foco_ano_raw, kpis
