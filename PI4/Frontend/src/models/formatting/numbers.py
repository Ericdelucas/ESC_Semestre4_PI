"""Formatadores numericos dependentes de idioma."""

from __future__ import annotations

from src.config.i18n import get_lang, t

from .base import fmt_number_en, fmt_number_pt, is_na


def fmt_rs(x: float) -> str:
    if is_na(x):
        return "—"
    sinal = "-" if x < 0 else ""
    v = abs(float(x))
    lang = get_lang()
    if lang == "en":
        if v >= 1e9:
            return f"{sinal}R$ {fmt_number_en(v / 1e9, 2)} {t('fmt.bn')}"
        if v >= 1e6:
            return f"{sinal}R$ {fmt_number_en(v / 1e6, 2)} {t('fmt.mn')}"
        return f"{sinal}R$ {fmt_number_en(v, 0)}"
    if v >= 1e9:
        return f"{sinal}R$ {fmt_number_pt(v / 1e9, 2)} {t('fmt.bn')}"
    if v >= 1e6:
        return f"{sinal}R$ {fmt_number_pt(v / 1e6, 2)} {t('fmt.mn')}"
    return f"{sinal}R$ {fmt_number_pt(v, 0)}"


def fmt_dias(x: float) -> str:
    if is_na(x):
        return "—"
    lang = get_lang()
    v = float(x)
    if lang == "en":
        return f"{fmt_number_en(v, 1)} {t('fmt.days')}"
    return f"{fmt_number_pt(v, 1)} {t('fmt.days')}"


def fmt_pct(x: float) -> str:
    if is_na(x):
        return "—"
    v = float(x) * 100
    if get_lang() == "en":
        return f"{fmt_number_en(v, 2)}%"
    return f"{fmt_number_pt(v, 2)}%"
