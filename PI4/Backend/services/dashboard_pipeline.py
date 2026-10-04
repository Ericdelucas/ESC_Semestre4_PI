"""Pipeline de dados pronto para consumo pelo dashboard."""

from __future__ import annotations

import os
from pathlib import Path

import pandas as pd

from Backend.data_loader import load_cti_csv, otimizar_base_cti
from Backend.metrics import calcular_kpis_recorte, montar_indicadores, probabilidade_caixa_negativo
from Backend.metrics.financial_kpis import compactar_indicadores


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


def build_context_metrics(
    ind: pd.DataFrame,
    ranking: pd.DataFrame,
    *,
    cena_sel: str,
    ano_sel: str | int,
) -> tuple[int, float, pd.DataFrame, pd.DataFrame, pd.Series]:
    """Calcula dados derivados de contexto para filtros ativos."""
    ano_enc = int(ranking["ano_encerramento"].iloc[0]) if len(ranking) else 12
    p_ruina = probabilidade_caixa_negativo(ranking)
    foco = ind.loc[ind["CENA"] == cena_sel].sort_values("ano_num")
    if ano_sel == "Todos":
        foco_ano = foco
    else:
        ano_num = int(ano_sel)
        foco_ano = foco.loc[pd.to_numeric(foco["ano_num"], errors="coerce") == ano_num]
    kpis = calcular_kpis_recorte(foco, foco_ano)
    return ano_enc, p_ruina, foco, foco_ano, kpis
