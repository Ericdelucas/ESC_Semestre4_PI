"""Aba Como ler estes números."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from src.controllers.resilience import resilient_view
from src.config.i18n import t
from src.models.formatting import cena_rotulo, fmt_pct


@resilient_view("aba Como ler")
def render(
    n_cenarios: int,
    cena_sel: str,
    k: pd.Series,
    ano_enc: int,
    p_ruina: float,
) -> None:
    st.markdown(
        t(
            "como_ler.body",
            n=f"{n_cenarios:,}",
            cena=cena_rotulo(cena_sel),
            rent=fmt_pct(k["rentabilidade"]),
            risco=fmt_pct(k["risco"]) if pd.notna(k["risco"]) else "—",
            ano=ano_enc,
            p_ruina=p_ruina,
        )
    )
