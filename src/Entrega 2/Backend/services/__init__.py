"""Servicos de aplicacao do backend CTI."""

from .dashboard_pipeline import build_context_metrics, prepare_dashboard_data

__all__ = [
    "block_options",
    "build_context_metrics",
    "default_block_notes",
    "generate_custom_report_pdf",
    "generate_executive_pdf",
    "listar_documentos",
    "prepare_dashboard_data",
    "status_rag",
]


def __getattr__(name: str):
    if name == "generate_executive_pdf":
        from .report_generator import generate_executive_pdf

        return generate_executive_pdf
    if name in {"block_options", "default_block_notes", "generate_custom_report_pdf"}:
        from . import custom_report_service

        return getattr(custom_report_service, name)
    if name in {"listar_documentos", "status_rag"}:
        from . import rag_indexer

        return getattr(rag_indexer, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

