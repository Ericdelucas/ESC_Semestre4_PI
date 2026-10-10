"""Configuracao visual global da aplicacao Streamlit."""

from __future__ import annotations

import streamlit as st

def configure_page() -> None:
    st.set_page_config(layout="wide", page_title="ESC | Dashboard CTI", page_icon="🔵")
    st.markdown(
        """
    <style>
    /* Oculta estritamente o botão de Deploy do Streamlit */
    .stAppDeployButton {
        display: none !important;
    }
    iframe[title*="CookieManager"],
    iframe[title*="cookie_manager"] {
        height: 0 !important;
        min-height: 0 !important;
        position: absolute !important;
        visibility: hidden !important;
    }
    </style>
""",
        unsafe_allow_html=True,
    )
    st.markdown(
        """
<style>
html, body, .stApp, .main,
[data-testid="stAppViewContainer"],
[data-testid="stMain"],
section.main,
section[data-testid="stMain"] {
  overflow-y: auto !important;
  overflow-x: hidden !important;
  height: auto !important;
  max-height: none !important;
}
.block-container,
[data-testid="stMainBlockContainer"],
.main .block-container,
main .block-container,
section.main .block-container,
div[data-testid="stAppViewContainer"] .block-container {
  width: 100% !important;
  max-width: 100% !important;
  margin-left: 0 !important;
  margin-right: 0 !important;
  padding-left: 2rem !important;
  padding-right: 2rem !important;
  padding-top: 3rem !important;
  height: auto !important;
  max-height: none !important;
  overflow: visible !important;
}
[data-testid="stMain"] {
  width: 100% !important;
}
header[data-testid="stHeader"] {
  background: var(--background-color) !important;
}
div[data-testid="stHeading"],
div[data-testid="stHeading"] h1,
div[data-testid="stHeading"] h2,
div[data-testid="stHeading"] h3,
div[data-testid="stWidgetLabel"],
div[data-testid="stWidgetLabel"] p,
div[data-testid="stWidgetLabel"] label {
  overflow: visible !important;
  line-height: 1.4 !important;
  text-overflow: clip !important;
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
  overflow-y: visible !important;
  padding-top: 0.15rem !important;
  padding-bottom: 0.15rem !important;
  scrollbar-width: thin;
  -webkit-overflow-scrolling: touch;
}
div[class*="st-key-cti_ops_menu"] {
  display: flex !important;
  justify-content: flex-end !important;
  align-items: center !important;
  min-width: 0 !important;
}
div[class*="st-key-cti_ops_menu"] [data-testid="stPopover"] {
  display: flex !important;
  justify-content: flex-end !important;
}
div[class*="st-key-cti_ops_menu"] [data-testid="stPopover"] button,
div[class*="st-key-cti_ops_menu"] button {
  min-width: 2.55rem !important;
  width: 2.55rem !important;
  padding: 0.25rem 0 !important;
  font-size: 1.25rem !important;
  line-height: 1 !important;
}
div[class*="st-key-cti_persona_header"] {
  padding-top: 0.35rem !important;
  margin-bottom: 0.55rem !important;
  overflow: visible !important;
}
div[class*="st-key-cti_persona_header"] [data-testid="stWidgetLabel"] {
  overflow: visible !important;
  white-space: normal !important;
  line-height: 1.45 !important;
  margin-bottom: 0.45rem !important;
  padding-top: 0.1rem !important;
}
div[class*="st-key-cti_persona_header"] div[data-testid="stSegmentedControl"] {
  overflow-x: auto !important;
  overflow-y: visible !important;
  align-items: center !important;
}
div[class*="st-key-cti_persona_header"] [role="radiogroup"] {
  align-items: center !important;
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
  overflow-y: visible !important;
  padding-bottom: 0.5rem !important;
  scrollbar-width: thin !important;
  scrollbar-color: var(--text-color) var(--secondary-background-color) !important;
  -webkit-overflow-scrolling: touch !important;
}
div[class*="st-key-cti_subnav_scroll"] div[data-testid="stSegmentedControl"]::-webkit-scrollbar {
  height: 8px !important;
}
div[class*="st-key-cti_subnav_scroll"] div[data-testid="stSegmentedControl"]::-webkit-scrollbar-track {
  background: var(--secondary-background-color) !important;
  border-radius: 999px !important;
}
div[class*="st-key-cti_subnav_scroll"] div[data-testid="stSegmentedControl"]::-webkit-scrollbar-thumb {
  background: var(--text-color) !important;
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
  color: var(--text-color) !important;
  -webkit-text-fill-color: var(--text-color) !important;
  opacity: 1 !important;
}
div[data-testid="stMetricLabel"],
div[data-testid="stMetricLabel"] * {
  color: var(--text-color) !important;
  -webkit-text-fill-color: var(--text-color) !important;
  opacity: 1 !important;
  white-space: normal !important;
  overflow-wrap: anywhere !important;
  text-overflow: clip !important;
  overflow: visible !important;
}
div[data-testid="stMetricDelta"],
div[data-testid="stMetricDelta"] * {
  white-space: normal !important;
  overflow-wrap: anywhere !important;
  word-break: normal !important;
  text-overflow: clip !important;
  overflow: visible !important;
  max-width: 100% !important;
}
div[data-testid="stMetric"] {
  min-width: 0 !important;
  background: var(--secondary-background-color) !important;
  color: var(--text-color) !important;
  border-radius: 8px !important;
  padding: 0.65rem !important;
  overflow: visible !important;
}
div[data-testid="stMetric"] label,
div[data-testid="stMetricValue"] {
  overflow-wrap: anywhere !important;
  word-break: normal !important;
  white-space: normal !important;
  text-overflow: clip !important;
  overflow: visible !important;
}
@media (max-width: 900px) {
  .block-container,
  [data-testid="stMainBlockContainer"],
  .main .block-container {
    width: 100% !important;
    max-width: 100vw !important;
    padding-left: 0.75rem !important;
    padding-right: 0.75rem !important;
    padding-top: 2.5rem !important;
  }
  div[data-testid="stHorizontalBlock"] {
    flex-wrap: wrap !important;
  }
  div[class*="st-key-cti_header_bar"] div[data-testid="stHorizontalBlock"] {
    flex-wrap: nowrap !important;
    align-items: center !important;
  }
  div[class*="st-key-cti_header_bar"] div[data-testid="column"] {
    flex: 1 1 auto !important;
    width: auto !important;
    min-width: 0 !important;
  }
  div[class*="st-key-cti_header_bar"] div[data-testid="column"]:last-child {
    flex: 0 0 3rem !important;
    width: 3rem !important;
    min-width: 3rem !important;
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
  .block-container,
  [data-testid="stMainBlockContainer"],
  .main .block-container {
    width: 100% !important;
    max-width: 100vw !important;
    padding-left: 0.5rem !important;
    padding-right: 0.5rem !important;
    padding-top: 2.5rem !important;
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

