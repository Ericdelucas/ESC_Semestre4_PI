"""Sandbox temporario da persona Teste."""

from __future__ import annotations

import streamlit as st

from src.controllers.bootstrap import AppContext
from src.models.financial_metrics import FINANCIAL_METRICS_DICT
from src.views import persona_tabs as view_persona_tabs

TEST_SANDBOX_KEY = "test_sandbox_analyses"
TEST_CHART_LABELS = {
    "Gráfico de Linha": "Linha",
    "Gráfico de Barra": "Barra",
    "Área": "Área",
    "Card KPI": "Card KPI",
}


def _test_sandbox_items() -> list[dict[str, str | None]]:
    items = st.session_state.setdefault(
        TEST_SANDBOX_KEY,
        [{"id": "analise_1", "label": "Análise 1", "metric": None, "chart_type": None}],
    )
    if not isinstance(items, list) or not items:
        items = [{"id": "analise_1", "label": "Análise 1", "metric": None, "chart_type": None}]
        st.session_state[TEST_SANDBOX_KEY] = items
    return items


def _render_test_sandbox_form() -> None:
    metric_names = sorted(FINANCIAL_METRICS_DICT)
    metric_name = st.selectbox(
        "Selecionar Indicador",
        options=metric_names,
        format_func=lambda nome: nome,
        key="test_sandbox_metric",
    )
    chart_label = st.selectbox(
        "Tipo de Visualização",
        options=list(TEST_CHART_LABELS),
        key="test_sandbox_chart",
    )
    if st.button("Criar Gráfico no Sandbox", type="primary", key="test_sandbox_create"):
        items = _test_sandbox_items()
        numero = len(items) + 1
        item = {
            "id": f"teste_{numero}_{metric_name}_{TEST_CHART_LABELS[chart_label]}",
            "label": f"Análise {numero}",
            "metric": metric_name,
            "chart_type": TEST_CHART_LABELS[chart_label],
        }
        items.append(item)
        st.session_state["teste_nav_key"] = item["id"]
        st.session_state["show_test_sandbox_dialog"] = False
        st.rerun()


def _render_test_sandbox_dialog() -> None:
    if not st.session_state.get("show_test_sandbox_dialog"):
        return
    if hasattr(st, "dialog"):
        @st.dialog("Criar gráfico no sandbox")
        def _dialog() -> None:
            _render_test_sandbox_form()

        _dialog()
        return
    with st.expander("Criar gráfico no sandbox", expanded=True):
        _render_test_sandbox_form()


def render_teste_sandbox(ctx: AppContext) -> None:
    items = _test_sandbox_items()
    labels = [str(item["label"]) for item in items]
    ids = [str(item["id"]) for item in items]
    item_by_id = dict(zip(ids, items, strict=True))
    if st.session_state.get("teste_nav_key") not in ids:
        st.session_state["teste_nav_key"] = ids[0]

    default_id = st.session_state["teste_nav_key"]
    default_label = str(item_by_id[default_id]["label"])
    col_nav, col_add = st.columns([0.94, 0.06])
    with col_nav:
        escolha = st.segmented_control(
            "sandbox",
            options=labels,
            default=default_label if default_label in labels else labels[0],
            key=f"teste_sandbox_nav_{len(items)}",
            label_visibility="collapsed",
        )
    with col_add:
        if st.button("+", help="Criar gráfico no sandbox", key="teste_sandbox_add"):
            st.session_state["show_test_sandbox_dialog"] = True
    _render_test_sandbox_dialog()

    label_to_id = dict(zip(labels, ids, strict=True))
    item_id = label_to_id.get(escolha or default_label, ids[0])
    st.session_state["teste_nav_key"] = item_id
    item = item_by_id[item_id]
    st.space("small")
    if not item.get("metric") or not item.get("chart_type"):
        st.info("Use o botão + para criar uma análise financeira temporária neste sandbox.")
        return
    view_persona_tabs.render_custom_analysis(
        ctx.df,
        {"metric": str(item["metric"]), "chart_type": str(item["chart_type"])},
        ctx.cena_sel,
        ctx.ano_sel,
    )
