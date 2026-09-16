"""Aba Faixa de risco."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from src.components.charts import figura_envelope, figura_histograma_ano, titulo_filtro
from src.components.headers import heading_with_help
from src.components.kpis import render_metric_card
from src.components.resilience import resilient_view, safe_render
from src.config import METRICAS_NUVEM
from src.config.glossary import NUVEM_HELP, help_join, help_text
from src.config.i18n import get_lang, t
from src.data.analytics import resumo_envelope
from src.data.formatting import fmt_rs


@resilient_view("aba Faixa de risco")
def render(
    ind: pd.DataFrame,
    cena_sel: str,
    ano_sel: str | int,
    anos: list[int],
) -> None:
    heading_with_help(t("faixa.title"), "faixa_envelope")
    st.caption(t("faixa.caption"))

    metric_keys = list(METRICAS_NUVEM.keys())
    metric_labels = [t(k) for k in metric_keys]
    label_to_key = dict(zip(metric_labels, metric_keys, strict=True))
    escolhido = st.selectbox(
        t("faixa.metric"),
        options=metric_labels,
        index=0,
        key=f"metrica_nuvem_{get_lang()}",
        help=help_text("metric_picker"),
    )
    metric_key = label_to_key[escolhido]
    col_nuvem, maior_melhor = METRICAS_NUVEM[metric_key]
    rotulo_nuvem = t(metric_key)
    ano_nuvem = None if ano_sel == "Todos" else int(ano_sel)

    def _envelope() -> None:
        st.plotly_chart(
            figura_envelope(
                ind,
                col_nuvem,
                rotulo_nuvem,
                maior_melhor,
                titulo=titulo_filtro(t("faixa.risk_title", metric=rotulo_nuvem), cena_sel, ano_sel),
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
        gloss_metrica = NUVEM_HELP.get(metric_key, "cash_available")
        with e1:
            render_metric_card(
                t("faixa.median"),
                fmt_rs(float(env["mediana"].mean())),
                help_join(gloss_metrica, "faixa_median"),
            )
        with e2:
            render_metric_card(
                t("faixa.mean"),
                fmt_rs(float(env["media"].mean())),
                help_join(gloss_metrica, "faixa_mean"),
            )
        with e3:
            render_metric_card(
                t("faixa.worst"),
                fmt_rs(float(env["pessimista"].min() if maior_melhor else env["pessimista"].max())),
                help_join(gloss_metrica, "faixa_worst"),
            )
        with e4:
            render_metric_card(
                t("faixa.best"),
                fmt_rs(float(env["otimista"].max() if maior_melhor else env["otimista"].min())),
                help_join(gloss_metrica, "faixa_best"),
            )
    except Exception as exc:  # noqa: BLE001
        st.error(str(exc))

    heading_with_help(t("faixa.hist"), "faixa_hist_year")
    if ano_sel == "Todos":
        ano_hist = st.selectbox(
            t("faixa.hist_year"),
            options=anos,
            index=anos.index(9) if 9 in anos else 0,
            key="ano_histograma",
            help=help_text("faixa_hist_year"),
        )
        st.caption(t("faixa.hist_all"))
    else:
        ano_hist = int(ano_sel)
        st.caption(t("faixa.hist_fixed", ano=ano_hist))

    fatia_ano = ind[ind["ano_num"] == ano_hist]

    def _hist() -> None:
        st.plotly_chart(
            figura_histograma_ano(
                fatia_ano,
                col_nuvem,
                rotulo_nuvem,
                ano_hist,
                titulo=titulo_filtro(t("faixa.dist_title", metric=rotulo_nuvem), cena_sel, ano_hist),
            ),
            width="stretch",
            theme="streamlit",
        )

    safe_render("histograma por ano", _hist)
