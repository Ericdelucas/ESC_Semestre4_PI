"""Pacote de dados CTI — imports sob demanda (evita ciclo na inicialização)."""

from __future__ import annotations

__all__ = [
    "cena_rotulo",
    "cena_sort_key",
    "cenas_padrao_comparacao",
    "cenas_por_percentil",
    "classificar_cenarios",
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


def __getattr__(name: str):
    if name in {
        "fmt_rs",
        "fmt_dias",
        "fmt_pct",
        "texto_ncg",
        "texto_tesouraria",
        "texto_ciclo",
        "cena_rotulo",
        "cena_sort_key",
        "melhor_entre",
        "cenas_padrao_comparacao",
    }:
        from src.models import formatting as mod

        return getattr(mod, name)
    if name in {
        "montar_indicadores",
        "resumo_envelope",
        "resumo_estatistico",
        "cenas_por_percentil",
        "probabilidade_caixa_negativo",
    }:
        from src.models import analytics as mod

        return getattr(mod, name)
    if name == "classificar_cenarios":
        from src.models.classifiers import classificar_cenarios

        return classificar_cenarios
    if name in {"load_cti_csv", "magnitude", "separar_demonstrativos", "soma_contas"}:
        from src.models import loaders as mod

        return getattr(mod, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
