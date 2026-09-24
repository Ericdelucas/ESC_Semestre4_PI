"""Formatação humana e utilitários de interface (rótulos, seleção, comparação visual)."""

from __future__ import annotations

import re
from typing import Any

from src.config.i18n import get_lang, t

_RE_CEN = re.compile(r"(?:Cen[_ ]?|cenário\s*|scenario\s*)(\d+)", re.IGNORECASE)


def _is_na(x: Any) -> bool:
    if x is None:
        return True
    try:
        return x != x  # NaN
    except Exception:
        return False


def _fmt_number_pt(v: float, decimals: int) -> str:
    if decimals == 0:
        raw = f"{v:,.0f}"
    else:
        raw = f"{v:,.{decimals}f}"
    return raw.replace(",", "X").replace(".", ",").replace("X", ".")


def _fmt_number_en(v: float, decimals: int) -> str:
    if decimals == 0:
        return f"{v:,.0f}"
    return f"{v:,.{decimals}f}"


def fmt_rs(x: float) -> str:
    if _is_na(x):
        return "—"
    sinal = "-" if x < 0 else ""
    v = abs(float(x))
    lang = get_lang()
    if lang == "en":
        if v >= 1e9:
            return f"{sinal}R$ {_fmt_number_en(v / 1e9, 2)} {t('fmt.bn')}"
        if v >= 1e6:
            return f"{sinal}R$ {_fmt_number_en(v / 1e6, 2)} {t('fmt.mn')}"
        return f"{sinal}R$ {_fmt_number_en(v, 0)}"
    if v >= 1e9:
        return f"{sinal}R$ {_fmt_number_pt(v / 1e9, 2)} {t('fmt.bn')}"
    if v >= 1e6:
        return f"{sinal}R$ {_fmt_number_pt(v / 1e6, 2)} {t('fmt.mn')}"
    return f"{sinal}R$ {_fmt_number_pt(v, 0)}"


def fmt_dias(x: float) -> str:
    if _is_na(x):
        return "—"
    lang = get_lang()
    v = float(x)
    if lang == "en":
        return f"{_fmt_number_en(v, 1)} {t('fmt.days')}"
    return f"{_fmt_number_pt(v, 1)} {t('fmt.days')}"


def fmt_pct(x: float) -> str:
    if _is_na(x):
        return "—"
    v = float(x) * 100
    if get_lang() == "en":
        return f"{_fmt_number_en(v, 2)}%"
    return f"{_fmt_number_pt(v, 2)}%"


def texto_ncg(ncg: float) -> str:
    if _is_na(ncg):
        return t("txt.ncg.na")
    if ncg > 0:
        return t("txt.ncg.pos")
    if ncg < 0:
        return t("txt.ncg.neg")
    return t("txt.ncg.zero")


def texto_tesouraria(saldo: float) -> str:
    if _is_na(saldo):
        return t("txt.treasury.na")
    if saldo >= 0:
        return t("txt.treasury.ok")
    return t("txt.treasury.bad")


def texto_ciclo(dias: float) -> str:
    if _is_na(dias):
        return t("txt.cycle.na")
    d = fmt_dias(dias)
    if dias > 30:
        return t("txt.cycle.long", dias=d)
    if dias > 0:
        return t("txt.cycle.mod", dias=d)
    return t("txt.cycle.neg", dias=d)


def cena_id(cena: str) -> int | None:
    """Extrai o número do cenário de strings como ``Total Cen_00001``."""
    s = str(cena)
    m = _RE_CEN.search(s)
    if m:
        return int(m.group(1))
    digitos = "".join(ch for ch in s if ch.isdigit())
    if digitos:
        return int(digitos)
    return None


def cena_rotulo(cena: str) -> str:
    """Converte ``Total Cen_00001`` → ``Cenário 00001`` / ``Scenario 00001``."""
    s = str(cena)
    m = _RE_CEN.search(s)
    prefix = t("scenario.prefix")
    if m:
        return f"{prefix} {m.group(1)}"
    n = cena_id(cena)
    if n is not None:
        return f"{prefix} {n:05d}"
    return s


def cena_sort_key(cena: str) -> tuple[int, str]:
    n = cena_id(cena)
    return (n if n is not None else 10**9, str(cena))


def melhor_entre(a: float, b: float, *, maior_melhor: bool) -> str:
    if _is_na(a) and _is_na(b):
        return ""
    if _is_na(a):
        return "B"
    if _is_na(b):
        return "A"
    if maior_melhor:
        if a > b:
            return "A"
        if b > a:
            return "B"
    else:
        if a < b:
            return "A"
        if b < a:
            return "B"
    return ""


def cenas_padrao_comparacao(cenas: list[str]) -> list[str]:
    escolhidas: list[str] = []
    for alvo in ("00001", "00500"):
        match = next((c for c in cenas if alvo in str(c)), None)
        if match is not None:
            escolhidas.append(match)
    if len(escolhidas) < 2:
        return cenas[:2]
    return escolhidas[:2]
