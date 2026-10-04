"""Resolucao resiliente de colunas financeiras."""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Iterable

import pandas as pd


def repair_mojibake(text: object) -> str:
    """Tenta desfazer mojibake comum de UTF-8 lido como Latin-1."""
    value = str(text).strip()
    for _ in range(3):
        try:
            repaired = value.encode("latin1").decode("utf-8")
        except (UnicodeEncodeError, UnicodeDecodeError):
            break
        if repaired == value:
            break
        value = repaired
    return value


def normalize_label(text: object) -> str:
    """Normaliza texto removendo acentos, simbolos e espacos redundantes."""
    repaired = repair_mojibake(text).casefold()
    ascii_text = unicodedata.normalize("NFKD", repaired).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", " ", ascii_text).strip()


def resolve_column(df: pd.DataFrame, aliases: Iterable[str], *, required: bool = True) -> str | None:
    """Retorna a coluna que corresponde a qualquer alias normalizado."""
    index = {normalize_label(col): col for col in df.columns}
    for alias in aliases:
        key = normalize_label(alias)
        if key in index:
            return str(index[key])
    if required:
        raise KeyError(f"Coluna nao encontrada. Aliases tentados: {list(aliases)}")
    return None


def series_by_alias(df: pd.DataFrame, aliases: Iterable[str], default: float = 0.0) -> pd.Series:
    """Recupera serie numerica por aliases, com fallback constante."""
    col = resolve_column(df, aliases, required=False)
    if col is None:
        return pd.Series(default, index=df.index, dtype="float64")
    return pd.to_numeric(df[col], errors="coerce").fillna(default)
