"""Formatação humana de métricas financeiras."""

from __future__ import annotations

import pandas as pd


def fmt_rs(x: float) -> str:
    if pd.isna(x):
        return "—"
    sinal = "-" if x < 0 else ""
    v = abs(x)
    if v >= 1e9:
        return f"{sinal}R$ {v/1e9:,.2f} bi".replace(",", "X").replace(".", ",").replace("X", ".")
    if v >= 1e6:
        return f"{sinal}R$ {v/1e6:,.2f} mi".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{sinal}R$ {v:,.0f}".replace(",", "X").replace(".", ",").replace("X", ".")


def fmt_dias(x: float) -> str:
    if pd.isna(x):
        return "—"
    return f"{x:,.1f} dias".replace(",", "X").replace(".", ",").replace("X", ".")


def fmt_pct(x: float) -> str:
    if pd.isna(x):
        return "—"
    return f"{x*100:,.2f}%".replace(",", "X").replace(".", ",").replace("X", ".")


def texto_ncg(ncg: float) -> str:
    if pd.isna(ncg):
        return "Sem dado"
    if ncg > 0:
        return "A operação consome caixa: clientes/estoques prendem mais recurso do que fornecedores financiam."
    if ncg < 0:
        return "A operação gera caixa: fornecedores e obrigações financiam parte do giro."
    return "NCG equilibrada."


def texto_tesouraria(saldo: float) -> str:
    if pd.isna(saldo):
        return "Sem dado"
    if saldo >= 0:
        return "Caixa disponível cobre (ou supera) os empréstimos de curto prazo — menor dependência de banco no dia a dia."
    return "Empréstimos de curto prazo superam o disponível — a empresa depende de bancos para financiar a rotina."


def texto_ciclo(dias: float) -> str:
    if pd.isna(dias):
        return "Sem dado"
    if dias > 30:
        return f"Ciclo longo ({fmt_dias(dias)}): a empresa precisa financiar a operação com recurso próprio por mais tempo."
    if dias > 0:
        return f"Ciclo positivo moderado ({fmt_dias(dias)}): ainda há intervalo a financiar entre pagar e receber."
    return f"Ciclo negativo ({fmt_dias(dias)}): a empresa recebe antes de pagar — situação favorável de caixa."
