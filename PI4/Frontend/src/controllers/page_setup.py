"""Configuracao visual global da aplicacao Streamlit."""

from __future__ import annotations

import streamlit as st


def configure_page() -> None:
    st.set_page_config(layout="wide", page_title="Dashboard CTI", page_icon="📊")
    st.markdown(
        """
        <style>
        .stAppDeployButton {
            visibility: hidden;
            display: none !important;
        }
        #MainMenu {
            visibility: hidden;
            display: none !important;
        }
        header[data-testid="stHeader"] {
            visibility: hidden;
            display: none !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        """
<style>
div[data-testid="stMetricValue"],
div[data-testid="stMetricValue"] * {
  color: #FFFFFF !important;
  -webkit-text-fill-color: #FFFFFF !important;
  opacity: 1 !important;
}
div[data-testid="stMetricLabel"],
div[data-testid="stMetricLabel"] * {
  color: rgba(255, 255, 255, 0.92) !important;
  -webkit-text-fill-color: rgba(255, 255, 255, 0.92) !important;
  opacity: 1 !important;
}
</style>
""",
        unsafe_allow_html=True,
    )
