"""Rótulos traduzidos das métricas financeiras do sandbox."""

from __future__ import annotations

from src.config.i18n import t

METRIC_I18N_KEYS: dict[str, str] = {
    "Rentabilidade · ROE (Return on Equity)": "fin.roe",
    "Rentabilidade · ROA (Return on Assets)": "fin.roa",
    "Rentabilidade · ROIC": "fin.roic",
    "Rentabilidade · Margem Bruta": "fin.mg",
    "Rentabilidade · Margem EBITDA": "fin.mebitda",
    "Rentabilidade · Margem Líquida": "fin.mnet",
    "Liquidez · Liquidez Corrente": "fin.lc",
    "Liquidez · Liquidez Seca": "fin.ls",
    "Liquidez · Liquidez Imediata": "fin.li",
    "Liquidez · Liquidez Geral": "fin.lg",
    "Estrutura de Capital · Endividamento Geral": "fin.debt",
    "Estrutura de Capital · Dívida Líquida": "fin.netdebt",
    "Eficiência Operacional · PMP (Prazo Médio de Pagamento)": "fin.pmp",
    "Eficiência Operacional · PMR (Prazo Médio de Recebimento)": "fin.pmr",
    "Eficiência Operacional · PME (Prazo Médio de Estoques)": "fin.pme",
    "Eficiência Operacional · Ciclo Operacional": "fin.opcycle",
    "Eficiência Operacional · Ciclo Financeiro": "fin.fincycle",
    "Eficiência Operacional · NCG (Necessidade de Capital de Giro)": "fin.ncg",
    "Fluxo de Caixa · FCFF (Geração de Caixa Livre da Empresa)": "fin.fcff",
    "Fluxo de Caixa · FCFE (Fluxo de Caixa do Acionista)": "fin.fcfe",
    "Fluxo de Caixa · Cobertura de Juros": "fin.interest",
}


def metric_label(key: str) -> str:
    i18n_key = METRIC_I18N_KEYS.get(key)
    return t(i18n_key) if i18n_key else key


def metric_short_name(key: str, fallback: str = "") -> str:
    i18n_key = METRIC_I18N_KEYS.get(key)
    return t(f"{i18n_key}.name") if i18n_key else fallback or key
