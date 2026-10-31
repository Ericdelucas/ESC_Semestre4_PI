"""Orquestrador de dados do dashboard, com a API publica original."""
from __future__ import annotations

import os
from pathlib import Path

import pandas as pd

from Backend.diag import diag
from Backend.services import dashboard_cache, metrics_calculator


BACKEND_DIR = Path(__file__).resolve().parents[1]
CACHE_DIR = BACKEND_DIR / "cache"
CSV_PATH = BACKEND_DIR / "Cti.csv"


def cache_paths() -> tuple[Path, Path, Path]:
    return dashboard_cache.cache_paths(CACHE_DIR)


def cache_disponivel() -> bool:
    return dashboard_cache.cache_disponivel(CACHE_DIR)


def df_longo_de_indicadores(ind: pd.DataFrame) -> pd.DataFrame:
    """Reconstroi CONTA/VALOR a partir dos indicadores — sem o CSV de 1M linhas."""
    return metrics_calculator.df_longo_de_indicadores(ind)


def load_cached_dashboard() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Le os 3 parquets do precompute — mesma volumetria que o ambiente local."""
    return dashboard_cache.load_cached_dashboard(CACHE_DIR)


def prepare_dashboard_data(csv_path: str | Path = CSV_PATH) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Parquet do precompute; CSV so em ambiente local se o cache faltar."""
    diag("cache", "fonte=local (parquet/CSV) — Supabase desligado")
    csv = Path(csv_path)
    dashboard_cache.log_ficheiros_cache(csv, CACHE_DIR)
    if cache_disponivel():
        try:
            diag("cache", "a ler os 3 parquets")
            dados = load_cached_dashboard()
            diag("cache", f"parquet OK df={len(dados[0]):,} ind={len(dados[1]):,} ranking={len(dados[2]):,}")
            return dados
        except Exception as exc:  # noqa: BLE001
            print(f"[cache] leitura parquet falhou {type(exc).__name__}: {exc}", flush=True)
    else:
        diag("cache", "parquet incompleto")
    if os.environ.get("RENDER"):
        diag("cache", "RENDER: Cti.csv bloqueado em runtime — sem carga de 1M linhas")
        raise RuntimeError(
            "Cache de indicadores em falta na Render. Cti.csv nao e lido em runtime."
        )
    return dashboard_cache.carregar_csv(csv, CACHE_DIR)


def build_context_metrics(
    ind: pd.DataFrame,
    ranking: pd.DataFrame,
    *,
    cena_sel: str,
    ano_sel: str | int,
) -> tuple[int, float, pd.DataFrame, pd.DataFrame, pd.Series]:
    """Calcula dados derivados de contexto para filtros ativos."""
    return metrics_calculator.build_context_metrics(ind, ranking, cena_sel=cena_sel, ano_sel=ano_sel)
