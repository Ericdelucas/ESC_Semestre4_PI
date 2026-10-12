"""Orquestracao da auditoria CTI."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from .config import (
    BUSINESS_KEY,
    CHUNKSIZE,
    DEFAULT_CONCESSION_YEAR_MAX,
    DEFAULT_CONCESSION_YEAR_MIN,
    DEFAULT_CSV_PATH,
    EXPECTED_COLUMNS,
)
from .control_totals import account_quality, control_totals, update_accounts
from .duplicate_check import summarize_duplicates, update_duplicates
from .models import AuditAccumulator
from .report_exporter import save_audit_report
from .structural_check import (
    imputation_rules,
    prepare_cti_chunk,
    read_csv_chunks,
    read_sql_chunks,
    summarize_columns,
    update_anomalies,
    update_profiles,
)


def _chunk_source(source: str | Path | None, db_url: str | None, table: str | None, chunksize: int):
    if db_url:
        if not table:
            raise ValueError("Informe --table ao usar --db-url.")
        return read_sql_chunks(db_url, table, chunksize), table, "sql"
    csv_path = Path(source) if source else DEFAULT_CSV_PATH
    if not csv_path.is_absolute():
        csv_path = DEFAULT_CSV_PATH.parent / csv_path
    return read_csv_chunks(csv_path, chunksize), str(csv_path), "csv"


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
) -> dict[str, Any]:
    """Executa auditoria da base CTI e retorna relatorio estruturado."""
    started_at = datetime.now().astimezone()
    acc = AuditAccumulator()
    chunks, source_label, source_type = _chunk_source(source, db_url, table, chunksize)

    for raw_chunk in chunks:
        prepared = prepare_cti_chunk(raw_chunk)
        update_profiles(acc, prepared)
        update_duplicates(acc, prepared)
        update_accounts(acc, prepared)
        update_anomalies(acc, prepared, concession_year_min, concession_year_max, sample_limit)

    finished_at = datetime.now().astimezone()
    column_summary = summarize_columns(acc)
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
    if save_report:
        report_path = save_audit_report(report, report_format=report_format)
        report["metadata"]["report_path"] = str(report_path)
    return report
