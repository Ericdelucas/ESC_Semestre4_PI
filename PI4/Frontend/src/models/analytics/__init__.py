"""Compatibilidade publica do pipeline analitico."""

from .indicators import _mapa_contas, montar_indicadores
from .summaries import (
    cenas_por_percentil,
    probabilidade_caixa_negativo,
    resumo_envelope,
    resumo_estatistico,
)

__all__ = [
    "_mapa_contas",
    "cenas_por_percentil",
    "montar_indicadores",
    "probabilidade_caixa_negativo",
    "resumo_envelope",
    "resumo_estatistico",
]
