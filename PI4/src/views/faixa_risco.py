"""Aba Faixa de risco."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from src.components.charts import figura_envelope, figura_histograma_ano, titulo_filtro
from src.components.resilience import safe_render
from src.config import METRICAS_NUVEM
from src.data.analytics import resumo_envelope
from src.data.formatting import fmt_rs


def render(
    ind: pd.DataFrame,
    cena_sel: str,
    ano_sel: str | int,
    anos: list[int],
) -> None:
    st.markdown("#### Envelope de probabilidade (todos os cenários)")
    st.caption(
        "Cada ponto é um cenário. A faixa sombreada cobre 90% dos casos (percentis 5 e 95). "
        "A mediana é o caminho mais típico; as linhas de extremo são o pior e o melhor caso."
    )
    rotulo_nuvem = st.selectbox("Métrica da nuvem", options=list(METRICAS_NUVEM.keys()), index=0, key="metrica_nuvem")
    col_nuvem, maior_melhor = METRICAS_NUVEM[rotulo_nuvem]
    ano_nuvem = None if ano_sel == "Todos" else int(ano_sel)

    def _envelope() -> None:
        st.plotly_chart(
            figura_envelope(
                ind,
                col_nuvem,
                rotulo_nuvem,
                maior_melhor,
                titulo=titulo_filtro(f"Faixa de risco — {rotulo_nuvem}", cena_sel, ano_sel),
                ano_destaque=ano_nuvem,
                cena_destaque=cena_sel,
            ),
            width="stretch",
            theme="streamlit",
        )

    safe_render("envelope de probabilidade", _envelope)

    try:
        env = resumo_envelope(ind, col_nuvem, maior_melhor)
        e1, e2, e3, e4 = st.columns(4)
        e1.metric("Mediana no horizonte", fmt_rs(float(env["mediana"].mean())))
        e2.metric("Média no horizonte", fmt_rs(float(env["media"].mean())))
        e3.metric(
            "Pior caso (extremo)",
            fmt_rs(float(env["pessimista"].min() if maior_melhor else env["pessimista"].max())),
        )
        e4.metric(
            "Melhor caso (extremo)",
            fmt_rs(float(env["otimista"].max() if maior_melhor else env["otimista"].min())),
        )
    except Exception as exc:  # noqa: BLE001
        st.error("Não foi possível carregar os KPIs do envelope no momento.")
        st.caption(f"{type(exc).__name__}: {exc}")

    st.markdown("#### Histograma por ano")
    if ano_sel == "Todos":
        ano_hist = st.selectbox(
            "Ano da distribuição",
            options=anos,
            index=anos.index(9) if 9 in anos else 0,
            key="ano_histograma",
        )
        st.caption("O filtro da barra lateral está em **Todos** — escolha o ano do histograma acima.")
    else:
        ano_hist = int(ano_sel)
        st.caption(f"Usando o ano do filtro lateral: **Ano {ano_hist}**.")

    fatia_ano = ind[ind["ano_num"] == ano_hist]

    def _hist() -> None:
        st.plotly_chart(
            figura_histograma_ano(
                fatia_ano,
                col_nuvem,
                rotulo_nuvem,
                ano_hist,
                titulo=titulo_filtro(f"Distribuição de {rotulo_nuvem}", cena_sel, ano_hist),
            ),
            width="stretch",
            theme="streamlit",
        )

    safe_render("histograma por ano", _hist)
