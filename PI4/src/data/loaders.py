"""Carregamento e limpeza da base CTI (independente da UI)."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.config import CSV_PATH


def parse_valor_br(serie: pd.Series) -> pd.Series:
    s = serie.astype("string").str.replace(".", "", regex=False).str.replace(",", ".", regex=False)
    return pd.to_numeric(s, errors="coerce")


def normalizar_conta(serie: pd.Series) -> pd.Series:
    return serie.astype("string").str.replace(r"\s+", " ", regex=True).str.strip()


def magnitude(serie: pd.Series) -> pd.Series:
    """Saldos do BP misturam débito (+) e crédito (−); indicadores usam abs."""
    return serie.abs()


def load_cti_csv(path: Path | None = None) -> pd.DataFrame:
    csv_path = path or CSV_PATH
    df = pd.read_csv(csv_path, header=None, names=["ANO", "CENA", "CONTA", "VALOR"])
    df["CONTA"] = normalizar_conta(df["CONTA"])
    df["VALOR"] = parse_valor_br(df["VALOR"])
    df["ano_num"] = df["ANO"].astype(str).str.extract(r"(\d+)")[0].astype("Int64")
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
