"""Injeta o chat flutuante por cima do dashboard, sem empurrar o layout."""

from __future__ import annotations

from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

_HTML = Path(__file__).with_name("chat_widget.html")

# O iframe do componente é fixado no canto. height=0 cortaria o widget.
_CSS = """
<style>
[data-testid="stElementContainer"]:has([data-testid="stCustomComponentV1"]) {
  position: fixed !important;
  right: 12px !important;
  bottom: 12px !important;
  width: 380px !important;
  height: 540px !important;
  z-index: 999999 !important;
  margin: 0 !important;
  padding: 0 !important;
  overflow: visible !important;
}
[data-testid="stElementContainer"]:has([data-testid="stCustomComponentV1"]) iframe {
  border: 0 !important;
  background: transparent !important;
}
</style>
"""


def render_floating_chat() -> None:
    """Lê chat_widget.html e sobrepõe a janela ao dashboard."""
    st.markdown(_CSS, unsafe_allow_html=True)
    html_code = _HTML.read_text(encoding="utf-8")
    components.html(html_code, height=540, width=380, scrolling=False)
