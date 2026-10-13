"""Metricas de contexto e reconstrucao das contas financeiras do dashboard.

As formulas de KPIs, EBITDA e margens permanecem em Backend.metrics.
"""
from __future__ import annotations

import pandas as pd

from Backend.data_loader import otimizar_base_cti
from Backend.diag import diag
from Backend.metrics import calcular_kpis_recorte, montar_indicadores, probabilidade_caixa_negativo
from Backend.metrics.financial_kpis import is_all_scenarios, mapa_contas
from Backend.services.scenario_filter import filtrar_cenario_ano, media_por_ano


def df_longo_de_indicadores(ind: pd.DataFrame) -> pd.DataFrame:
    """Reconstroi CONTA/VALOR a partir dos indicadores — sem o CSV de 1M linhas."""
    if ind is None or ind.empty:
        diag("cache", "df_longo: indicadores vazios")
        return pd.DataFrame(columns=["ANO", "CENA", "CONTA", "VALOR", "ano_num"])
    inverso: dict[str, str] = {}
    for conta, campo in mapa_contas().items():
        inverso.setdefault(campo, conta)
    eixos = [col for col in ("ANO", "ano_num", "CENA") if col in ind.columns]
    partes: list[pd.DataFrame] = []
    for campo, conta in inverso.items():
        if campo not in ind.columns:
            continue
        bloco = ind[eixos].copy()
        bloco["CONTA"] = conta
        bloco["VALOR"] = pd.to_numeric(ind[campo], errors="coerce").fillna(0.0)
        partes.append(bloco)
    if not partes:
        diag("cache", "df_longo: nenhum campo mapeado")
        return pd.DataFrame(columns=["ANO", "CENA", "CONTA", "VALOR", "ano_num"])
    out = otimizar_base_cti(pd.concat(partes, ignore_index=True))
    diag("cache", f"df_longo reconstruido shape={out.shape} contas={out['CONTA'].nunique()} cenas={out['CENA'].nunique()}")
    return out


def calcular_indicadores(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Reutiliza o calculo financeiro existente e devolve indicadores e ranking."""
    return montar_indicadores(df)


def build_context_metrics(
    ind: pd.DataFrame,
    ranking: pd.DataFrame,
    *,
    cena_sel: str,
    ano_sel: str | int,
) -> tuple[int, float, pd.DataFrame, pd.DataFrame, pd.Series]:
    """Calcula dados derivados de contexto para filtros ativos."""
    ano_enc = int(ranking["ano_encerramento"].iloc[0]) if len(ranking) and "ano_encerramento" in ranking.columns else 12
    p_ruina = probabilidade_caixa_negativo(ranking)
    foco_raw, foco_ano_raw = filtrar_cenario_ano(ind, cena_sel=cena_sel, ano_sel=ano_sel)
    kpis = calcular_kpis_recorte(foco_raw, foco_ano_raw)
    if is_all_scenarios(cena_sel):
        return ano_enc, p_ruina, media_por_ano(foco_raw), media_por_ano(foco_ano_raw), kpis
    return ano_enc, p_ruina, foco_raw, foco_ano_raw, kpis

