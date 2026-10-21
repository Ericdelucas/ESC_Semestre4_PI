# ele define os modelos internos da auditoria, que sao usados para acumular contadores e perfis de colunas em memoria
"""Modelos internos da auditoria."""

# ele importa a anotacao de futuras funcionalidades do python
from __future__ import annotations

# ele importa o Counter e o defaultdict do modulo collections, que sao usados para contar elementos em iteraveis e criar dicionarios com valores padrao
from collections import Counter, defaultdict
# ele importa o dataclass e o field do modulo dataclasses, que sao usados para criar classes de dados com campos padrao
from dataclasses import dataclass, field
# essa biblioteca typing e usada para indicar que um valor pode ser de qualquer tipo
from typing import Any

# esse @ e para indicar que a classe ColumnProfile e uma classe de dados, que tem campos padrao e metodos gerados automaticamente
@dataclass
# essa classe representa o perfil acumulado de uma coluna auditada, que armazena contadores de valores nulos, strings vazias, tipos de dados, falhas de parse e valores minimos e maximos
class ColumnProfile:
    """Perfil acumulado de uma coluna auditada."""

    # ele define os campos da classe ColumnProfile, que sao inicializados com valores padrao
    nulls: int = 0
    empty_strings: int = 0
    dtype_samples: Counter[str] = field(default_factory=Counter)
    parse_failures: int = 0
    min_value: float | None = None
    max_value: float | None = None

# agora ele define a classe AuditAccumulator, que representa o estado incremental da auditoria em chunks, e armazena contadores de linhas, colunas, memoria, perfis de colunas, contadores de duplicidade, contadores de contas, conjuntos de cenarios e anos vistos, e exemplos de erros
@dataclass
#essa classe representa o estado incremental da auditoria em chunks, e armazena contadores de linhas, colunas, memoria, perfis de colunas, contadores de duplicidade, contadores de contas, conjuntos de cenarios e anos vistos, e exemplos de erros
class AuditAccumulator:
    """Estado incremental da auditoria em chunks."""
    # ele define os campos da classe AuditAccumulator, que sao inicializados com valores padrao
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

