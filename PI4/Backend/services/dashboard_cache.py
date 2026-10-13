"""Leitura/escrita dos parquets e fallback CSV do dashboard.

O diretorio de cache e recebido do orquestrador para manter a configuracao central.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from Backend.data_loader import load_cti_csv, otimizar_base_cti
from Backend.diag import diag
from Backend.metrics.financial_kpis import compactar_indicadores
from Backend.services.metrics_calculator import calcular_indicadores, df_longo_de_indicadores


def cache_paths(cache_dir: Path) -> tuple[Path, Path, Path]:
    return (
        cache_dir / "cti_limpo.parquet",
        cache_dir / "indicadores.parquet",
        cache_dir / "ranking.parquet",
    )


def cache_disponivel(cache_dir: Path) -> bool:
    raw_path, ind_path, rank_path = cache_paths(cache_dir)
    return raw_path.exists() and ind_path.exists() and rank_path.exists()


def _log_volume(tag: str, df: pd.DataFrame, nome: str) -> None:
    if df is None or df.empty:
        diag(tag, f"{nome} vazio")
        return
    contas = int(df["CONTA"].nunique()) if "CONTA" in df.columns else 0
    cenas = int(df["CENA"].nunique()) if "CENA" in df.columns else 0
    anos = int(df["ano_num"].nunique()) if "ano_num" in df.columns else 0
    diag(tag, f"{nome} linhas={len(df):,} shape={df.shape} contas={contas} cenas={cenas} anos={anos}")


def load_cached_dashboard(cache_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Le os 3 parquets do precompute — mesma volumetria que o ambiente local."""
    raw_path, ind_path, rank_path = cache_paths(cache_dir)
    if not (ind_path.exists() and rank_path.exists()):
        raise FileNotFoundError(
            f"Cache em falta: {ind_path.name} / {rank_path.name} em {cache_dir}"
        )
    diag("cache", f"a ler cti_limpo={raw_path} existe={raw_path.exists()} bytes={raw_path.stat().st_size if raw_path.exists() else 0}")
    diag("cache", f"a ler indicadores={ind_path} bytes={ind_path.stat().st_size}")
    diag("cache", f"a ler ranking={rank_path} bytes={rank_path.stat().st_size}")
    if raw_path.exists():
        df = pd.read_parquet(raw_path)
        if "CONTA" in df.columns and not isinstance(df["CONTA"].dtype, pd.CategoricalDtype):
            df = otimizar_base_cti(df)
        _log_volume("cache", df, "cti_limpo")
    else:
        diag("cache", "MISS cti_limpo.parquet — DRE/break-even ficam incompletos")
        df = pd.DataFrame(columns=["ANO", "CENA", "CONTA", "VALOR", "ano_num"])
    ind = compactar_indicadores(pd.read_parquet(ind_path))
    ranking = compactar_indicadores(pd.read_parquet(rank_path)).copy()
    if "selo" in ranking.columns:
        ranking["selo"] = ranking["selo"].astype("category")
    _log_volume("cache", ind, "indicadores")
    diag("cache", f"ranking linhas={len(ranking):,}")
    if df is None or df.empty:
        diag("cache", "aviso: cti_limpo ausente — reconstrucao parcial pelos indicadores")
        df = df_longo_de_indicadores(ind)
    diag("cache", f"cache final df={len(df):,} ind={len(ind):,} ranking={len(ranking):,}")
    return df, ind, ranking


def log_ficheiros_cache(csv: Path, cache_dir: Path) -> None:
    diag("cache", f"CACHE_DIR={cache_dir.resolve()}")
    diag("cache", f"CSV={csv.resolve()} existe={csv.exists()}")
    for path in cache_paths(cache_dir):
        if path.exists():
            diag("cache", f"HIT {path.resolve()} bytes={path.stat().st_size}")
        else:
            diag("cache", f"MISS {path.resolve()}")


def carregar_csv(csv: Path, cache_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    diag("cache", f"FALLBACK CSV a ler {csv.resolve()}")
    df = load_cti_csv(csv, forcar_ficheiro=True)
    diag("cache", f"CSV carregado linhas={len(df):,}; a calcular indicadores")
    ind, ranking = calcular_indicadores(df)
    cache_dir.mkdir(exist_ok=True)
    raw_path, ind_path, rank_path = cache_paths(cache_dir)
    try:
        ind.to_parquet(ind_path, index=False)
        ranking.to_parquet(rank_path, index=False)
        if not raw_path.exists():
            df.to_parquet(raw_path, index=False)
        print("[cache] fallback gravou parquets para a proxima subida", flush=True)
    except Exception as exc:  # noqa: BLE001
        print(f"[cache] aviso: nao gravou parquet ({type(exc).__name__}: {exc})", flush=True)
    return df, ind, ranking
