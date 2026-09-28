"""Roteador dos KPIs por persona."""

from __future__ import annotations

import pandas as pd

from src.config.glossary import help_text
from src.models.formatting import fmt_dias, fmt_rs

from .ceo import _kpis_ceo
from .concession import _kpis_poder_concedente
from .constants import KpiItem
from .shareholders import _kpis_acionistas


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
        liq = k["liquidez"] if "liquidez" in k.index else float("nan")
        ciclo = k["Ciclo_Financeiro"] if "Ciclo_Financeiro" in k.index else float("nan")
        return [
            ("Necessidade de Capital de Giro (NCG)", fmt_rs(k["NCG"]) if "NCG" in k.index else "—", help_text("ncg")),
            (
                "Saldo de Tesouraria",
                fmt_rs(k["Saldo_Tesouraria"]) if "Saldo_Tesouraria" in k.index else "—",
                help_text("treasury"),
            ),
            (
                "Ciclo Financeiro",
                fmt_dias(ciclo) if pd.notna(ciclo) else "—",
                help_text("cycle"),
            ),
            (
                "Liquidez Corrente (LC)",
                f"{liq:.2f}x" if pd.notna(liq) else "—",
                help_text("liquidity"),
            ),
        ]

    if persona == "acionistas":
        return _kpis_acionistas(df, cena_sel, ano_sel)

    return _kpis_poder_concedente(df, cena_sel, ano_sel)
