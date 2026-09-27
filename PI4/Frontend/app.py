"""Orquestrador do dashboard (< 100 linhas)."""

from __future__ import annotations

import streamlit as st

from chat_component import render_floating_chat
from src.config import NAV_KEYS
from src.config.i18n import get_lang, t
from src.controllers.bootstrap import AppContext, carregar_estado, montar_contexto, render_cabecalho
from src.controllers.headers import expander_auditoria_base
from src.controllers.resilience import safe_render
from src.controllers.sidebar import render_language_selector, render_persona, render_sidebar
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

st.set_page_config(layout="wide", page_title="Dashboard CTI", page_icon="📊")

# Contraste dos KPIs no Dark Mode (st.metric herda textColor do tema).
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

# Chaves estáveis — rótulos vêm do i18n (troca de idioma não perde a seção).
VIEW_RENDERERS = {
    "capital_giro": lambda ctx: view_capital_giro.render(ctx.foco, ctx.foco_ano, ctx.cena_sel, ctx.ano_sel),
    "prazos": lambda ctx: view_prazos_ciclo.render(ctx.foco, ctx.k, ctx.cena_sel, ctx.ano_sel),
    "mapeamento": lambda ctx: view_mapeamento_risco.render(
        ctx.ranking, ctx.persona, ctx.cenas, ctx.mapa_rotulo, ctx.n_cenarios
    ),
    "distribuicao": lambda ctx: view_distribuicao.render(
        ctx.ranking, ctx.ano_enc, ctx.n_cenarios, ctx.p_ruina
    ),
    "faixa": lambda ctx: view_faixa_risco.render(ctx.ind, ctx.cena_sel, ctx.ano_sel, ctx.anos),
    "comparar": lambda ctx: view_comparar.render(ctx.ind, ctx.cenas, ctx.cena_sel, ctx.ano_sel),
    "como_ler": lambda ctx: view_como_ler.render(
        ctx.n_cenarios, ctx.cena_sel, ctx.k, ctx.ano_enc, ctx.p_ruina
    ),
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
    lang = get_lang()
    nav_keys = PERSONA_NAV_KEYS.get(ctx.persona, NAV_KEYS)
    renderers = {**VIEW_RENDERERS, "comparar": PERSONA_VIEW_RENDERERS["comparar"]} if ctx.persona == "cfo" else PERSONA_VIEW_RENDERERS
    if st.session_state.get("nav_key") not in nav_keys:
        st.session_state["nav_key"] = nav_keys[0]
    labels = [t(f"nav.{k}") if k in NAV_KEYS else PERSONA_NAV_LABELS[k] for k in nav_keys]
    label_to_key = dict(zip(labels, nav_keys, strict=True))
    default_key = st.session_state["nav_key"]
    default_label = t(f"nav.{default_key}") if default_key in NAV_KEYS else PERSONA_NAV_LABELS[default_key]
    secao_label = st.segmented_control(
        "nav",
        options=labels,
        default=default_label if default_label in labels else labels[0],
        key=f"nav_secao_{ctx.persona}_{lang}",
        label_visibility="collapsed",
    )
    nav_key = label_to_key.get(secao_label or default_label, nav_keys[0])
    st.session_state["nav_key"] = nav_key
    st.space("small")
    safe_render("auditoria da base", expander_auditoria_base, ctx.df, ctx.cena_sel, ctx.ano_sel)
    renderers[nav_key](ctx)
    st.caption(t("app.footer"))


def render_pagina(ctx: AppContext) -> None:
    render_cabecalho(ctx)
    render_analises(ctx)


def main() -> None:
    render_language_selector()
    estado = carregar_estado()
    if estado is None:
        st.stop()
    df, ind, ranking = estado

    ano_sel, cena_sel, anos, cenas = render_sidebar(df, ind, int(ranking["CENA"].nunique()))
    persona = render_persona()
    ctx = montar_contexto(
        df, ind, ranking, ano_sel=ano_sel, cena_sel=cena_sel, anos=anos, cenas=cenas, persona=persona
    )
    render_pagina(ctx)
    render_floating_chat()


main()
