"""Deteccao de duplicidades completas e por chave de negocio."""
# ele tras a anotacao de futuras funcionalidades do Python
from __future__ import annotations

# ele importa o Counter do modulo collections, que e usado para contar elementos em iteraveis
from collections import Counter
# ele importa Any do modulo typing, que e usado para indicar que um valor pode ser de qualquer tipo
from typing import Any

# ele importa o pandas, que e usado para manipular os dados da auditoria
import pandas as pd

# ele importa as constantes BUSINESS_KEY e EXPECTED_COLUMNS do modulo de configuracao da auditoria, que definem as colunas que formam a chave de negocio e as colunas esperadas no arquivo Cti.csv
from .config import BUSINESS_KEY, EXPECTED_COLUMNS
# ele importa a classe AuditAccumulator do modulo de modelos da auditoria, que e usada para acumular contadores de duplicidade
from .models import AuditAccumulator


# e uma funcao que atualiza os contadores de duplicidade em memoria compacta, a partir de um chunk de dados do arquivo cti.csv
def update_duplicates(acc: AuditAccumulator, chunk: pd.DataFrame) -> None:
    """Acumula contadores de duplicidade em memoria compacta."""
    # ele faz um loop sobre cada linha do chunk, e atualiza o contador de duplicidade completa com a tupla das colunas esperadas, e o contador de duplicidade por chave de negocio com a tupla das colunas da chave de negocio
    for row in chunk[EXPECTED_COLUMNS].astype(object).where(pd.notna(chunk[EXPECTED_COLUMNS]), None).itertuples(index=False, name=None):
        acc.full_row_counts[row] += 1
    # ele faz a mesma coisa para a chave de negocio, mas usando as colunas da chave de negocio
    for row in chunk[BUSINESS_KEY].astype(object).where(pd.notna(chunk[BUSINESS_KEY]), None).itertuples(index=False, name=None):
        acc.business_key_counts[row] += 1

# ele resume os grupos duplicados e exemplos a partir de um contador de tuplas, limitando o numero de exemplos retornados
def summarize_duplicates(counter: Counter[tuple[Any, ...]], columns: list[str], sample_limit: int) -> dict[str, Any]:
    """Resume grupos duplicados e exemplos."""
    duplicated = [(key, count) for key, count in counter.items() if count > 1]
    examples = [{"count": count, **dict(zip(columns, key))} for key, count in duplicated[:sample_limit]]
    # e ele retorna apenas o numero de grupos duplicados, o numero total de linhas duplicadas, o numero de linhas extras (duplicadas menos uma), e os exemplos limitados
    return {
        "duplicated_groups": len(duplicated),
        "duplicated_rows": sum(count for _, count in duplicated),
        "extra_rows": sum(count - 1 for _, count in duplicated),
        "examples": examples,
    }

