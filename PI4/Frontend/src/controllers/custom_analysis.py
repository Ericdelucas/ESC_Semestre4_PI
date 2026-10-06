"""Estado e formulario de analises financeiras customizadas."""

from __future__ import annotations

import streamlit as st

from src.models.financial_metrics import FINANCIAL_METRICS_DICT

CUSTOM_ANALYSES_KEY = "custom_financial_analyses"
MODAL_CUSTOM_ANALYSIS_KEY = "modal_custom_analysis_open"
CHART_TYPES = ["Linha", "Barra", "Área", "Card KPI"]


def custom_analysis_modal_key(persona: str) -> str:
    """Chave unica do modal de analise customizada por persona."""
    return f"{MODAL_CUSTOM_ANALYSIS_KEY}_{persona}"


def set_custom_analysis_modal(persona: str, open_: bool) -> None:
    """Abre/fecha o modal e limpa a chave legada."""
    st.session_state[custom_analysis_modal_key(persona)] = open_
    st.session_state[MODAL_CUSTOM_ANALYSIS_KEY] = open_
    st.session_state[f"show_custom_analysis_dialog_{persona}"] = False


def custom_store() -> dict[str, list[dict[str, str]]]:
    store = st.session_state.setdefault(CUSTOM_ANALYSES_KEY, {})
    return store if isinstance(store, dict) else {}


def custom_analyses(persona: str) -> list[dict[str, str]]:
    store = custom_store()
    analyses = store.setdefault(persona, [])
    return analyses if isinstance(analyses, list) else []


def custom_key(analysis: dict[str, str]) -> str:
    return f"custom::{analysis['id']}"


def custom_label(analysis: dict[str, str]) -> str:
    return analysis.get("label", f"{analysis['metric']} · {analysis['chart_type']}")


def insert_custom_tabs(nav_keys: list[str], custom_keys: list[str]) -> list[str]:
    if "comparar" not in nav_keys:
        return [*nav_keys, *custom_keys]
    idx = nav_keys.index("comparar")
    return [*nav_keys[:idx], *custom_keys, *nav_keys[idx:]]


def _render_custom_analysis_form(persona: str) -> None:
    metric_names = sorted(FINANCIAL_METRICS_DICT)
    metric_name = st.selectbox(
        "Indicador financeiro",
        options=metric_names,
        format_func=lambda nome: nome,
        key=f"custom_metric_{persona}",
    )
    chart_type = st.selectbox("Tipo de gráfico", options=CHART_TYPES, key=f"custom_chart_{persona}")
    if st.button("Adicionar ao Dashboard", type="primary", key=f"custom_add_{persona}"):
        analyses = custom_analyses(persona)
        numero = len(analyses) + 1
        analysis = {
            "id": f"{numero}_{metric_name}_{chart_type}",
            "label": f"{metric_name} · {chart_type} #{numero}",
            "metric": metric_name,
            "chart_type": chart_type,
        }
        analyses.append(analysis)
        st.session_state["nav_key"] = custom_key(analysis)
        st.session_state[f"show_custom_analysis_dialog_{persona}"] = False
        st.rerun()


def render_custom_analysis_dialog(persona: str) -> None:
    flag = f"show_custom_analysis_dialog_{persona}"
    if not st.session_state.get(flag):
        return
    if hasattr(st, "dialog"):
        @st.dialog("Adicionar análise customizada")
        def _dialog() -> None:
            _render_custom_analysis_form(persona)

        _dialog()
        return
    with st.expander("Adicionar análise customizada", expanded=True):
        _render_custom_analysis_form(persona)
