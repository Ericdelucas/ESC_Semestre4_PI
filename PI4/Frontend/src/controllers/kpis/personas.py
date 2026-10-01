"""Roteador dos KPIs por persona."""

from __future__ import annotations

import pandas as pd

from src.config.glossary import help_text
from src.models.formatting import fmt_dias, fmt_rs

from .ceo import _kpis_ceo
from .concession import _kpis_poder_concedente
from .constants import KpiItem
from .shareholders import _kpis_acionistas


def _zero_se_na(valor: object) -> float:
    if pd.isna(valor):
        return 0.0
    return float(valor)


def kpis_por_persona(
    persona: str,
    k: pd.Series,
    ranking: pd.DataFrame,
    df: pd.DataFrame | None = None,
    cena_sel: str | None = None,
    ano_sel: str | int = "Todos",
) -> list[KpiItem]:
    _ = ranking
    if persona == "ceo":
        return _kpis_ceo(df, cena_sel, ano_sel)

    if persona == "cfo":
        ncg = _zero_se_na(k["NCG"]) if "NCG" in k.index else 0.0
        tesouraria = _zero_se_na(k["Saldo_Tesouraria"]) if "Saldo_Tesouraria" in k.index else 0.0
        liq = _zero_se_na(k["liquidez"]) if "liquidez" in k.index else 0.0
        ciclo = _zero_se_na(k["Ciclo_Financeiro"]) if "Ciclo_Financeiro" in k.index else 0.0
        return [
            ("Necessidade de Capital de Giro (NCG)", fmt_rs(ncg), help_text("ncg")),
            (
                "Saldo de Tesouraria",
                fmt_rs(tesouraria),
                help_text("treasury"),
            ),
            (
                "Ciclo Financeiro",
                fmt_dias(ciclo),
                help_text("cycle"),
            ),
            (
                "Liquidez Corrente (LC)",
                f"{liq:.2f}x",
                help_text("liquidity"),
            ),
        ]

    if persona == "acionistas":
        return _kpis_acionistas(df, cena_sel, ano_sel)

    return _kpis_poder_concedente(df, cena_sel, ano_sel)
