"""Compatibilidade para utilitarios de formatacao."""

from .base import fmt_number_en as _fmt_number_en
from .base import fmt_number_pt as _fmt_number_pt
from .base import is_na as _is_na
from .comparisons import cenas_padrao_comparacao, melhor_entre
from .numbers import fmt_dias, fmt_pct, fmt_rs
from .scenarios import _RE_CEN, cena_id, cena_rotulo, cena_sort_key
from .texts import texto_ciclo, texto_ncg, texto_tesouraria

__all__ = [
    "_RE_CEN",
    "_fmt_number_en",
    "_fmt_number_pt",
    "_is_na",
    "cenas_padrao_comparacao",
    "cena_id",
    "cena_rotulo",
    "cena_sort_key",
    "fmt_dias",
    "fmt_pct",
    "fmt_rs",
    "melhor_entre",
    "texto_ciclo",
    "texto_ncg",
    "texto_tesouraria",
]
