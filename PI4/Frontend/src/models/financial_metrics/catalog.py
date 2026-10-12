"""Catalogo de metricas financeiras disponiveis no sandbox."""

from __future__ import annotations

from .types import FinancialMetric
from .utils import _safe_div


FINANCIAL_METRICS_DICT: dict[str, FinancialMetric] = {
    "Rentabilidade · ROE (Return on Equity)": {
        "categoria": "Rentabilidade & Retorno",
        "nome": "ROE (Return on Equity)",
        "formula": lambda df: _safe_div(df["DRE - Resultado Líquido"], df["BAL - Patrimônio Líquido"]) * 100,
        "format": "{:.2f}%",
    },
    "Rentabilidade · ROA (Return on Assets)": {
        "categoria": "Rentabilidade & Retorno",
        "nome": "ROA (Return on Assets)",
        "formula": lambda df: _safe_div(df["DRE - Resultado Líquido"], df["BAL - Total do Ativo"]) * 100,
        "format": "{:.2f}%",
    },
    "Rentabilidade · ROIC": {
        "categoria": "Rentabilidade & Retorno",
        "nome": "ROIC (Return on Invested Capital)",
        "formula": lambda df: _safe_div(
            df["DRE - Resultado Operacional"] * (1 - 0.34),
            df["BAL - Patrimônio Líquido"].abs() + df["BAL - Empréstimos"].abs(),
        )
        * 100,
        "format": "{:.2f}%",
    },
    "Rentabilidade · Margem Bruta": {
        "categoria": "Rentabilidade & Retorno",
        "nome": "Margem Bruta",
        "formula": lambda df: _safe_div(df["DRE - Receita"] - df["DRE - Custos"].abs(), df["DRE - Receita"]) * 100,
        "format": "{:.2f}%",
    },
    "Rentabilidade · Margem EBITDA": {
        "categoria": "Rentabilidade & Retorno",
        "nome": "Margem EBITDA",
        "formula": lambda df: _safe_div(df["DRE - EBITDA"], df["DRE - Receita"]) * 100,
        "format": "{:.2f}%",
    },
    "Rentabilidade · Margem Líquida": {
        "categoria": "Rentabilidade & Retorno",
        "nome": "Margem Líquida",
        "formula": lambda df: _safe_div(df["DRE - Resultado Líquido"], df["DRE - Receita"]) * 100,
        "format": "{:.2f}%",
    },
    "Liquidez · Liquidez Corrente": {
        "categoria": "Liquidez & Solvência",
        "nome": "Liquidez Corrente",
        "formula": lambda df: _safe_div(df["BAL - Ativo Circulante"], df["BAL - Passivo Circulante"]),
        "format": "{:.2f}x",
    },
    "Liquidez · Liquidez Seca": {
        "categoria": "Liquidez & Solvência",
        "nome": "Liquidez Seca",
        "formula": lambda df: _safe_div(df["BAL - Ativo Circulante"] - df["BAL - Estoques Diversos"], df["BAL - Passivo Circulante"]),
        "format": "{:.2f}x",
    },
    "Liquidez · Liquidez Imediata": {
        "categoria": "Liquidez & Solvência",
        "nome": "Liquidez Imediata",
        "formula": lambda df: _safe_div(df["BAL - Disponível"], df["BAL - Passivo Circulante"]),
        "format": "{:.2f}x",
    },
    "Liquidez · Liquidez Geral": {
        "categoria": "Liquidez & Solvência",
        "nome": "Liquidez Geral",
        "formula": lambda df: _safe_div(
            df["BAL - Ativo Circulante"] + df["BAL - Realizável a Longo Prazo"],
            df["BAL - Passivo Circulante"] + df["BAL - Exigível a Longo Prazo"],
        ),
        "format": "{:.2f}x",
    },
    "Estrutura de Capital · Endividamento Geral": {
        "categoria": "Estrutura de Capital",
        "nome": "Endividamento Geral",
        "formula": lambda df: _safe_div(
            df["BAL - Passivo Circulante"] + df["BAL - Exigível a Longo Prazo"],
            df["BAL - Total do Ativo"],
        )
        * 100,
        "format": "{:.2f}%",
    },
    "Estrutura de Capital · Dívida Líquida": {
        "categoria": "Estrutura de Capital",
        "nome": "Dívida Líquida",
        "formula": lambda df: df["BAL - Empréstimos"] - df["BAL - Disponível"],
        "format": "R$ {:,.2f}",
    },
    "Eficiência Operacional · PMP (Prazo Médio de Pagamento)": {
        "categoria": "Eficiência Operacional",
        "nome": "PMP (Prazo Médio de Pagamento)",
        "formula": lambda df: _safe_div(df["BAL - Fornecedores"], df["DRE - Custos"].abs()) * 365,
        "format": "{:.1f} dias",
    },
    "Eficiência Operacional · PMR (Prazo Médio de Recebimento)": {
        "categoria": "Eficiência Operacional",
        "nome": "PMR (Prazo Médio de Recebimento)",
        "formula": lambda df: _safe_div(df["BAL - Contas a Receber - Clientes"], df["DRE - Receita"]) * 365,
        "format": "{:.1f} dias",
    },
    "Eficiência Operacional · PME (Prazo Médio de Estoques)": {
        "categoria": "Eficiência Operacional",
        "nome": "PME (Prazo Médio de Estoques)",
        "formula": lambda df: _safe_div(df["BAL - Estoques Diversos"], df["DRE - Custos"].abs()) * 365,
        "format": "{:.1f} dias",
    },
    "Eficiência Operacional · Ciclo Operacional": {
        "categoria": "Eficiência Operacional",
        "nome": "Ciclo Operacional",
        "formula": lambda df: (_safe_div(df["BAL - Estoques Diversos"], df["DRE - Custos"].abs()) * 365)
        + (_safe_div(df["BAL - Contas a Receber - Clientes"], df["DRE - Receita"]) * 365),
        "format": "{:.1f} dias",
    },
    "Eficiência Operacional · Ciclo Financeiro": {
        "categoria": "Eficiência Operacional",
        "nome": "Ciclo Financeiro (Caixa)",
        "formula": lambda df: (
            (_safe_div(df["BAL - Estoques Diversos"], df["DRE - Custos"].abs()) * 365)
            + (_safe_div(df["BAL - Contas a Receber - Clientes"], df["DRE - Receita"]) * 365)
        )
        - (_safe_div(df["BAL - Fornecedores"], df["DRE - Custos"].abs()) * 365),
        "format": "{:.1f} dias",
    },
    "Eficiência Operacional · NCG (Necessidade de Capital de Giro)": {
        "categoria": "Eficiência Operacional",
        "nome": "Necessidade de Capital de Giro (NCG)",
        "formula": lambda df: (df["BAL - Contas a Receber - Clientes"] + df["BAL - Estoques Diversos"]) - df["BAL - Fornecedores"],
        "format": "R$ {:,.2f}",
    },
    "Fluxo de Caixa · FCFF (Geração de Caixa Livre da Empresa)": {
        "categoria": "Fluxo de Caixa",
        "nome": "FCFF (Free Cash Flow to Firm)",
        "formula": lambda df: df["FLU - Geração de Caixa"] - df["FLU - Investimentos"],
        "format": "R$ {:,.2f}",
    },
    "Fluxo de Caixa · FCFE (Fluxo de Caixa do Acionista)": {
        "categoria": "Fluxo de Caixa",
        "nome": "FCFE (Free Cash Flow to Equity)",
        "formula": lambda df: (df["FLU - Geração de Caixa"] - df["FLU - Investimentos"]) - df["FLU - Despesas Financeiras"].abs(),
        "format": "R$ {:,.2f}",
    },
    "Fluxo de Caixa · Cobertura de Juros": {
        "categoria": "Fluxo de Caixa",
        "nome": "Cobertura de Juros",
        "formula": lambda df: _safe_div(df["DRE - EBITDA"], df["DRE - Despesas Financeiras"].abs()),
        "format": "{:.2f}x",
    },
}
