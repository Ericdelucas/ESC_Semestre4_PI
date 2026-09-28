"""Textos explicativos para indicadores financeiros."""

from __future__ import annotations

from src.config.i18n import t

from .base import is_na
from .numbers import fmt_dias


def texto_ncg(ncg: float) -> str:
    if is_na(ncg):
        return t("txt.ncg.na")
    if ncg > 0:
        return t("txt.ncg.pos")
    if ncg < 0:
        return t("txt.ncg.neg")
    return t("txt.ncg.zero")


def texto_tesouraria(saldo: float) -> str:
    if is_na(saldo):
        return t("txt.treasury.na")
    if saldo >= 0:
        return t("txt.treasury.ok")
    return t("txt.treasury.bad")


def texto_ciclo(dias: float) -> str:
    if is_na(dias):
        return t("txt.cycle.na")
    d = fmt_dias(dias)
    if dias > 30:
        return t("txt.cycle.long", dias=d)
    if dias > 0:
        return t("txt.cycle.mod", dias=d)
    return t("txt.cycle.neg", dias=d)
