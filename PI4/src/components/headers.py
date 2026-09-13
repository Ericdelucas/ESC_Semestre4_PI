"""Cabeçalhos, banners e auditoria."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from src.components.charts import recorte_label
from src.config import COR_ANCORA


def banner_auditoria_filtro(cena_sel: str, ano_sel: str | int) -> None:
    ano_txt = "Todos" if ano_sel == "Todos" else str(ano_sel)
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
📌 Exibindo dados de: Cenário {cena_sel} | Ano {ano_txt}
</div>
""",
        unsafe_allow_html=True,
    )


def expander_auditoria_base(df: pd.DataFrame, cena_sel: str, ano_sel: str | int) -> None:
    bruto = df.loc[df["CENA"] == cena_sel]
    if ano_sel != "Todos":
        bruto = bruto.loc[bruto["ano_num"] == ano_sel]
    n = len(bruto)
    with st.expander("🔍 Conferir dados brutos (Auditoria)"):
        st.caption(
            f"{n:,} registros encontrados na base para **{cena_sel}** · recorte **{recorte_label(ano_sel)}**."
        )
        if n == 0:
            st.warning("Nenhuma linha da base corresponde a este recorte.")
            return
        visao = bruto[["ANO", "CENA", "CONTA", "VALOR"]].copy()
        st.dataframe(visao, width="stretch", hide_index=True)


def render_titulo() -> None:
    st.title("Painel financeiro CTI")
    st.caption(
        "Leitura executiva dos cenários de planejamento · capital de giro, risco × retorno e probabilidade de caixa"
    )
