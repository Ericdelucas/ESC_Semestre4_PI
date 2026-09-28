"""Renderizacao visual dos cards de KPI."""

from __future__ import annotations

from html import escape

import streamlit as st

from src.config import COR, CORES_SELO
from src.config.i18n import t, translate_selo

from .constants import KpiItem

_KPI_FORCE_CSS = """
<style>
div[data-testid="stMetricValue"],
div[data-testid="stMetricValue"] > div,
div[data-testid="stMetricValue"] span,
div[data-testid="stMetricValue"] p {
  color: #FFFFFF !important;
  -webkit-text-fill-color: #FFFFFF !important;
  opacity: 1 !important;
  filter: none !important;
  font-weight: 700 !important;
}
div[data-testid="stMetricLabel"],
div[data-testid="stMetricLabel"] > div,
div[data-testid="stMetricLabel"] span,
div[data-testid="stMetricLabel"] p,
div[data-testid="stMetricLabel"] label {
  color: rgba(255, 255, 255, 0.92) !important;
  -webkit-text-fill-color: rgba(255, 255, 255, 0.92) !important;
  opacity: 1 !important;
  filter: none !important;
}
div[data-testid="stMetric"] {
  opacity: 1 !important;
  filter: none !important;
  color: #FFFFFF !important;
  -webkit-text-fill-color: #FFFFFF !important;
}
</style>
"""


def _garantir_css_metricas() -> None:
    if st.session_state.get("_cti_kpi_css_ok"):
        return
    st.markdown(_KPI_FORCE_CSS, unsafe_allow_html=True)
    st.session_state["_cti_kpi_css_ok"] = True


def card_selo_html(nome: str, qtd: int, ativo: bool) -> str:
    cor = CORES_SELO.get(nome, COR)
    borda = "3px solid #111" if ativo else f"1px solid {cor}"
    fundo = f"{cor}22" if not ativo else f"{cor}44"
    rotulo = translate_selo(nome)
    return f"""
<div style="
    border:{borda};
    background:{fundo};
    border-radius:10px;
    padding:0.65rem 0.75rem;
    min-height:4.6rem;
    color:#FFFFFF;
    -webkit-text-fill-color:#FFFFFF;
">
  <div style="font-size:0.78rem;font-weight:700;color:{cor};-webkit-text-fill-color:{cor};line-height:1.25;">{escape(rotulo)}</div>
  <div style="font-size:1.15rem;font-weight:700;margin-top:0.35rem;color:#FFFFFF;-webkit-text-fill-color:#FFFFFF;">{escape(t("map.scenarios_n", n=qtd))}</div>
</div>
"""


def render_metric_card(label: str, value: str, dica: str | None = None) -> None:
    """Uma metrica nativa + CSS de contraste; tooltip unico via ``help``."""
    _garantir_css_metricas()
    if dica:
        st.metric(label, value, help=dica)
    else:
        st.metric(label, value)


def render_kpi_row(itens: list[KpiItem]) -> None:
    """Linha de KPIs com ``st.metric`` e contraste forcado no Dark Mode."""
    if not itens:
        return
    st.markdown(_KPI_FORCE_CSS, unsafe_allow_html=True)
    st.session_state["_cti_kpi_css_ok"] = True
    cols = st.columns(len(itens))
    for col, item in zip(cols, itens, strict=True):
        if len(item) == 4:
            rotulo, valor, delta, dica = item
        else:
            rotulo, valor, dica = item
            delta = None
        with col:
            if dica:
                st.metric(rotulo, valor, delta=delta, help=dica, delta_color="off")
            else:
                st.metric(rotulo, valor, delta=delta, delta_color="off")
