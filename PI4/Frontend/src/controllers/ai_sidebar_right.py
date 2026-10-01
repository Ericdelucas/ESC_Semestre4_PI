"""Abre o Assistente CTI numa coluna à direita do dashboard."""

from __future__ import annotations

from collections.abc import Callable

import streamlit as st

from src.controllers.bootstrap import AppContext
from src.controllers.resilience import safe_render
from src.views.ai_assistant import render_chat_panel

_CSS_FECHADA = """
<style>
div[class*="st-key-ai_edge"] {
  position: fixed !important;
  top: 46%;
  right: 0;
  width: 2.15rem !important;
  min-width: 2.15rem !important;
  max-width: 2.15rem !important;
  z-index: 999980;
  margin: 0 !important;
  padding: 0 !important;
  background: transparent !important;
  border: 0 !important;
}
div[class*="st-key-ai_edge"] button {
  background: transparent !important;
  color: #d4d4d4 !important;
  border: 0 !important;
  box-shadow: none !important;
  height: 2.1rem !important;
  min-height: 2.1rem !important;
  width: 2.05rem !important;
  padding: 0 !important;
  font-size: 1.05rem !important;
}
[data-testid="stElementContainer"]:has(div[class*="st-key-ai_edge"]) {
  height: 0 !important;
  min-height: 0 !important;
  margin: 0 !important;
  padding: 0 !important;
  overflow: visible !important;
}
</style>
"""


def _painel_aberto() -> bool:
    if "show_chat" not in st.session_state:
        st.session_state.show_chat = True
    return bool(st.session_state.show_chat)


def _abrir() -> None:
    st.session_state.show_chat = True
    st.session_state.ai_panel_open = True


def render_ai_layout(ctx: AppContext, corpo: Callable[[AppContext], None]) -> None:
    """Fecha: só o `>>`. Abre: dashboard à esquerda e o chat à direita."""
    if not _painel_aberto():
        st.markdown(_CSS_FECHADA, unsafe_allow_html=True)
        with st.container(key="ai_edge", border=False):
            st.button(">>", key="ai_fab", help="Abrir o Assistente CTI", type="tertiary", on_click=_abrir)
        corpo(ctx)
        return

    col_main, col_ai = st.columns([3, 1], gap="small", vertical_alignment="top")
    with col_main:
        corpo(ctx)
    with col_ai:
        safe_render(
            "assistente IA",
            render_chat_panel,
            ctx.ranking,
            ctx.n_cenarios,
            ctx.p_ruina,
            ctx.cena_sel,
            ctx.k,
            ctx.ano_enc,
            ctx.ano_sel,
            ctx.df,
            ctx.ind,
        )
