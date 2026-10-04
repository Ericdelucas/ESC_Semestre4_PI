"""Verificacao estrutural: leitura, colunas, tipos, nulos e anomalias."""

from __future__ import annotations

from typing import Any, Iterable

import pandas as pd

from Backend.data_loader import normalizar_conta, parse_valor_br

from .config import (
    CRITICAL_VALUE_ACCOUNTS,
    EXPECTED_COLUMNS,
    EXPECTED_NON_NEGATIVE_ACCOUNTS,
)
from .models import AuditAccumulator


def sample_records(df: pd.DataFrame, limit: int = 5) -> list[dict[str, Any]]:
    """Serializa exemplos pequenos sem valores pandas nao JSON."""
    if df.empty:
        return []
    sample = df.head(limit).astype(object)
    records = sample.where(pd.notna(sample), None).to_dict(orient="records")
    return [{str(k): v for k, v in record.items()} for record in records]


def read_csv_chunks(path, chunksize: int) -> Iterable[pd.DataFrame]:
    """Le CSV CTI em chunks com tratamento de erros claro."""
    if not path.exists():
        raise FileNotFoundError(f"Arquivo base nao encontrado: {path}")
    try:
        yield from pd.read_csv(
            path,
            header=None,
            names=EXPECTED_COLUMNS,
            dtype=str,
            engine="c",
            chunksize=chunksize,
            low_memory=False,
        )
    except pd.errors.EmptyDataError as exc:
        raise ValueError(f"Arquivo CSV vazio: {path}") from exc
    except UnicodeDecodeError as exc:
        raise ValueError(f"Falha de encoding ao ler CSV: {path}") from exc


def read_sql_chunks(db_url: str, table: str, chunksize: int) -> Iterable[pd.DataFrame]:
    """Le uma tabela SQL em chunks via SQLAlchemy."""
    try:
        from sqlalchemy import create_engine, text
    except ImportError as exc:
        raise RuntimeError(
            "Para auditar PostgreSQL/Supabase, instale sqlalchemy e o driver do banco "
            "(ex.: psycopg2-binary ou psycopg)."
        ) from exc

    try:
        engine = create_engine(db_url)
        with engine.connect() as conn:
            yield from pd.read_sql_query(text(f"SELECT * FROM {table}"), conn, chunksize=chunksize)
    except Exception as exc:
        raise RuntimeError(f"Falha ao ler tabela SQL '{table}': {exc}") from exc


def prepare_cti_chunk(chunk: pd.DataFrame) -> pd.DataFrame:
    """Normaliza nomes, datas de ano e valores monetarios."""
    chunk = chunk.rename(columns={col: str(col).upper() for col in chunk.columns})
    missing = [col for col in EXPECTED_COLUMNS if col not in chunk.columns]
    if missing:
        raise KeyError(f"Colunas esperadas ausentes: {', '.join(missing)}")

    out = chunk[EXPECTED_COLUMNS].copy()
    out["ANO"] = out["ANO"].astype("string").str.strip()
    out["CENA"] = out["CENA"].astype("string").str.strip()
    out["CONTA"] = normalizar_conta(out["CONTA"])
    out["VALOR_RAW"] = out["VALOR"]
    out["VALOR"] = (
        pd.to_numeric(out["VALOR"], errors="coerce")
        if pd.api.types.is_numeric_dtype(out["VALOR"])
        else parse_valor_br(out["VALOR"])
    )
    out["ano_num"] = pd.to_numeric(out["ANO"].str.extract(r"(\d+)", expand=False), errors="coerce")
    return out


def update_profiles(acc: AuditAccumulator, chunk: pd.DataFrame) -> None:
    """Acumula perfil de tipos, nulos e limites numericos."""
    acc.rows += len(chunk)
    acc.columns = list(chunk.columns)
    acc.memory_bytes_estimate = max(acc.memory_bytes_estimate, int(chunk.memory_usage(deep=True).sum()))

    for col in EXPECTED_COLUMNS + ["ano_num"]:
        if col not in chunk.columns:
            continue
        profile = acc.column_profiles[col]
        series = chunk[col]
        profile.nulls += int(series.isna().sum())
        if series.dtype == object or str(series.dtype).startswith("string"):
            profile.empty_strings += int(series.astype("string").str.strip().eq("").fillna(False).sum())
        profile.dtype_samples[str(series.dtype)] += len(series)
        if col in {"VALOR", "ano_num"}:
            profile.parse_failures += int(series.isna().sum())
            numeric = pd.to_numeric(series, errors="coerce").dropna()
            if not numeric.empty:
                min_val = float(numeric.min())
                max_val = float(numeric.max())
                profile.min_value = min_val if profile.min_value is None else min(profile.min_value, min_val)
                profile.max_value = max_val if profile.max_value is None else max(profile.max_value, max_val)


def update_anomalies(
    acc: AuditAccumulator,
    chunk: pd.DataFrame,
    concession_year_min: int,
    concession_year_max: int,
    sample_limit: int,
) -> None:
    """Registra exemplos de ausentes criticos, negativos e periodos invalidos."""
    critical_mask = chunk["CONTA"].isin(CRITICAL_VALUE_ACCOUNTS)
    missing_critical = chunk.loc[
        critical_mask
        & (
            chunk["VALOR"].isna()
            | chunk["ANO"].isna()
            | chunk["CENA"].isna()
            | chunk["CONTA"].isna()
            | chunk["ano_num"].isna()
        ),
        EXPECTED_COLUMNS + ["ano_num"],
    ]
    if len(acc.missing_critical_examples) < sample_limit:
        acc.missing_critical_examples.extend(sample_records(missing_critical, sample_limit - len(acc.missing_critical_examples)))

    negative_rows = chunk.loc[
        chunk["CONTA"].isin(EXPECTED_NON_NEGATIVE_ACCOUNTS) & (chunk["VALOR"] < 0),
        EXPECTED_COLUMNS + ["ano_num"],
    ]
    if len(acc.negative_unexpected_examples) < sample_limit:
        acc.negative_unexpected_examples.extend(sample_records(negative_rows, sample_limit - len(acc.negative_unexpected_examples)))

    out_period_rows = chunk.loc[
        chunk["ano_num"].isna() | ~chunk["ano_num"].between(concession_year_min, concession_year_max, inclusive="both"),
        EXPECTED_COLUMNS + ["ano_num"],
    ]
    if len(acc.out_of_period_examples) < sample_limit:
        acc.out_of_period_examples.extend(sample_records(out_period_rows, sample_limit - len(acc.out_of_period_examples)))

    parse_error_rows = chunk.loc[chunk["VALOR"].isna(), ["ANO", "CENA", "CONTA", "VALOR_RAW"]]
    if len(acc.parse_error_examples) < sample_limit:
        acc.parse_error_examples.extend(sample_records(parse_error_rows, sample_limit - len(acc.parse_error_examples)))


def summarize_columns(acc: AuditAccumulator) -> dict[str, Any]:
    """Gera resumo de qualidade por coluna."""
    out: dict[str, Any] = {}
    for col, profile in acc.column_profiles.items():
        out[col] = {
            "dtype_samples": dict(profile.dtype_samples),
            "nulls": profile.nulls,
            "null_pct": round((profile.nulls / acc.rows) * 100, 4) if acc.rows else 0.0,
            "empty_strings": profile.empty_strings,
            "parse_failures": profile.parse_failures if col in {"VALOR", "ano_num"} else 0,
            "min": profile.min_value,
            "max": profile.max_value,
        }
    return out


def imputation_rules() -> dict[str, str]:
    """Regras metodologicas para ausentes."""
    return {
        "VALOR em conta critica": "Nao imputar automaticamente; bloquear reconciliacao e corrigir na origem ou justificar ajuste tecnico.",
        "VALOR em conta nao critica": "Manter NaN no relatorio; o pipeline analitico atual converte para 0 apenas depois da leitura controlada.",
        "ANO/CENA/CONTA ausente": "Descartar ou corrigir na origem, pois compoe chave de negocio.",
        "ANO fora do horizonte": "Descartar do dashboard ate validacao do periodo de concessao.",
    }

