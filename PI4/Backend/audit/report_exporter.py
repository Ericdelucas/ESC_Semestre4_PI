"""Formatacao e exportacao dos relatorios de auditoria."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from .config import REPORT_DIR


def _json_default(value):
    """Converte escalares pandas/numpy para JSON nativo."""
    if hasattr(value, "item"):
        return value.item()
    return str(value)


def format_money(value: float | None) -> str:
    """Formata numero no padrao brasileiro."""
    if value is None:
        return "n/d"
    return f"{value:,.2f}".replace(",", "_").replace(".", ",").replace("_", ".")


def format_console_report(report: dict[str, Any]) -> str:
    """Formata relatorio para terminal."""
    meta = report["metadata"]
    structure = report["structure"]
    dup = report["duplicates"]
    columns = report["columns"]
    missing = report["missing_values"]
    anomalies = report["anomalies"]
    controls = report["control_totals"]

    lines = [
        "",
        "========== AUDITORIA CTI ==========",
        f"Fonte: {meta['source']}",
        f"Executada em: {meta['started_at']} | duracao: {meta['duration_seconds']}s",
        f"Memoria estimada por chunk: {meta['peak_chunk_memory_mb']} MB",
        "",
        "[1] Estrutura e volume",
        f"- Linhas: {structure['rows']:,}",
        f"- Colunas esperadas: {structure['columns']} ({', '.join(structure['expected_columns'])})",
        f"- Cenarios: {structure['scenarios']:,}",
        f"- Anos detectados: {structure['years']}",
        "",
        "[2] Tipagem e parsing",
    ]
    for col, info in columns.items():
        minmax = ""
        if col in {"VALOR", "ano_num"}:
            minmax = f" | min={info['min']} max={info['max']} falhas_parse={info['parse_failures']}"
        lines.append(f"- {col}: tipos={info['dtype_samples']} | nulls={info['nulls']} ({info['null_pct']}%){minmax}")

    lines.extend(
        [
            "",
            "[3] Duplicidades",
            f"- Linhas 100% duplicadas: grupos={dup['full_rows']['duplicated_groups']:,}, excedentes={dup['full_rows']['extra_rows']:,}",
            f"- Chave de negocio {structure['business_key']}: grupos={dup['business_key']['duplicated_groups']:,}, excedentes={dup['business_key']['extra_rows']:,}",
            "",
            "[4] Ausentes, sujeiras e anomalias",
        ]
    )
    for col, info in missing["by_column"].items():
        lines.append(f"- {col}: nulls={info['nulls']:,} ({info['null_pct']}%), vazios={info['empty_strings']:,}")
    lines.extend(
        [
            f"- Exemplos criticos ausentes: {len(missing['critical_examples'])}",
            f"- Exemplos negativos inesperados: {len(anomalies['negative_where_unexpected_examples'])}",
            f"- Exemplos fora do periodo: {len(anomalies['out_of_period_examples'])}",
            f"- Exemplos de falha no parsing monetario: {len(anomalies['value_parse_error_examples'])}",
            "",
            "[5] Totais de controle",
        ]
    )
    for name, info in controls.items():
        lines.append(
            f"- {name}: soma={format_money(info['sum'])} | soma_abs={format_money(info['abs_sum'])} | media={format_money(info['mean'])} | n={info['non_null_values']:,}"
        )
    if meta.get("report_path"):
        lines.extend(["", f"Relatorio salvo em: {meta['report_path']}"])
    lines.append("===================================")
    return "\n".join(lines)


def save_audit_report(report: dict[str, Any], *, report_format: str = "json") -> Path:
    """Salva relatorio JSON ou Markdown dentro do backend."""
    REPORT_DIR.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    fmt = report_format.lower().strip()
    if fmt not in {"json", "markdown", "md"}:
        raise ValueError("report_format deve ser 'json' ou 'markdown'.")
    if fmt == "json":
        path = REPORT_DIR / f"auditoria_cti_{stamp}.json"
        path.write_text(json.dumps(report, ensure_ascii=False, indent=2, default=_json_default), encoding="utf-8")
        return path
    path = REPORT_DIR / f"auditoria_cti_{stamp}.md"
    path.write_text(format_markdown_report(report), encoding="utf-8")
    return path


def format_markdown_report(report: dict[str, Any]) -> str:
    """Gera relatorio Markdown resumido."""
    lines = [
        "# Auditoria CTI",
        "",
        f"- Fonte: `{report['metadata']['source']}`",
        f"- Executada em: `{report['metadata']['started_at']}`",
        f"- Linhas: `{report['structure']['rows']:,}`",
        f"- Cenarios: `{report['structure']['scenarios']:,}`",
        f"- Anos: `{report['structure']['years']}`",
        "",
        "## Totais de controle",
        "",
        "| Grupo | Soma | Soma absoluta | Media | N |",
        "|---|---:|---:|---:|---:|",
    ]
    for name, info in report["control_totals"].items():
        lines.append(
            f"| {name} | {format_money(info['sum'])} | {format_money(info['abs_sum'])} | {format_money(info['mean'])} | {info['non_null_values']:,} |"
        )
    lines.extend(
        [
            "",
            "## Duplicidades",
            "",
            f"- Linhas 100% duplicadas: `{report['duplicates']['full_rows']['extra_rows']:,}` excedentes.",
            f"- Chave de negocio: `{report['duplicates']['business_key']['extra_rows']:,}` excedentes.",
            "",
            "## Regras de tratamento",
            "",
        ]
    )
    for field_name, rule in report["missing_values"]["imputation_rules"].items():
        lines.append(f"- **{field_name}:** {rule}")
    return "\n".join(lines) + "\n"

