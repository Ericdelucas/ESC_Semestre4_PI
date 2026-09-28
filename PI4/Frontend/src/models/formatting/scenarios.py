"""Formatacao e ordenacao de cenarios."""

from __future__ import annotations

import re

from src.config.i18n import t

_RE_CEN = re.compile(r"(?:Cen[_ ]?|cenário\s*|scenario\s*)(\d+)", re.IGNORECASE)


def cena_id(cena: str) -> int | None:
    """Extrai o numero do cenario de strings como ``Total Cen_00001``."""
    s = str(cena)
    m = _RE_CEN.search(s)
    if m:
        return int(m.group(1))
    digitos = "".join(ch for ch in s if ch.isdigit())
    if digitos:
        return int(digitos)
    return None


def cena_rotulo(cena: str) -> str:
    """Converte ``Total Cen_00001`` -> ``Cenario 00001`` / ``Scenario 00001``."""
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
