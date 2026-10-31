"""Calculo de series temporais para metricas financeiras dinamicas."""

from __future__ import annotations

import pandas as pd

from src.models.formatting.scenarios import is_all_scenarios

from .catalog import FINANCIAL_METRICS_DICT
from .utils import _normalizar_aliases, _to_number


def contas_necessarias() -> list[str]:
    return sorted(
        {
            "BAL  - Patrimônio Líquido",
            "BAL - Patrimônio Líquido",
            "BAL - Ativo Circulante",
            "BAL - Contas a Receber - Clientes",
            "BAL - Disponível",
            "BAL - Empréstimos",
            "BAL - Estoques Diversos",
            "BAL - Exigível a Longo Prazo",
            "BAL - Fornecedores",
            "BAL - Passivo Circulante",
            "BAL - Realizável a Longo Prazo",
            "BAL - Total do Ativo",
            "DRE - Custos",
            "DRE - Despesas Financeiras",
            "DRE - EBITDA",
            "DRE - Receita",
            "DRE - Resultado Líquido",
            "DRE - Resultado Operacional",
            "FLU - Despesas Financeiras",
            "FLU - Geração de Caixa",
            "FLU - Investimentos",
        }
    )


def metric_timeseries(df: pd.DataFrame, cena: str, metric_name: str) -> pd.DataFrame:
    metric = FINANCIAL_METRICS_DICT[metric_name]
    contas = df["CONTA"].isin(contas_necessarias())
    base = df.loc[contas, ["ano_num", "CONTA", "VALOR"]].copy() if is_all_scenarios(cena) else df.loc[(df["CENA"] == cena) & contas, ["ano_num", "CONTA", "VALOR"]].copy()
    if base.empty:
        return pd.DataFrame(columns=["ano_num", "Valor"])
    base["ano_num"] = pd.to_numeric(base["ano_num"], errors="coerce")
    base["VALOR"] = _to_number(base["VALOR"])
    agrupado = base.groupby(["ano_num", "CONTA"], as_index=False)["VALOR"]
    agregado = agrupado.mean() if is_all_scenarios(cena) else agrupado.sum()
    wide = (
        agregado.pivot(index="ano_num", columns="CONTA", values="VALOR")
        .reset_index()
        .sort_values("ano_num")
    )
    wide.columns.name = None
    for conta in contas_necessarias():
        if conta not in wide.columns:
            wide[conta] = 0.0
    wide = _normalizar_aliases(wide)
    wide["Valor"] = pd.to_numeric(metric["formula"](wide), errors="coerce")
    return wide[["ano_num", "Valor"]]


def format_metric_value(metric_name: str, value: float) -> str:
    if pd.isna(value):
        return "—"
    return FINANCIAL_METRICS_DICT[metric_name]["format"].format(float(value))
