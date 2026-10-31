# ele faz a interseção das contas a receber com as contas de peças de contas, e ordena o resultado
"""Totais de controle e reconciliacao com CTI/controladoria."""
# isso serve para evitar importacoes circulares, pois o runner importa o config
from __future__ import annotations
# ele importa o config antes de ser importado, o que causaria erro de importacao circular
from typing import Any
# ele seve para baixar a biblioteca pandas, que é usada para manipular os dados da auditoria
import pandas as pd

# serve para importar o dicionário de grupos de contas de controle do módulo de configuração da auditoria
from .config import CONTROL_ACCOUNT_GROUPS
# ele importa a classe AuditAccumulator do módulo de modelos da auditoria, que é usada para acumular totais e contagens por conta
from .models import AuditAccumulator


# e uma funcao que atualiza os totais, contagens e qualidade por conta individual, a partir de um chunk de dados do arquivo Cti.csv
def update_accounts(acc: AuditAccumulator, chunk: pd.DataFrame) -> None:
    """Acumula totais, contagens e qualidade por conta."""
    # ele atualiza o dicionário de contagens de contas, adicionando as contas do chunk atual
    acc.account_counts.update(chunk["CONTA"].dropna().astype(str).tolist())
    # esse atualiza o conjunto de cenarios vistos, adicionando os cenarios do chunk atual
    acc.scenario_count.update(chunk["CENA"].dropna().astype(str).tolist())
    # esse atualiza o conjunto de anos vistos, adicionando os anos do chunk atual
    acc.years_seen.update(int(v) for v in chunk["ano_num"].dropna().astype(int).tolist())


    # ele repete para cada grupo de contas de controle, e para cada conta do grupo, ele calcula a soma, soma absoluta, contagem de valores nao nulos e contagem de valores nulos, e atualiza os dicionarios correspondentes no acumulador
    for conta, series in chunk.groupby("CONTA", dropna=False, observed=True)["VALOR"]:
        # ele pega a conta_key como string, e converte a serie de valores para numerico, ignorando erros
        conta_key = str(conta)
        # ele converte a serie de valores para numerico, ignorando erros
        numeric = pd.to_numeric(series, errors="coerce")
        # ele atualiza os totais, somas absolutas, contagens de valores nao nulos e contagens de valores nulos para a conta atual no acumulador
        acc.account_totals[conta_key] += float(numeric.sum(skipna=True))
        # o acc.account_abs_totals[conta_key] += float(numeric.abs().sum(skipna=True)) atualiza a soma absoluta dos valores da conta atual no acumulador
        acc.account_abs_totals[conta_key] += float(numeric.abs().sum(skipna=True))
        acc.account_non_null[conta_key] += int(numeric.notna().sum())
        acc.account_nulls[conta_key] += int(numeric.isna().sum())

# esta funcao calcula os totais de controle, somas absolutas e medias por grupo de controle, a partir dos totais acumulados por conta individual
def control_totals(acc: AuditAccumulator) -> dict[str, Any]:
    """Calcula somas, somas absolutas e medias por grupo de controle."""
    # ele cria um dicionário vazio para armazenar os totais de controle por grupo
    controls: dict[str, Any] = {}
    # ele itera sobre os grupos de contas de controle definidos no dicionário CONTROL_ACCOUNT_GROUPS, e para cada grupo, ele calcula a soma dos totais, a soma das somas absolutas, a contagem de valores nao nulos e a contagem de valores nulos, e armazena essas informacoes no dicionario controls
    for group_name, accounts in CONTROL_ACCOUNT_GROUPS.items():
        # o total e de cada conta do grupo, e a soma de todos os totais das contas do grupo
        total = sum(acc.account_totals.get(conta, 0.0) for conta in accounts)
        abs_total = sum(acc.account_abs_totals.get(conta, 0.0) for conta in accounts)
        count = sum(acc.account_non_null.get(conta, 0) for conta in accounts)
        controls[group_name] = {
            "accounts": accounts,
            "sum": round(total, 2),
            "abs_sum": round(abs_total, 2),
            "mean": round(total / count, 2) if count else None,
            "non_null_values": count,
            "missing_values": sum(acc.account_nulls.get(conta, 0) for conta in accounts),
        }
    return controls

# esta funcao resume a qualidade e os totais por conta individual a partir dos totais acumulados por conta individual
def account_quality(acc: AuditAccumulator) -> dict[str, Any]:
    """Resume qualidade e totais por conta individual."""
    quality: dict[str, Any] = {}
    for conta in sorted(acc.account_counts):
        total = acc.account_counts[conta]
        missing = acc.account_nulls.get(conta, 0)
        quality[conta] = {
            "rows": total,
            "value_nulls": missing,
            "value_null_pct": round((missing / total) * 100, 4) if total else 0.0,
            "sum": round(acc.account_totals.get(conta, 0.0), 2),
            "abs_sum": round(acc.account_abs_totals.get(conta, 0.0), 2),
        }
    return quality

