"""Carregamento e limpeza da base CTI (independente da UI)."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.config import CACHE_DIR, CSV_PATH


def parse_valor_br(serie: pd.Series) -> pd.Series:
    s = (
        serie.astype(str)
        .str.replace(".", "", regex=False)
        .str.replace(",", ".", regex=False)
    )
    return pd.to_numeric(s, errors="coerce")


def normalizar_conta(serie: pd.Series) -> pd.Series:
    return serie.astype(str).str.replace(r"\s+", " ", regex=True).str.strip()


def magnitude(serie: pd.Series) -> pd.Series:
    """Saldos do BP misturam débito (+) e crédito (−); indicadores usam abs."""
    return serie.abs()


def load_cti_csv(path: Path | None = None) -> pd.DataFrame:
    """Lê Cti.csv. Preferencialmente reutiliza Parquet em cache/ se estiver atualizado."""
    csv_path = Path(path) if path is not None else CSV_PATH
    CACHE_DIR.mkdir(exist_ok=True)
    parquet_path = CACHE_DIR / "cti_limpo.parquet"

    if (
        parquet_path.exists()
        and csv_path.exists()
        and parquet_path.stat().st_mtime >= csv_path.stat().st_mtime
    ):
        return pd.read_parquet(parquet_path)

    # object + engine C: menos RAM que dtype="string"/ArrowStringArray no CSV grande
    df = pd.read_csv(
        csv_path,
        header=None,
        names=["ANO", "CENA", "CONTA", "VALOR"],
        dtype=str,
        engine="c",
        low_memory=False,
    )
    df["CONTA"] = normalizar_conta(df["CONTA"])
    df["VALOR"] = parse_valor_br(df["VALOR"])
    df["ano_num"] = df["ANO"].str.extract(r"(\d+)", expand=False).astype("Int64")
    df.to_parquet(parquet_path, index=False)
    return df


def separar_demonstrativos(df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Replica a organização de organizando.ipynb: BP / DRE / DFC."""
    conta = df["CONTA"].astype("string").str.strip()
    return {
        "BP": df[conta.str.startswith("BAL -", na=False)].copy().reset_index(drop=True),
        "DRE": df[conta.str.startswith("DRE -", na=False)].copy().reset_index(drop=True),
        "DFC": df[conta.str.startswith("FLU -", na=False)].copy().reset_index(drop=True),
    }


def soma_contas(df: pd.DataFrame, nomes: list[str]) -> pd.DataFrame:
    m = df["CONTA"].isin(nomes)
    return (
        df.loc[m]
        .groupby(["ANO", "ano_num", "CENA"], as_index=False)["VALOR"]
        .sum()
        .rename(columns={"VALOR": "valor"})
    )
