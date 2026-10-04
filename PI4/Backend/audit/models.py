"""Modelos internos da auditoria."""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ColumnProfile:
    """Perfil acumulado de uma coluna auditada."""

    nulls: int = 0
    empty_strings: int = 0
    dtype_samples: Counter[str] = field(default_factory=Counter)
    parse_failures: int = 0
    min_value: float | None = None
    max_value: float | None = None


@dataclass
class AuditAccumulator:
    """Estado incremental da auditoria em chunks."""

    rows: int = 0
    columns: list[str] = field(default_factory=list)
    memory_bytes_estimate: int = 0
    column_profiles: dict[str, ColumnProfile] = field(default_factory=lambda: defaultdict(ColumnProfile))
    full_row_counts: Counter[tuple[Any, ...]] = field(default_factory=Counter)
    business_key_counts: Counter[tuple[Any, ...]] = field(default_factory=Counter)
    account_counts: Counter[str] = field(default_factory=Counter)
    account_totals: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    account_abs_totals: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    account_non_null: Counter[str] = field(default_factory=Counter)
    account_nulls: Counter[str] = field(default_factory=Counter)
    scenario_count: set[str] = field(default_factory=set)
    years_seen: set[int] = field(default_factory=set)
    missing_critical_examples: list[dict[str, Any]] = field(default_factory=list)
    negative_unexpected_examples: list[dict[str, Any]] = field(default_factory=list)
    out_of_period_examples: list[dict[str, Any]] = field(default_factory=list)
    parse_error_examples: list[dict[str, Any]] = field(default_factory=list)

