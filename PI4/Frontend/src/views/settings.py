"""Tela de configuracoes visuais do dashboard."""

from __future__ import annotations

import streamlit as st


THEME_KEY = "cti_theme_mode"


def get_theme_mode() -> str:
    """Retorna o tema selecionado pelo usuario."""
    return str(st.session_state.get(THEME_KEY, "dark"))


def render() -> None:
    """Renderiza controles de configuracao."""
    st.subheader("Configurações")
    current = get_theme_mode()
    choice = st.segmented_control(
        "Tema",
        options=["Escuro", "Claro"],
        default="Claro" if current == "light" else "Escuro",
        key="theme_mode_selector",
    )
    selected = "light" if choice == "Claro" else "dark"
    if selected != current:
        st.session_state[THEME_KEY] = selected
        st.rerun()
    st.caption("O tema altera a camada visual do dashboard nesta sessão.")
