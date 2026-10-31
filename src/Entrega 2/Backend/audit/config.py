# isso serve para evitar importacoes circulares, pois o runner importa o config
"""Constantes compartilhadas da auditoria CTI."""
# isso serve para evitar importacoes circulares, pois o runner importa o config
from __future__ import annotations
# ele importa o config antes de ser importado, o que causaria erro de importacao circular
from pathlib import Path
# trazendo as contas e pecas de contas do modulo de metricas para evitar importacoes circulares
from Backend.metrics.financial_kpis import CONTAS_RECEBER, PECAS_CONTAS

# o BACKEND_DIR é o diretório pai do arquivo atual, que é o diretório "audit"
BACKEND_DIR = Path(__file__).resolve().parents[1]
# o DEFAULT_CSV_PATH é o caminho para o arquivo Cti.csv, que é o arquivo de entrada da auditoria
DEFAULT_CSV_PATH = BACKEND_DIR / "Cti.csv"
# o REPORT_DIR é o diretório onde os relatórios da auditoria serão salvos
REPORT_DIR = BACKEND_DIR / "audit_reports"
# o expected_columns é a lista de colunas esperadas no arquivo Cti.csv
EXPECTED_COLUMNS = ["ANO", "CENA", "CONTA", "VALOR"]
# o BUSINESS_KEY é a lista de colunas que formam a chave de negócio da auditoria
BUSINESS_KEY = ["ANO", "CENA", "CONTA"]
# esta constante define o intervalo de anos de concessão que serão auditados
DEFAULT_CONCESSION_YEAR_MIN = 1
# esta constante define o intervalo de anos de concessão que serão auditados
DEFAULT_CONCESSION_YEAR_MAX = 12
# CHUNKSIZE define o tamanho do lote de dados que será processado de cada vez na auditoria
CHUNKSIZE = 120_000

# ele faz a interseção das contas a receber com as contas de peças de contas, e ordena o resultado
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

# ele faz a interseção das contas a receber com as contas de peças de contas, e ordena o resultado
EXPECTED_NON_NEGATIVE_ACCOUNTS = sorted(
    set(CONTAS_RECEBER)
    | {
        conta
        for chave in ["disponivel", "ativo_circ", "passivo_circ", "total_ativo", "total_passivo", "dre_receita"]
        for conta in PECAS_CONTAS.get(chave, [])
    }
)

# ele cria um dicionário que mapeia os grupos de contas de controle para suas respectivas contas
CONTROL_ACCOUNT_GROUPS = {
    "contas_receber": list(CONTAS_RECEBER),
    **{nome: contas for nome, contas in PECAS_CONTAS.items()},
}

