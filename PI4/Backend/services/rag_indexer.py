"""Varredura recursiva da base documental usada pelo RAG."""

from __future__ import annotations

from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
DOCS_DIR = BACKEND_DIR / "documentos"
GLOBS_RAG = ("**/*.md", "**/*.pdf")


def listar_documentos() -> list[Path]:
    """Lista .md e .pdf em Backend/documentos, incluindo subpastas."""
    if not DOCS_DIR.is_dir():
        return []
    unicos: list[Path] = []
    vistos: set[Path] = set()
    for padrao in GLOBS_RAG:
        for path in DOCS_DIR.glob(padrao):
            if not path.is_file():
                continue
            resolved = path.resolve()
            if resolved in vistos:
                continue
            vistos.add(resolved)
            unicos.append(path)
    unicos.sort(key=lambda item: str(item).lower())
    return unicos


def status_rag() -> dict[str, object]:
    arquivos = listar_documentos()
    return {
        "ok": bool(arquivos),
        "directory": str(DOCS_DIR),
        "globs": list(GLOBS_RAG),
        "count": len(arquivos),
        "sources": [str(path.relative_to(BACKEND_DIR.parent)) for path in arquivos],
    }
