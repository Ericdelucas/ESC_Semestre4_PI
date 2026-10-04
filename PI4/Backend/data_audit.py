"""Entrada CLI/importavel para auditoria da base CTI."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PI4_ROOT = Path(__file__).resolve().parents[1]
if str(PI4_ROOT) not in sys.path:
    sys.path.insert(0, str(PI4_ROOT))

from Backend.audit import run_audit
from Backend.audit.config import (
    CHUNKSIZE,
    DEFAULT_CONCESSION_YEAR_MAX,
    DEFAULT_CONCESSION_YEAR_MIN,
    DEFAULT_CSV_PATH,
)
from Backend.audit.report_exporter import format_console_report


def build_parser() -> argparse.ArgumentParser:
    """Cria argumentos da auditoria CLI."""
    parser = argparse.ArgumentParser(description="Audita integridade e reconciliacao da base CTI.")
    parser.add_argument("--source", default=str(DEFAULT_CSV_PATH), help="Caminho do CSV dentro do Backend.")
    parser.add_argument("--db-url", default=None, help="URL SQLAlchemy para PostgreSQL/Supabase.")
    parser.add_argument("--table", default=None, help="Tabela SQL quando --db-url for usado.")
    parser.add_argument("--chunksize", type=int, default=CHUNKSIZE, help="Linhas por chunk.")
    parser.add_argument("--no-save", action="store_true", help="Nao salva relatorio estruturado.")
    parser.add_argument(
        "--report-format",
        choices=["json", "markdown", "md"],
        default="json",
        help="Formato do relatorio salvo.",
    )
    parser.add_argument("--year-min", type=int, default=DEFAULT_CONCESSION_YEAR_MIN)
    parser.add_argument("--year-max", type=int, default=DEFAULT_CONCESSION_YEAR_MAX)
    return parser


def main(argv: list[str] | None = None) -> int:
    """Executa auditoria e imprime resumo no console."""
    args = build_parser().parse_args(argv)
    try:
        report = run_audit(
            source=args.source,
            db_url=args.db_url,
            table=args.table,
            chunksize=args.chunksize,
            save_report=not args.no_save,
            report_format=args.report_format,
            concession_year_min=args.year_min,
            concession_year_max=args.year_max,
        )
    except Exception as exc:
        print(f"[ERRO] Auditoria interrompida: {exc}", file=sys.stderr)
        return 1

    print(format_console_report(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
