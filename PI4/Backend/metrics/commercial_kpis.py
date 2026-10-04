"""KPIs comerciais derivados da base financeira."""

from __future__ import annotations

import pandas as pd

from .column_resolver import series_by_alias
from .financial_kpis import build_break_even


def _scenario_rows(df: pd.DataFrame, cena: str) -> pd.DataFrame:
    if df.empty or "CENA" not in df.columns:
        return df.iloc[0:0]
    return df.loc[df["CENA"].astype(str) == str(cena)].copy()


def _assumption_series(df: pd.DataFrame, cena: str, aliases: list[str], fallback: float) -> pd.Series | float:
    """Busca premissa comercial na base longa ou retorna fallback."""
    rows = _scenario_rows(df, cena)
    if rows.empty or "CONTA" not in rows.columns:
        return fallback
    mask = rows["CONTA"].astype(str).str.strip().isin(aliases)
    found = rows.loc[mask, ["ano_num", "VALOR"]].copy()
    if found.empty:
        return fallback
    found["ano_num"] = pd.to_numeric(found["ano_num"], errors="coerce")
    found["VALOR"] = pd.to_numeric(found["VALOR"], errors="coerce")
    return found.groupby("ano_num")["VALOR"].mean()


def _align(value: pd.Series | float, index: pd.Index) -> pd.Series:
    if isinstance(value, pd.Series):
        return value.reindex(index).ffill().bfill().fillna(0)
    return pd.Series(float(value), index=index)


def calculate_ltv_cac(
    df: pd.DataFrame,
    cena: str,
    *,
    ticket_medio: float = 4_500.0,
    retencao_meses: float = 10.0,
    investimento_vendas: float = 100_000.0,
    novos_clientes: float = 1_000.0,
) -> pd.DataFrame:
    """Calcula LTV, CAC e razao LTV/CAC por ano."""
    dados = build_break_even(df, cena)
    if dados.empty:
        return dados

    indexed = dados.set_index("ano_num", drop=False)
    margin = series_by_alias(dados, ["Margem de Contribuição (%)", "Margem de Contribuicao (%)"]).fillna(0)
    ticket = _align(
        _assumption_series(df, cena, ["Ticket Médio (R$)", "Ticket Medio (R$)", "Ticket MÃ©dio (R$)"], ticket_medio),
        indexed.index,
    )
    retencao = _align(
        _assumption_series(
            df,
            cena,
            ["Tempo Médio de Retenção (Meses)", "Tempo Medio de Retencao (Meses)", "Tempo MÃ©dio de RetenÃ§Ã£o (Meses)"],
            retencao_meses,
        ),
        indexed.index,
    )
    investimento = _align(
        _assumption_series(
            df,
            cena,
            ["Investimento em Vendas e Mkt (R$)", "Investimento em Vendas e Marketing (R$)"],
            investimento_vendas,
        ),
        indexed.index,
    )
    novos = _align(
        _assumption_series(df, cena, ["Novos Clientes Adquiridos (un)", "Novos Clientes Adquiridos"], novos_clientes),
        indexed.index,
    ).replace(0, pd.NA)

    dados["CAC"] = (investimento / novos).to_numpy()
    dados["LTV"] = (ticket * margin.to_numpy() * retencao).to_numpy()
    dados["LTV/CAC"] = dados["LTV"] / pd.to_numeric(dados["CAC"], errors="coerce").replace(0, pd.NA)
    return dados


def summarize_ltv_cac(df: pd.DataFrame, cena: str, ano_sel: str | int = "Todos") -> dict[str, float]:
    """Resume LTV/CAC para cards e views com uma unica regra."""
    dados = calculate_ltv_cac(df, cena)
    if dados.empty:
        return {"ltv": 0.0, "cac": 0.0, "ratio": 0.0}
    if ano_sel != "Todos":
        dados = dados.loc[pd.to_numeric(dados["ano_num"], errors="coerce") == int(ano_sel)]
    if dados.empty:
        return {"ltv": 0.0, "cac": 0.0, "ratio": 0.0}
    ltv = float(pd.to_numeric(dados["LTV"], errors="coerce").mean())
    cac = float(pd.to_numeric(dados["CAC"], errors="coerce").mean())
    ratio = float(pd.to_numeric(dados["LTV/CAC"], errors="coerce").mean())
    return {
        "ltv": 0.0 if pd.isna(ltv) else ltv,
        "cac": 0.0 if pd.isna(cac) else cac,
        "ratio": 0.0 if pd.isna(ratio) else ratio,
    }
