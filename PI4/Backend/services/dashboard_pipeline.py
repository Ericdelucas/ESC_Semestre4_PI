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


def cache_paths() -> tuple[Path, Path, Path]:
    return (
        CACHE_DIR / "cti_limpo.parquet",
        CACHE_DIR / "indicadores.parquet",
        CACHE_DIR / "ranking.parquet",
    )


def cache_disponivel() -> bool:
    raw_path, ind_path, rank_path = cache_paths()
    return ind_path.exists() and rank_path.exists() and raw_path.exists()


def load_cached_dashboard() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Le apenas os parquets do precompute. Nao relê o CSV nem recalcula KPIs."""
    raw_path, ind_path, rank_path = cache_paths()
    if not (ind_path.exists() and rank_path.exists()):
        raise FileNotFoundError(
            f"Cache em falta: {ind_path.name} / {rank_path.name} em {CACHE_DIR}"
        )
    df = pd.read_parquet(raw_path) if raw_path.exists() else pd.DataFrame()
    if not df.empty:
        df = otimizar_base_cti(df)
    ind = compactar_indicadores(pd.read_parquet(ind_path))
    ranking = compactar_indicadores(pd.read_parquet(rank_path)).copy()
    if "selo" in ranking.columns:
        ranking["selo"] = ranking["selo"].astype("category")
    return df, ind, ranking


def _log_ficheiros_cache(csv: Path) -> None:
    print(f"[cache] CACHE_DIR={CACHE_DIR.resolve()}", flush=True)
    print(f"[cache] CSV={csv.resolve()} existe={csv.exists()}", flush=True)
    for path in cache_paths():
        if path.exists():
            print(f"[cache] HIT {path.resolve()} bytes={path.stat().st_size}", flush=True)
        else:
            print(f"[cache] MISS {path.resolve()}", flush=True)


def _carregar_csv(csv: Path) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    print(f"[cache] FALLBACK CSV a ler {csv.resolve()}", flush=True)
    df = load_cti_csv(csv)
    print(f"[cache] CSV carregado linhas={len(df):,}; a calcular indicadores", flush=True)
    ind, ranking = montar_indicadores(df)
    CACHE_DIR.mkdir(exist_ok=True)
    raw_path, ind_path, rank_path = cache_paths()
    try:
        ind.to_parquet(ind_path, index=False)
        ranking.to_parquet(rank_path, index=False)
        if not raw_path.exists():
            df.to_parquet(raw_path, index=False)
        print("[cache] fallback gravou parquets para a proxima subida", flush=True)
    except Exception as exc:  # noqa: BLE001
        print(f"[cache] aviso: nao gravou parquet ({type(exc).__name__}: {exc})", flush=True)
    return df, ind, ranking


def prepare_dashboard_data(csv_path: str | Path = CSV_PATH) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """PostgreSQL (DATABASE_URL) tem prioridade; senao parquet/CSV local."""
    try:
        from Backend.data_loader.sql_reader import load_dashboard_from_sql, postgres_disponivel

        if postgres_disponivel():
            print("[cache] fonte=PostgreSQL tabela=cti_dados", flush=True)
            return load_dashboard_from_sql()
    except Exception as exc:  # noqa: BLE001
        print(f"[cache] PostgreSQL falhou {type(exc).__name__}: {exc}", flush=True)
        if os.environ.get("RENDER"):
            raise

    csv = Path(csv_path)
    _log_ficheiros_cache(csv)
    if cache_disponivel():
        try:
            print("[cache] a ler os 3 parquets", flush=True)
            dados = load_cached_dashboard()
            print("[cache] parquet OK", flush=True)
            return dados
        except Exception as exc:  # noqa: BLE001
            print(f"[cache] leitura parquet falhou {type(exc).__name__}: {exc}", flush=True)
    else:
        print("[cache] parquet incompleto — fallback CSV", flush=True)
    return _carregar_csv(csv)


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
