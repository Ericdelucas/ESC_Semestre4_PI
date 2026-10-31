"""Compatibilidade publica do motor RAG."""

from .answers import gerar_llm as _gerar_llm
from .answers import paragrafos_financeiros as _paragrafos_financeiros
from .answers import resolve_api_key
from .answers import resposta_extrativa as _resposta_extrativa
from .config import GEMINI_MODELS as _GEMINI_MODELS
from .config import MARCA_FALA as _MARCA_FALA
from .config import MAX_FILE_BYTES as _MAX_FILE_BYTES
from .config import NOME_TRANSCRICAO as _NOME_TRANSCRICAO
from .config import PDF_SUFFIXES as _PDF_SUFFIXES
from .config import PLACEHOLDER_NAMES as _PLACEHOLDER_NAMES
from .config import SYSTEM_PROMPT_EN, SYSTEM_PROMPT_PT
from .config import TERMOS_FIN as _TERMOS_FIN
from .config import TEXT_SUFFIXES as _TEXT_SUFFIXES
from .context import build_focus_context
from .context import serie_val as _serie_val
from .documents import docs_cenarios as _docs_cenarios
from .documents import docs_glossario as _docs_glossario
from .documents import docs_manuais as _docs_manuais
from .documents import iter_arquivos_doc as _iter_arquivos_doc
from .documents import ler_pdf as _ler_pdf
from .documents import parece_transcricao as _parece_transcricao
from .engine import RagEngine
from .engine import faiss_index as _faiss_index
from .engine import prioridade_fonte as _prioridade_fonte
from .embeddings import TfidfEmbeddings
from .formatters import dias as _dias
from .formatters import pct as _pct
from .formatters import rs as _rs

__all__ = [
    "RagEngine",
    "SYSTEM_PROMPT_EN",
    "SYSTEM_PROMPT_PT",
    "TfidfEmbeddings",
    "_GEMINI_MODELS",
    "_MARCA_FALA",
    "_MAX_FILE_BYTES",
    "_NOME_TRANSCRICAO",
    "_PDF_SUFFIXES",
    "_PLACEHOLDER_NAMES",
    "_TERMOS_FIN",
    "_TEXT_SUFFIXES",
    "_dias",
    "_docs_cenarios",
    "_docs_glossario",
    "_docs_manuais",
    "_faiss_index",
    "_gerar_llm",
    "_iter_arquivos_doc",
    "_ler_pdf",
    "_paragrafos_financeiros",
    "_pct",
    "_parece_transcricao",
    "_prioridade_fonte",
    "_resposta_extrativa",
    "_rs",
    "_serie_val",
    "build_focus_context",
    "resolve_api_key",
]
