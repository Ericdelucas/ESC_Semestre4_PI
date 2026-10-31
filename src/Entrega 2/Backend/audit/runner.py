# esse arquivo serve para orquestrar a auditoria do arquivo Cti.csv, lendo os dados em chunks, atualizando os acumuladores de contadores e perfis, e gerando um relatorio estruturado com as informacoes coletadas
"""Orquestracao da auditoria CTI."""

# ele importa a anotacao de futuras funcionalidades do Python
from __future__ import annotations

# o detetime e usado para medir o tempo de execucao da auditoria, e o Path e usado para manipular caminhos de arquivos
from datetime import datetime
# o pathlib e usado para manipular caminhos de arquivos, e o typing e usado para indicar que um valor pode ser de qualquer tipo
from pathlib import Path
# o typing e usado para indicar que um valor pode ser de qualquer tipo
from typing import Any

# o config e usado para importar as constantes de configuracao da auditoria, como o caminho do arquivo cti.csv, o tamanho do chunk, o intervalo de anos de concessao, e as colunas esperadas
from .config import (
    BUSINESS_KEY,
    CHUNKSIZE,
    DEFAULT_CONCESSION_YEAR_MAX,
    DEFAULT_CONCESSION_YEAR_MIN,
    DEFAULT_CSV_PATH,
    EXPECTED_COLUMNS,
)
# esse .control_totals importa as funcoes de calculo de totais de controle e qualidade por conta, e a funcao de atualizacao de contas a partir de um chunk de dados
from .control_totals import account_quality, control_totals, update_accounts
# esse .duplicate_check importa as funcoes de atualizacao de contadores de duplicidade e resumo de duplicidades a partir de um chunk de dados
from .duplicate_check import summarize_duplicates, update_duplicates
# esse .models importa a classe AuditAccumulator, que representa o estado incremental da auditoria em chunks, e armazena contadores de linhas, colunas, memoria, perfis de colunas, contadores de duplicidade, contadores de contas, conjuntos de cenarios e anos vistos, e exemplos de erros
from .models import AuditAccumulator
# esse .report_exporter importa a funcao de salvamento do relatorio de auditoria em arquivo, e a funcao de formatacao do relatorio em Markdown
from .report_exporter import save_audit_report
# esse .structural_check importa as funcoes de leitura de chunks de dados do arquivo cti.csv ou do banco de dados, de preparacao do chunk para auditoria, de atualizacao de perfis e anomalias, e de resumo das colunas
from .structural_check import (
    # essas funcoes sao usadas para ler os dados do arquivo cti.csv ou do banco de dados em chunks, preparar o chunk para auditoria, atualizar os perfis e anomalias, e resumir as colunas
    imputation_rules,
    prepare_cti_chunk,
    read_csv_chunks,
    read_sql_chunks,
    summarize_columns,
    update_anomalies,
    update_profiles,
)


# essa funcao _chunk_source retorna um gerador de chunks de dados do arquivo cti.csv ou do banco de dados, dependendo dos parametros passados, e tambem retorna o label da fonte e o tipo da fonte
def _chunk_source(source: str | Path | None, db_url: str | None, table: str | None, chunksize: int):
    # ele verifica se o parametro db_url foi passado, e se sim, ele verifica se o parametro table foi passado, e se nao for, ele levanta um ValueError, pois e necessario informar a tabela do banco de dados para ler os dados
    if db_url:
        if not table:
            raise ValueError("Informe --table ao usar --db-url.")
        return read_sql_chunks(db_url, table, chunksize), table, "sql"
    csv_path = Path(source) if source else DEFAULT_CSV_PATH
    if not csv_path.is_absolute():
        csv_path = DEFAULT_CSV_PATH.parent / csv_path
        # ele retorna o gerador de chunks de dados do arquivo cti.csv, o label da fonte como o caminho absoluto do arquivo, e o tipo da fonte como "csv"
    return read_csv_chunks(csv_path, chunksize), str(csv_path), "csv"

# essa funcao run_audit executa a auditoria da base cti, lendo os dados em chunks, atualizando os acumuladores de contadores e perfis, e gerando um relatorio estruturado com as informacoes coletadas
def run_audit(
    source: str | Path | None = None,
    *,
    db_url: str | None = None,
    table: str | None = None,
    chunksize: int = CHUNKSIZE,
    save_report: bool = True,
    report_format: str = "json",
    concession_year_min: int = DEFAULT_CONCESSION_YEAR_MIN,
    concession_year_max: int = DEFAULT_CONCESSION_YEAR_MAX,
    sample_limit: int = 10,
    # esse dict[str, Any] e usado para indicar que o relatorio retornado e um dicionario com chaves do tipo string e valores de qualquer tipo
) -> dict[str, Any]:
    """Executa auditoria da base CTI e retorna relatorio estruturado."""
    started_at = datetime.now().astimezone()
    acc = AuditAccumulator()
    chunks, source_label, source_type = _chunk_source(source, db_url, table, chunksize)
    # o for faz um loop sobre cada chunk de dados lido do arquivo cti.csv ou do banco de dados, e para cada chunk ele prepara os dados para auditoria, atualiza os perfis de colunas, os contadores de duplicidade, os totais e contagens por conta, e as anomalias detectadas
    for raw_chunk in chunks:
        prepared = prepare_cti_chunk(raw_chunk)
        update_profiles(acc, prepared)
        update_duplicates(acc, prepared)
        update_accounts(acc, prepared)
        update_anomalies(acc, prepared, concession_year_min, concession_year_max, sample_limit)

    # ele calcula a data e hora de termino da auditoria, resume os perfis de colunas, e monta o relatorio estruturado com as informacoes coletadas, como metadados, estrutura, perfis de colunas, duplicidades, valores ausentes, anomalias, totais de controle e qualidade por conta
    finished_at = datetime.now().astimezone()
    column_summary = summarize_columns(acc)
    # essa tuple report e um dicionario que armazena todas as informacoes coletadas durante a auditoria, como metadados, estrutura, perfis de colunas, duplicidades, valores ausentes, anomalias, totais de controle e qualidade por conta
    report = {
        "metadata": {
            "source": source_label,
            "source_type": source_type,
            "started_at": started_at.isoformat(timespec="seconds"),
            "finished_at": finished_at.isoformat(timespec="seconds"),
            "duration_seconds": round((finished_at - started_at).total_seconds(), 3),
            "chunksize": chunksize,
            "peak_chunk_memory_mb": round(acc.memory_bytes_estimate / (1024 * 1024), 2),
        },
        # e agora ele monta a estrutura do relatorio, com o numero de linhas, colunas, colunas esperadas, chave de negocio, cenarios e anos detectados, e o intervalo de anos de concessao auditados
        "structure": {
            "rows": acc.rows,
            "columns": len(EXPECTED_COLUMNS),
            "expected_columns": EXPECTED_COLUMNS,
            "business_key": BUSINESS_KEY,
            "scenarios": len(acc.scenario_count),
            "years": sorted(acc.years_seen),
            "concession_horizon": [concession_year_min, concession_year_max],
        },

        "columns": column_summary,
        "duplicates": {
            "full_rows": summarize_duplicates(acc.full_row_counts, EXPECTED_COLUMNS, sample_limit),
            "business_key": summarize_duplicates(acc.business_key_counts, BUSINESS_KEY, sample_limit),
        },
        "missing_values": {
            "by_column": {
                col: {
                    "nulls": info["nulls"],
                    "null_pct": info["null_pct"],
                    "empty_strings": info["empty_strings"],
                }
                for col, info in column_summary.items()
            },
            "critical_examples": acc.missing_critical_examples,
            "imputation_rules": imputation_rules(),
        },
        "anomalies": {
            "negative_where_unexpected_examples": acc.negative_unexpected_examples,
            "out_of_period_examples": acc.out_of_period_examples,
            "value_parse_error_examples": acc.parse_error_examples,
        },
        "control_totals": control_totals(acc),
        "account_quality": account_quality(acc),
    }
    # e agora a condicao que verifica se o parametro save_report e True, e se for, ele chama a funcao save_audit_report para salvar o relatorio em arquivo, e adiciona o caminho do relatorio ao dicionario de metadados do relatorio
    if save_report:
        report_path = save_audit_report(report, report_format=report_format)
        report["metadata"]["report_path"] = str(report_path)
        # e retorna o relatorio estruturado com as informacoes coletadas durante a auditoria, incluindo o caminho do relatorio salvo, se aplicavel
    return report
