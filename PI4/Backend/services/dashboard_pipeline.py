"""Pipeline de dados pronto para consumo pelo dashboard."""

from __future__ import annotations

import os
from pathlib import Path

import pandas as pd

from Backend.data_loader import load_cti_csv, otimizar_base_cti
from Backend.diag import diag
from Backend.metrics import calcular_kpis_recorte, montar_indicadores, probabilidade_caixa_negativo
from Backend.metrics.financial_kpis import compactar_indicadores, is_all_scenarios, mapa_contas


BACKEND_DIR = Path(__file__).resolve().parents[1]
CACHE_DIR = BACKEND_DIR / "cache"
CSV_PATH = BACKEND_DIR / "Cti.csv"


def cache_paths() -> tuple[Path, Path, Path]:
    return (
        CACHE_DIR / "cti_limpo.parquet",
        CACHE_DIR / "indicadores.parquet",
        CACHE_DIR / "ranking.parquet",
    )


def _na_render() -> bool:
    return bool(os.environ.get("RENDER"))


def cache_disponivel() -> bool:
    raw_path, ind_path, rank_path = cache_paths()
    return raw_path.exists() and ind_path.exists() and rank_path.exists()


def _log_volume(tag: str, df: pd.DataFrame, nome: str) -> None:
    if df is None or df.empty:
        diag(tag, f"{nome} vazio")
        return
    contas = int(df["CONTA"].nunique()) if "CONTA" in df.columns else 0
    cenas = int(df["CENA"].nunique()) if "CENA" in df.columns else 0
    anos = int(df["ano_num"].nunique()) if "ano_num" in df.columns else 0
    mem = 0
    try:
        mem = int(df.memory_usage(deep=True).sum())
    except Exception:
        pass
    diag(tag, f"{nome} linhas={len(df):,} shape={df.shape} contas={contas} cenas={cenas} anos={anos} ram={mem:,}B")


def df_longo_de_indicadores(ind: pd.DataFrame) -> pd.DataFrame:
    """Reconstroi CONTA/VALOR a partir dos indicadores — sem o CSV de 1M linhas."""
    if ind is None or ind.empty:
        diag("cache", "df_longo: indicadores vazios")
        return pd.DataFrame(columns=["ANO", "CENA", "CONTA", "VALOR", "ano_num"])
    inverso: dict[str, str] = {}
    for conta, campo in mapa_contas().items():
        inverso.setdefault(campo, conta)
    eixos = [col for col in ("ANO", "ano_num", "CENA") if col in ind.columns]
    partes: list[pd.DataFrame] = []
    for campo, conta in inverso.items():
        if campo not in ind.columns:
            continue
        bloco = ind[eixos].copy()
        bloco["CONTA"] = conta
        bloco["VALOR"] = pd.to_numeric(ind[campo], errors="coerce").fillna(0.0)
        partes.append(bloco)
    if not partes:
        diag("cache", "df_longo: nenhum campo mapeado")
        return pd.DataFrame(columns=["ANO", "CENA", "CONTA", "VALOR", "ano_num"])
    out = otimizar_base_cti(pd.concat(partes, ignore_index=True))
    diag("cache", f"df_longo reconstruido shape={out.shape} contas={out['CONTA'].nunique()} cenas={out['CENA'].nunique()}")
    return out


def load_cached_dashboard() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Le os 3 parquets do precompute — mesma volumetria que o ambiente local."""
    raw_path, ind_path, rank_path = cache_paths()
    if not (ind_path.exists() and rank_path.exists()):
        raise FileNotFoundError(
            f"Cache em falta: {ind_path.name} / {rank_path.name} em {CACHE_DIR}"
        )
    diag("cache", f"a ler cti_limpo={raw_path} existe={raw_path.exists()} bytes={raw_path.stat().st_size if raw_path.exists() else 0}")
    diag("cache", f"a ler indicadores={ind_path} bytes={ind_path.stat().st_size}")
    diag("cache", f"a ler ranking={rank_path} bytes={rank_path.stat().st_size}")
    if raw_path.exists():
        df = otimizar_base_cti(pd.read_parquet(raw_path))
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


def _log_ficheiros_cache(csv: Path) -> None:
    diag("cache", f"CACHE_DIR={CACHE_DIR.resolve()}")
    diag("cache", f"CSV={csv.resolve()} existe={csv.exists()}")
    for path in cache_paths():
        if path.exists():
            diag("cache", f"HIT {path.resolve()} bytes={path.stat().st_size}")
        else:
            diag("cache", f"MISS {path.resolve()}")


def _carregar_csv(csv: Path) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    diag("cache", f"FALLBACK CSV a ler {csv.resolve()}")
    df = load_cti_csv(csv, forcar_ficheiro=True)
    diag("cache", f"CSV carregado linhas={len(df):,}; a calcular indicadores")
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
    """Parquet do precompute; CSV so em ambiente local se o cache faltar."""
    diag("cache", "fonte=local (parquet/CSV) — Supabase desligado")
    csv = Path(csv_path)
    _log_ficheiros_cache(csv)
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
    if _na_render():
        diag("cache", "RENDER: Cti.csv bloqueado em runtime — sem carga de 1M linhas")
        raise RuntimeError(
            "Cache de indicadores em falta na Render. Cti.csv nao e lido em runtime."
        )
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
