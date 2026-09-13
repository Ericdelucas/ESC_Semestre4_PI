"""Pacote de dados CTI."""

from src.data.analytics import (
    cenas_padrao_comparacao,
    cenas_por_percentil,
    cena_rotulo,
    melhor_entre,
    montar_indicadores,
    probabilidade_caixa_negativo,
    resumo_envelope,
    resumo_estatistico,
)
from src.data.formatting import fmt_dias, fmt_pct, fmt_rs, texto_ciclo, texto_ncg, texto_tesouraria
from src.data.loaders import load_cti_csv, magnitude, separar_demonstrativos, soma_contas

__all__ = [
    "cenas_padrao_comparacao",
    "cenas_por_percentil",
    "cena_rotulo",
    "fmt_dias",
    "fmt_pct",
    "fmt_rs",
    "load_cti_csv",
    "magnitude",
    "melhor_entre",
    "montar_indicadores",
    "probabilidade_caixa_negativo",
    "resumo_envelope",
    "resumo_estatistico",
    "separar_demonstrativos",
    "soma_contas",
    "texto_ciclo",
    "texto_ncg",
    "texto_tesouraria",
]
