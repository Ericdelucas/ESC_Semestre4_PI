"""Carregamento otimizado da base CTI em formato longo."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


BACKEND_DIR = Path(__file__).resolve().parents[1]
CSV_PATH = BACKEND_DIR / "Cti.csv"
CACHE_DIR = BACKEND_DIR / "cache"
CTI_COLUMNS = ["ANO", "CENA", "CONTA", "VALOR"]


def parse_valor_br(serie: pd.Series) -> pd.Series:
    """Converte numeros brasileiros, preservando series numericas."""
    if pd.api.types.is_numeric_dtype(serie):
        return pd.to_numeric(serie, errors="coerce")
    texto = serie.astype(str).str.replace(".", "", regex=False).str.replace(",", ".", regex=False)
    return pd.to_numeric(texto, errors="coerce")


def normalizar_conta(serie: pd.Series) -> pd.Series:
    """Remove espacos redundantes dos nomes de conta."""
    return serie.astype(str).str.replace(r"\s+", " ", regex=True).str.strip()


def magnitude(serie: pd.Series) -> pd.Series:
    """Retorna modulo financeiro para saldos com sinais contabeis mistos."""
    return serie.abs()


def otimizar_base_cti(df: pd.DataFrame) -> pd.DataFrame:
    """Compacta tipos para reduzir uso de memoria."""
    if df.empty:
        return df
    out = df
    if "CONTA" in out.columns:
        out["CONTA"] = normalizar_conta(out["CONTA"]).astype("category")
    if "CENA" in out.columns:
        out["CENA"] = out["CENA"].astype(str).str.strip().astype("category")
    if "ANO" in out.columns:
        out["ANO"] = out["ANO"].astype(str).str.strip().astype("category")
    if "ano_num" in out.columns:
        out["ano_num"] = pd.to_numeric(out["ano_num"], errors="coerce").fillna(0).astype("int8")
    if "VALOR" in out.columns:
        out["VALOR"] = pd.to_numeric(out["VALOR"], errors="coerce").fillna(0.0).astype("float64")
    return out


def _preparar_chunk(chunk: pd.DataFrame) -> pd.DataFrame:
    chunk["CONTA"] = normalizar_conta(chunk["CONTA"])
    chunk["VALOR"] = parse_valor_br(chunk["VALOR"])
    chunk["ano_num"] = chunk["ANO"].astype(str).str.extract(r"(\d+)", expand=False)
    return chunk[["ANO", "CENA", "CONTA", "VALOR", "ano_num"]]


def load_cti_csv(path: Path | str | None = None) -> pd.DataFrame:
    """Le Cti.csv em chunks e reutiliza parquet fresco quando possivel."""
    csv_path = Path(path) if path is not None else CSV_PATH
    CACHE_DIR.mkdir(exist_ok=True)
    parquet_path = CACHE_DIR / "cti_limpo.parquet"

    if (
        parquet_path.exists()
        and csv_path.exists()
        and parquet_path.stat().st_mtime >= csv_path.stat().st_mtime
    ):
        return otimizar_base_cti(pd.read_parquet(parquet_path))

    chunks = pd.read_csv(
        csv_path,
        header=None,
        names=CTI_COLUMNS,
        dtype=str,
        engine="c",
        chunksize=120_000,
        low_memory=False,
    )
    partes = [_preparar_chunk(chunk) for chunk in chunks]
    df = (
        pd.concat(partes, ignore_index=True, copy=False)
        if partes
        else pd.DataFrame(columns=["ANO", "CENA", "CONTA", "VALOR", "ano_num"])
    )
    df = otimizar_base_cti(df)
    df.to_parquet(parquet_path, index=False)
    return df


def separar_demonstrativos(df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Separa BP, DRE e DFC por prefixo da conta."""
    conta = df["CONTA"].astype("string").str.strip()
    return {
        "BP": df[conta.str.startswith("BAL -", na=False)].copy().reset_index(drop=True),
        "DRE": df[conta.str.startswith("DRE -", na=False)].copy().reset_index(drop=True),
        "DFC": df[conta.str.startswith("FLU -", na=False)].copy().reset_index(drop=True),
    }


def soma_contas(df: pd.DataFrame, nomes: list[str]) -> pd.DataFrame:
    """Soma uma lista de contas por ano e cenario."""
    recorte = df.loc[df["CONTA"].isin(nomes)]
    return (
        recorte.groupby(["ANO", "ano_num", "CENA"], as_index=False, observed=True)["VALOR"]
        .sum()
        .rename(columns={"VALOR": "valor"})
    )
