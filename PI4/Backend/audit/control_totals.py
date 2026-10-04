"""Totais de controle e reconciliacao com CTI/controladoria."""

from __future__ import annotations

from typing import Any

import pandas as pd

from .config import CONTROL_ACCOUNT_GROUPS
from .models import AuditAccumulator


def update_accounts(acc: AuditAccumulator, chunk: pd.DataFrame) -> None:
    """Acumula totais, contagens e qualidade por conta."""
    acc.account_counts.update(chunk["CONTA"].dropna().astype(str).tolist())
    acc.scenario_count.update(chunk["CENA"].dropna().astype(str).tolist())
    acc.years_seen.update(int(v) for v in chunk["ano_num"].dropna().astype(int).tolist())

    for conta, series in chunk.groupby("CONTA", dropna=False, observed=True)["VALOR"]:
        conta_key = str(conta)
        numeric = pd.to_numeric(series, errors="coerce")
        acc.account_totals[conta_key] += float(numeric.sum(skipna=True))
        acc.account_abs_totals[conta_key] += float(numeric.abs().sum(skipna=True))
        acc.account_non_null[conta_key] += int(numeric.notna().sum())
        acc.account_nulls[conta_key] += int(numeric.isna().sum())


def control_totals(acc: AuditAccumulator) -> dict[str, Any]:
    """Calcula somas, somas absolutas e medias por grupo de controle."""
    controls: dict[str, Any] = {}
    for group_name, accounts in CONTROL_ACCOUNT_GROUPS.items():
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

