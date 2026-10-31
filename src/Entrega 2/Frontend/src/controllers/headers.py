"""Cabeçalhos, banners e auditoria."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from src.config import COR_ANCORA
from src.config.glossary import help_text
from src.config.i18n import t
from src.models.formatting import cena_rotulo, is_all_scenarios
from src.models.formatting.tables import render_table


def recorte_label(ano_sel: str | int) -> str:
    return t("filter.all") if ano_sel == "Todos" else t("filter.year_n", n=ano_sel)


def banner_auditoria_filtro(cena_sel: str, ano_sel: str | int) -> None:
    ano_txt = t("filter.all") if ano_sel == "Todos" else str(ano_sel)
    st.markdown(
        f"""
<div style="
    background: linear-gradient(90deg, rgba(232,192,122,0.16), rgba(91,138,122,0.10));
    border: 1px solid #C4A15A;
    border-left: 6px solid {COR_ANCORA};
    border-radius: 8px;
    padding: 0.8rem 1.1rem;
    margin: 0.15rem 0 0.85rem 0;
    font-size: 1.05rem;
    font-weight: 600;
    letter-spacing: 0.01em;
    line-height: 1.45;
">
📌 {t("banner.showing", cena=cena_rotulo(cena_sel), ano=ano_txt)}
</div>
""",
        unsafe_allow_html=True,
    )


def expander_auditoria_base(df: pd.DataFrame, cena_sel: str, ano_sel: str | int) -> None:
    """Nao materializa o recorte completo em todo rerun — isso derrubava o websocket."""
    if df is None or df.empty:
        with st.expander(t("audit.title")):
            st.warning(t("audit.empty"))
        return
    recorte_completo = is_all_scenarios(cena_sel) and ano_sel == "Todos"
    n = int(st.session_state.get("cti_row_count") or 0) if recorte_completo else None
    with st.expander(t("audit.title")):
        if recorte_completo:
            st.caption(
                t(
                    "audit.found",
                    n=f"{n:,}",
                    cena=cena_rotulo(cena_sel),
                    recorte=recorte_label(ano_sel),
                )
            )
            return
        bruto = df.loc[df["CENA"] == cena_sel] if "CENA" in df.columns else df
        if ano_sel != "Todos" and "ano_num" in bruto.columns:
            bruto = bruto.loc[pd.to_numeric(bruto["ano_num"], errors="coerce") == int(ano_sel)]
        n_recorte = len(bruto)
        st.caption(
            t(
                "audit.found",
                n=f"{n_recorte:,}",
                cena=cena_rotulo(cena_sel),
                recorte=recorte_label(ano_sel),
            )
        )
        if n_recorte == 0:
            st.warning(t("audit.empty"))
            return
        colunas = [c for c in ("ANO", "CENA", "CONTA", "VALOR") if c in bruto.columns]
        visao = bruto[colunas].head(80)
        if n_recorte > 80:
            st.caption(t("audit.sample", n=80, total=f"{n_recorte:,}"))
        render_table(visao)


def heading_with_help(title: str, gloss_key: str) -> None:
    """Título de seção com tooltip nativo (ⓘ) a partir do glossário."""
    body = title.lstrip("#").strip()
    st.subheader(body, help=help_text(gloss_key))
