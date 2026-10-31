"""Helpers de comparacao visual e defaults."""

from __future__ import annotations

from .base import is_na


def melhor_entre(a: float, b: float, *, maior_melhor: bool) -> str:
    if is_na(a) and is_na(b):
        return ""
    if is_na(a):
        return "B"
    if is_na(b):
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
