"""Deteccao de duplicidades completas e por chave de negocio."""

from __future__ import annotations

from collections import Counter
from typing import Any

import pandas as pd

from .config import BUSINESS_KEY, EXPECTED_COLUMNS
from .models import AuditAccumulator


def update_duplicates(acc: AuditAccumulator, chunk: pd.DataFrame) -> None:
    """Acumula contadores de duplicidade em memoria compacta."""
    for row in chunk[EXPECTED_COLUMNS].astype(object).where(pd.notna(chunk[EXPECTED_COLUMNS]), None).itertuples(index=False, name=None):
        acc.full_row_counts[row] += 1
    for row in chunk[BUSINESS_KEY].astype(object).where(pd.notna(chunk[BUSINESS_KEY]), None).itertuples(index=False, name=None):
        acc.business_key_counts[row] += 1


def summarize_duplicates(counter: Counter[tuple[Any, ...]], columns: list[str], sample_limit: int) -> dict[str, Any]:
    """Resume grupos duplicados e exemplos."""
    duplicated = [(key, count) for key, count in counter.items() if count > 1]
    examples = [{"count": count, **dict(zip(columns, key))} for key, count in duplicated[:sample_limit]]
    return {
        "duplicated_groups": len(duplicated),
        "duplicated_rows": sum(count for _, count in duplicated),
        "extra_rows": sum(count - 1 for _, count in duplicated),
        "examples": examples,
    }

