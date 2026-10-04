"""RAG do Assistente CTI. Dados locais: ./Cti.csv, ./documentos/ e ./cache/."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parent
CSV_PATH = BACKEND_DIR / "Cti.csv"
DOCS_DIR = BACKEND_DIR / "documentos"
CACHE_DIR = BACKEND_DIR / "cache"
load_dotenv(BACKEND_DIR / ".env")
load_dotenv(BACKEND_DIR.parent / ".env")

_FRONTEND = BACKEND_DIR.parent / "Frontend"
if str(_FRONTEND) not in sys.path:
    sys.path.insert(0, str(_FRONTEND))

from Backend.data_loader import load_cti_csv
from Backend.metrics import montar_indicadores
from src.models.rag_engine import RagEngine, resolve_api_key


class CTIRag:
    """Indexa a base CTI e devolve a resposta textual do consultor."""

    def __init__(self) -> None:
        ranking = _carregar_ranking()
        self._engine = RagEngine.from_ranking(ranking)

    def responder(
        self,
        message: str,
        history: list[dict[str, str]] | None = None,
    ) -> tuple[str, list[str]]:
        resposta, fontes = self._engine.ask(
            message,
            lang="pt",
            history=history or [],
            api_key=resolve_api_key(),
            extra_context="",
            cena_sel=None,
        )
        return resposta, fontes


def _carregar_ranking() -> pd.DataFrame:
    CACHE_DIR.mkdir(exist_ok=True)
    cache = CACHE_DIR / "ranking.parquet"
    if cache.exists() and CSV_PATH.exists() and cache.stat().st_mtime >= CSV_PATH.stat().st_mtime:
        return pd.read_parquet(cache)
    df = load_cti_csv(CSV_PATH)
    _ind, ranking = montar_indicadores(df)
    return ranking
