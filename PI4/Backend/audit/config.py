"""Constantes compartilhadas da auditoria CTI."""

from __future__ import annotations

from pathlib import Path

from Backend.metrics.financial_kpis import CONTAS_RECEBER, PECAS_CONTAS


BACKEND_DIR = Path(__file__).resolve().parents[1]
DEFAULT_CSV_PATH = BACKEND_DIR / "Cti.csv"
REPORT_DIR = BACKEND_DIR / "audit_reports"
EXPECTED_COLUMNS = ["ANO", "CENA", "CONTA", "VALOR"]
BUSINESS_KEY = ["ANO", "CENA", "CONTA"]
DEFAULT_CONCESSION_YEAR_MIN = 1
DEFAULT_CONCESSION_YEAR_MAX = 12
CHUNKSIZE = 120_000

CRITICAL_VALUE_ACCOUNTS = sorted(
    set(CONTAS_RECEBER)
    | {
        conta
        for chave in [
            "disponivel",
            "ativo_circ",
            "passivo_circ",
            "total_ativo",
            "total_passivo",
            "dre_receita",
            "dre_custos",
            "resultado",
            "ebitda",
            "geracao_caixa",
            "investimentos",
            "distribuicao",
            "saldo_final",
        ]
        for conta in PECAS_CONTAS.get(chave, [])
    }
)

EXPECTED_NON_NEGATIVE_ACCOUNTS = sorted(
    set(CONTAS_RECEBER)
    | {
        conta
        for chave in ["disponivel", "ativo_circ", "passivo_circ", "total_ativo", "total_passivo", "dre_receita"]
        for conta in PECAS_CONTAS.get(chave, [])
    }
)

CONTROL_ACCOUNT_GROUPS = {
    "contas_receber": list(CONTAS_RECEBER),
    **{nome: contas for nome, contas in PECAS_CONTAS.items()},
}

