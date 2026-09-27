"""Cabeçalhos, banners e auditoria."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from src.config import COR_ANCORA
from src.config.glossary import help_text
from src.config.i18n import t
from src.models.formatting import cena_rotulo


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
    bruto = df.loc[df["CENA"] == cena_sel]
    if ano_sel != "Todos":
        bruto = bruto.loc[bruto["ano_num"] == ano_sel]
    n = len(bruto)
    with st.expander(t("audit.title")):
        st.caption(
            t(
                "audit.found",
                n=f"{n:,}",
                cena=cena_rotulo(cena_sel),
                recorte=recorte_label(ano_sel),
            )
        )
        if n == 0:
            st.warning(t("audit.empty"))
            return
        visao = bruto[["ANO", "CENA", "CONTA", "VALOR"]].copy()
        st.dataframe(visao, width="stretch", hide_index=True)


def heading_with_help(title: str, gloss_key: str) -> None:
    """Título de seção com tooltip nativo (ⓘ) a partir do glossário."""
    body = title.lstrip("#").strip()
    st.subheader(body, help=help_text(gloss_key))
