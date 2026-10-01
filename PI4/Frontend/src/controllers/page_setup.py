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
.block-container {
  width: 100% !important;
  max-width: 100% !important;
  margin-left: 0 !important;
  margin-right: 0 !important;
  padding-left: 2rem !important;
  padding-right: 2rem !important;
  padding-top: 1rem !important;
}
[data-testid="stMain"] {
  width: 100% !important;
}
[data-testid="stMainBlockContainer"],
.main .block-container {
  max-width: 100% !important;
  width: 100% !important;
  padding-left: 2rem !important;
  padding-right: 2rem !important;
  margin-left: 0 !important;
  margin-right: 0 !important;
}
main .block-container,
section.main .block-container,
div[data-testid="stAppViewContainer"] .block-container {
  max-width: 100% !important;
  width: 100% !important;
  margin-left: 0 !important;
  margin-right: 0 !important;
}
section[data-testid="stSidebar"] {
  min-width: min(23rem, 92vw) !important;
}
div[data-testid="stHorizontalBlock"] {
  gap: 0.75rem !important;
}
div[data-testid="column"] {
  min-width: 0 !important;
}
div[data-testid="stDataFrame"],
div[data-testid="stDataEditor"],
div[data-testid="stTable"] {
  width: 100% !important;
  overflow-x: auto !important;
}
div[data-testid="stDataFrame"] > div,
div[data-testid="stDataEditor"] > div {
  max-width: 100% !important;
}
div[data-testid="stPlotlyChart"] {
  width: 100% !important;
  overflow-x: auto !important;
}
div[data-testid="stPlotlyChart"] .js-plotly-plot,
div[data-testid="stPlotlyChart"] .plot-container {
  max-width: 100% !important;
}
div[data-testid="stButton"] button,
div[data-testid="stDownloadButton"] button,
div[data-testid="stFormSubmitButton"] button {
  white-space: normal !important;
  min-height: 2.5rem;
}
div[data-testid="stSegmentedControl"] {
  width: 100% !important;
  max-width: 100% !important;
  overflow-x: auto !important;
  overflow-y: hidden !important;
  padding-bottom: 0.15rem !important;
  scrollbar-width: thin;
  -webkit-overflow-scrolling: touch;
}
div[data-testid="stSegmentedControl"] [role="radiogroup"] {
  display: flex !important;
  flex-wrap: nowrap !important;
  gap: 0.35rem !important;
  width: max-content !important;
  min-width: 100% !important;
  white-space: nowrap !important;
}
div[data-testid="stSegmentedControl"] label,
div[data-testid="stSegmentedControl"] button {
  white-space: nowrap !important;
  overflow-wrap: normal !important;
  text-align: center !important;
}
div[data-testid="stSegmentedControl"] [role="radio"] {
  flex: 0 0 auto !important;
  min-width: max-content !important;
}
div[class*="st-key-cti_subnav_scroll"] {
  width: 100% !important;
  max-width: 100% !important;
  overflow: visible !important;
}
div[class*="st-key-cti_subnav_scroll"] div[data-testid="stHorizontalBlock"] {
  display: flex !important;
  flex-wrap: nowrap !important;
  gap: 0.5rem !important;
  width: 100% !important;
  max-width: 100% !important;
  align-items: stretch !important;
}
div[class*="st-key-cti_subnav_scroll"] div[data-testid="column"]:first-child {
  flex: 1 1 auto !important;
  width: calc(100% - 3.5rem) !important;
  min-width: 0 !important;
}
div[class*="st-key-cti_subnav_scroll"] div[data-testid="column"]:last-child {
  flex: 0 0 3rem !important;
  width: 3rem !important;
  min-width: 3rem !important;
}
div[class*="st-key-cti_subnav_scroll"] div[data-testid="stSegmentedControl"] {
  display: block !important;
  width: 100% !important;
  max-width: 100% !important;
  overflow-x: scroll !important;
  overflow-y: hidden !important;
  padding-bottom: 0.5rem !important;
  scrollbar-width: thin !important;
  scrollbar-color: rgba(255,255,255,.45) rgba(255,255,255,.10) !important;
  -webkit-overflow-scrolling: touch !important;
}
div[class*="st-key-cti_subnav_scroll"] div[data-testid="stSegmentedControl"]::-webkit-scrollbar {
  height: 8px !important;
}
div[class*="st-key-cti_subnav_scroll"] div[data-testid="stSegmentedControl"]::-webkit-scrollbar-track {
  background: rgba(255,255,255,.10) !important;
  border-radius: 999px !important;
}
div[class*="st-key-cti_subnav_scroll"] div[data-testid="stSegmentedControl"]::-webkit-scrollbar-thumb {
  background: rgba(255,255,255,.45) !important;
  border-radius: 999px !important;
}
div[class*="st-key-cti_subnav_scroll"] div[data-testid="stSegmentedControl"] [role="radiogroup"] {
  display: flex !important;
  flex-wrap: nowrap !important;
  width: max-content !important;
  min-width: max-content !important;
  white-space: nowrap !important;
}
div[class*="st-key-cti_subnav_scroll"] div[data-testid="stSegmentedControl"] [role="radio"],
div[class*="st-key-cti_subnav_scroll"] div[data-testid="stSegmentedControl"] label,
div[class*="st-key-cti_subnav_scroll"] div[data-testid="stSegmentedControl"] button {
  flex: 0 0 auto !important;
  white-space: nowrap !important;
  max-width: none !important;
}
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
div[data-testid="stMetric"] {
  min-width: 0 !important;
}
div[data-testid="stMetric"] label,
div[data-testid="stMetricValue"] {
  overflow-wrap: anywhere !important;
  word-break: normal !important;
}
@media (max-width: 900px) {
  .block-container {
    width: 100% !important;
    max-width: 100vw !important;
    padding-left: 0.75rem !important;
    padding-right: 0.75rem !important;
  }
  div[data-testid="stHorizontalBlock"] {
    flex-wrap: wrap !important;
  }
  div[class*="st-key-cti_subnav_scroll"] div[data-testid="stHorizontalBlock"] {
    flex-wrap: nowrap !important;
  }
  div[data-testid="column"] {
    flex: 1 1 100% !important;
    width: 100% !important;
    min-width: 100% !important;
  }
  div[class*="st-key-cti_subnav_scroll"] div[data-testid="column"]:first-child {
    flex: 1 1 auto !important;
    width: calc(100% - 3.5rem) !important;
    min-width: 0 !important;
  }
  div[class*="st-key-cti_subnav_scroll"] div[data-testid="column"]:last-child {
    flex: 0 0 3rem !important;
    width: 3rem !important;
    min-width: 3rem !important;
  }
  div[data-testid="stMetric"] {
    padding: 0.55rem 0 !important;
  }
  div[data-testid="stMetricValue"] {
    font-size: clamp(1.2rem, 7vw, 1.75rem) !important;
  }
  div[data-testid="stTabs"] button {
    white-space: nowrap !important;
  }
  div[data-testid="stTabs"] [role="tablist"] {
    overflow-x: auto !important;
    scrollbar-width: thin;
  }
  div[data-testid="stSelectbox"],
  div[data-testid="stMultiSelect"],
  div[data-testid="stNumberInput"],
  div[data-testid="stTextInput"] {
    width: 100% !important;
  }
}
@media (max-width: 520px) {
  .block-container {
    width: 100% !important;
    max-width: 100vw !important;
    padding-left: 0.5rem !important;
    padding-right: 0.5rem !important;
  }
  h1 { font-size: 1.65rem !important; }
  h2 { font-size: 1.35rem !important; }
  h3 { font-size: 1.12rem !important; }
  div[data-testid="stButton"] button,
  div[data-testid="stDownloadButton"] button,
  div[data-testid="stFormSubmitButton"] button {
    width: 100% !important;
  }
}
</style>
""",
        unsafe_allow_html=True,
    )
