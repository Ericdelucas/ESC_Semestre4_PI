"""Navegacao principal e renderizacao das abas analiticas."""

from __future__ import annotations

import streamlit as st

from src.config import NAV_KEYS
from src.config.i18n import get_lang, t
from src.controllers.bootstrap import AppContext, render_cabecalho
from src.controllers.custom_analysis import (
    custom_analyses,
    custom_key,
    custom_label,
    insert_custom_tabs,
    render_custom_analysis_dialog,
)
from src.controllers.headers import expander_auditoria_base
from src.controllers.resilience import safe_render
from src.controllers.test_sandbox import render_teste_sandbox
from src.views import (
    capital_giro as view_capital_giro,
    comparar as view_comparar,
    como_ler as view_como_ler,
    distribuicao as view_distribuicao,
    faixa_risco as view_faixa_risco,
    mapeamento_risco as view_mapeamento_risco,
    persona_tabs as view_persona_tabs,
    prazos_ciclo as view_prazos_ciclo,
)

VIEW_RENDERERS = {
    "capital_giro": lambda ctx: view_capital_giro.render(ctx.foco, ctx.foco_ano, ctx.cena_sel, ctx.ano_sel),
    "prazos": lambda ctx: view_prazos_ciclo.render(ctx.foco, ctx.k, ctx.cena_sel, ctx.ano_sel),
    "mapeamento": lambda ctx: view_mapeamento_risco.render(ctx.ranking, ctx.persona, ctx.cenas, ctx.mapa_rotulo, ctx.n_cenarios),
    "distribuicao": lambda ctx: view_distribuicao.render(ctx.ranking, ctx.ano_enc, ctx.n_cenarios, ctx.p_ruina),
    "faixa": lambda ctx: view_faixa_risco.render(ctx.ind, ctx.cena_sel, ctx.ano_sel, ctx.anos),
    "comparar": lambda ctx: view_comparar.render(ctx.ind, ctx.cenas, ctx.cena_sel, ctx.ano_sel),
    "como_ler": lambda ctx: view_como_ler.render(ctx.n_cenarios, ctx.cena_sel, ctx.k, ctx.ano_enc, ctx.p_ruina),
}

PERSONA_NAV_KEYS = {
    "ceo": ["ceo_geral", "ceo_dre", "ceo_break_even", "ceo_ltv_cac", "comparar"],
    "cfo": NAV_KEYS,
    "acionistas": ["acionistas_retorno", "acionistas_eva", "acionistas_dividendos", "comparar"],
    "concedente": ["concedente_capex", "concedente_solvencia", "concedente_ativos", "comparar"],
}

PERSONA_NAV_LABELS = {
    "ceo_geral": "Visão Geral & DRE",
    "ceo_dre": "DRE Operacional",
    "ceo_break_even": "Break-Even & Margens",
    "ceo_ltv_cac": "Eficiência LTV/CAC",
    "acionistas_retorno": "Retorno & ROIC",
    "acionistas_eva": "Geração de EVA",
    "acionistas_dividendos": "Lucro Líquido & Dividendos",
    "concedente_capex": "Plano de CAPEX",
    "concedente_solvencia": "Solvência & Liquidez Geral",
    "concedente_ativos": "Ativos Reversíveis",
}

PERSONA_VIEW_RENDERERS = {
    "ceo_geral": lambda ctx: view_persona_tabs.render_ceo_visao_geral(ctx.df, ctx.cena_sel, ctx.ano_sel),
    "ceo_dre": lambda ctx: view_persona_tabs.render_ceo_dre_operacional(ctx.df, ctx.cena_sel, ctx.ano_sel),
    "ceo_break_even": lambda ctx: view_persona_tabs.render_ceo_break_even(ctx.df, ctx.cena_sel, ctx.ano_sel),
    "ceo_ltv_cac": lambda ctx: view_persona_tabs.render_ceo_ltv_cac(ctx.df, ctx.cena_sel, ctx.ano_sel),
    "acionistas_retorno": lambda ctx: view_persona_tabs.render_acionistas_retorno(ctx.df, ctx.cena_sel, ctx.ano_sel),
    "acionistas_eva": lambda ctx: view_persona_tabs.render_acionistas_eva(ctx.df, ctx.cena_sel, ctx.ano_sel),
    "acionistas_dividendos": lambda ctx: view_persona_tabs.render_acionistas_dividendos(ctx.df, ctx.cena_sel, ctx.ano_sel),
    "concedente_capex": lambda ctx: view_persona_tabs.render_concedente_capex(ctx.df, ctx.cena_sel, ctx.ano_sel),
    "concedente_solvencia": lambda ctx: view_persona_tabs.render_concedente_solvencia(ctx.df, ctx.cena_sel, ctx.ano_sel),
    "concedente_ativos": lambda ctx: view_persona_tabs.render_concedente_ativos(ctx.df, ctx.cena_sel, ctx.ano_sel),
    "comparar": lambda ctx: view_persona_tabs.render_comparar_cenarios(ctx.df, ctx.ind, ctx.cenas, ctx.persona, ctx.ano_sel),
}


def render_analises(ctx: AppContext) -> None:
    if ctx.persona == "teste":
        render_teste_sandbox(ctx)
        return

    lang = get_lang()
    base_nav_keys = PERSONA_NAV_KEYS.get(ctx.persona, NAV_KEYS)
    analyses = custom_analyses(ctx.persona)
    custom_keys = [custom_key(analysis) for analysis in analyses]
    custom_by_key = dict(zip(custom_keys, analyses, strict=True))
    nav_keys = insert_custom_tabs(base_nav_keys, custom_keys)
    renderers = {**VIEW_RENDERERS, "comparar": PERSONA_VIEW_RENDERERS["comparar"]} if ctx.persona == "cfo" else PERSONA_VIEW_RENDERERS
    if st.session_state.get("nav_key") not in nav_keys:
        st.session_state["nav_key"] = nav_keys[0]
    labels = [
        custom_label(custom_by_key[k])
        if k in custom_by_key
        else t(f"nav.{k}") if k in NAV_KEYS else PERSONA_NAV_LABELS[k]
        for k in nav_keys
    ]
    label_to_key = dict(zip(labels, nav_keys, strict=True))
    default_key = st.session_state["nav_key"]
    if default_key in custom_by_key:
        default_label = custom_label(custom_by_key[default_key])
    else:
        default_label = t(f"nav.{default_key}") if default_key in NAV_KEYS else PERSONA_NAV_LABELS[default_key]
    col_nav, col_add = st.columns([0.94, 0.06])
    with col_nav:
        secao_label = st.segmented_control(
            "nav",
            options=labels,
            default=default_label if default_label in labels else labels[0],
            key=f"nav_secao_{ctx.persona}_{lang}_{len(analyses)}",
            label_visibility="collapsed",
        )
    with col_add:
        if st.button("+", help="Adicionar análise customizada", key=f"add_analysis_{ctx.persona}"):
            st.session_state[f"show_custom_analysis_dialog_{ctx.persona}"] = True
    render_custom_analysis_dialog(ctx.persona)
    nav_key = label_to_key.get(secao_label or default_label, nav_keys[0])
    st.session_state["nav_key"] = nav_key
    st.space("small")
    safe_render("auditoria da base", expander_auditoria_base, ctx.df, ctx.cena_sel, ctx.ano_sel)
    if nav_key in custom_by_key:
        view_persona_tabs.render_custom_analysis(ctx.df, custom_by_key[nav_key], ctx.cena_sel, ctx.ano_sel)
    else:
        renderers[nav_key](ctx)
    st.caption(t("app.footer"))


def render_pagina(ctx: AppContext) -> None:
    render_cabecalho(ctx)
    render_analises(ctx)
