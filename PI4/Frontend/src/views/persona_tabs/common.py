"""Calculos compartilhados pelas sub-abas de persona."""

from __future__ import annotations

import pandas as pd

WACC = 0.10
PAYOUT = 0.35
ALIQUOTA_IR_FALLBACK = 0.34


def _safe_div(num: float | pd.Series, den: float | pd.Series) -> float | pd.Series:
    if isinstance(num, pd.Series) or isinstance(den, pd.Series):
        index = num.index if isinstance(num, pd.Series) else den.index
        numerador = pd.to_numeric(num, errors="coerce")
        denominador = pd.to_numeric(den, errors="coerce")
        if not isinstance(numerador, pd.Series):
            numerador = pd.Series(numerador, index=index)
        if not isinstance(denominador, pd.Series):
            denominador = pd.Series(denominador, index=index)
        denominador = denominador.replace(0, pd.NA)
        return numerador / denominador
    return float("nan") if pd.isna(den) or float(den) == 0 else num / den


def _wide(df: pd.DataFrame, cena: str, contas: list[str]) -> pd.DataFrame:
    base = df.loc[(df["CENA"] == cena) & (df["CONTA"].isin(contas)), ["ano_num", "CONTA", "VALOR"]].copy()
    if base.empty:
        return pd.DataFrame(columns=["ano_num", *contas])
    base["ano_num"] = pd.to_numeric(base["ano_num"], errors="coerce")
    base["VALOR"] = pd.to_numeric(base["VALOR"], errors="coerce")
    out = (
        base.groupby(["ano_num", "CONTA"], as_index=False)["VALOR"]
        .sum()
        .pivot(index="ano_num", columns="CONTA", values="VALOR")
        .reset_index()
        .sort_values("ano_num")
    )
    out.columns.name = None
    for conta in contas:
        if conta not in out.columns:
            out[conta] = 0.0
    out["ano_num"] = out["ano_num"].astype(int)
    return out


def _conta(dados: pd.DataFrame, nome: str) -> pd.Series:
    return pd.to_numeric(dados.get(nome, 0.0), errors="coerce").fillna(0.0)


def _dre(df: pd.DataFrame, cena: str) -> pd.DataFrame:
    contas = [
        "DRE - Receita",
        "DRE - Tributos",
        "DRE - Custos",
        "DRE - Depreciação e Amortização",
        "DRE - Resultado Operacional",
        "DRE - Resultado Financeiro",
        "DRE - Despesas Financeiras",
        "DRE - Outros Resultados Operacionais",
        "DRE - Resultado Antes do Imposto de Renda",
        "DRE - Imposto de Renda e Contribuição Social",
        "DRE - Resultado Líquido",
        "DRE - EBITDA",
    ]
    dados = _wide(df, cena, contas)
    if dados.empty:
        return dados
    receita = _conta(dados, "DRE - Receita")
    tributos = _conta(dados, "DRE - Tributos")
    custos = _conta(dados, "DRE - Custos")
    dep = _conta(dados, "DRE - Depreciação e Amortização")
    ebitda = _conta(dados, "DRE - EBITDA")
    ebit = _conta(dados, "DRE - Resultado Operacional")
    fin = _conta(dados, "DRE - Resultado Financeiro")
    ebt = _conta(dados, "DRE - Resultado Antes do Imposto de Renda")
    lucro = _conta(dados, "DRE - Resultado Líquido")
    outros = _conta(dados, "DRE - Outros Resultados Operacionais")
    despesas_fin = _conta(dados, "DRE - Despesas Financeiras")

    dados["Receita Líquida"] = receita + tributos
    dados["Margem Bruta"] = dados["Receita Líquida"] + custos
    dados["OPEX"] = ebitda - dados["Margem Bruta"]
    dados["EBITDA"] = ebitda
    dados["EBIT"] = ebit
    dados["Resultado Financeiro"] = fin
    dados["EBT"] = ebt
    dados["Lucro Líquido"] = lucro
    dados["Custos"] = custos
    dados["Depreciação"] = dep
    dados["Outros Operacionais"] = outros
    dados["Despesas Financeiras"] = despesas_fin
    return dados


def _balanco_fluxo(df: pd.DataFrame, cena: str) -> pd.DataFrame:
    contas = [
        "BAL - Total do Ativo",
        "BAL - Total do Passivo",
        "BAL - Ativo Circulante",
        "BAL - Passivo Circulante",
        "BAL - Realizável a Longo Prazo",
        "BAL - Exigível a Longo Prazo",
        "BAL  - Patrimônio Líquido",
        "BAL - Empréstimos",
        "BAL - Disponível",
        "BAL - Investimentos - Imobilizado",
        "BAL - Investimentos - Intangível",
        "BAL - Depreciação Acumulada",
        "BAL - Amortização Acumulada",
        "FLU - Investimentos",
        "FLU - Distribuição para Acionista",
    ]
    return _wide(df, cena, contas)


def _financeiro(df: pd.DataFrame, cena: str) -> pd.DataFrame:
    dre = _dre(df, cena)
    bal = _balanco_fluxo(df, cena)
    dados = dre.merge(bal, on="ano_num", how="outer").sort_values("ano_num").fillna(0.0)
    patrimonio = _conta(dados, "BAL  - Patrimônio Líquido").abs()
    divida = _conta(dados, "BAL - Empréstimos").abs()
    caixa = _conta(dados, "BAL - Disponível").abs()
    divida_liquida = (divida - caixa).clip(lower=0)
    capital = (patrimonio + divida_liquida).replace(0, pd.NA)
    ir_cs = _conta(dados, "DRE - Imposto de Renda e Contribuição Social")
    aliquota_ir = (_safe_div(ir_cs.abs(), dados["EBIT"].abs())).clip(lower=0, upper=ALIQUOTA_IR_FALLBACK).fillna(ALIQUOTA_IR_FALLBACK)
    nopat = dados["EBIT"] * (1 - aliquota_ir)
    lucro = dados["Lucro Líquido"]
    dados["Dívida Líquida"] = divida_liquida
    dados["Capital Investido"] = capital
    dados["NOPAT"] = nopat
    dados["ROIC"] = nopat / capital
    dados["ROE"] = lucro / patrimonio.replace(0, pd.NA)
    dados["WACC"] = WACC
    dados["Custo do Capital"] = capital * WACC
    dados["EVA"] = nopat - dados["Custo do Capital"]
    dados["Dividendos"] = (lucro.clip(lower=0) * PAYOUT).fillna(0)
    dados["Retido"] = (lucro.clip(lower=0) - dados["Dividendos"]).fillna(0)
    dados["DY"] = dados["Dividendos"] / capital
    return dados


def _break_even_df(df: pd.DataFrame, cena: str) -> pd.DataFrame:
    dados = _dre(df, cena)
    if dados.empty:
        return dados
    receita = dados["Receita Líquida"].replace(0, pd.NA)
    custos_variaveis = dados["Custos"].abs()
    custos_fixos = dados["Outros Operacionais"].abs() + dados["Depreciação"].abs() + dados["Despesas Financeiras"].abs()
    mc = (dados["Receita Líquida"] - custos_variaveis) / receita
    dados["Custos Fixos"] = custos_fixos
    dados["Margem de Contribuição (%)"] = mc
    dados["Break-Even"] = custos_fixos / mc.replace(0, pd.NA)
    dados["Margem de Segurança (%)"] = (dados["Receita Líquida"] - dados["Break-Even"]) / receita
    return dados
