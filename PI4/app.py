"""
Painel financeiro CTI — orquestrador (< 100 linhas).

Execute:
  py -m streamlit run app.py
"""

from __future__ import annotations

import streamlit as st

from src.components.bootstrap import carregar_estado, montar_contexto, render_cabecalho
from src.components.headers import expander_auditoria_base
from src.components.resilience import safe_render
from src.components.sidebar import render_language_selector, render_persona, render_sidebar
from src.config import NAV_KEYS
from src.config.i18n import get_lang, t
from src.views import (
    capital_giro as view_capital_giro,
    comparar as view_comparar,
    como_ler as view_como_ler,
    distribuicao as view_distribuicao,
    faixa_risco as view_faixa_risco,
    mapeamento_risco as view_mapeamento_risco,
    prazos_ciclo as view_prazos_ciclo,
)

st.set_page_config(layout="wide", page_title="Dashboard CTI", page_icon="📊")

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
    render_cabecalho(ctx)

    lang = get_lang()
    if "nav_key" not in st.session_state:
        st.session_state["nav_key"] = NAV_KEYS[0]
    labels = [t(f"nav.{k}") for k in NAV_KEYS]
    label_to_key = dict(zip(labels, NAV_KEYS, strict=True))
    default_label = t(f"nav.{st.session_state['nav_key']}")
    secao_label = st.segmented_control(
        "nav",
        options=labels,
        default=default_label if default_label in labels else labels[0],
        key=f"nav_secao_{lang}",
        label_visibility="collapsed",
    )
    nav_key = label_to_key.get(secao_label or default_label, NAV_KEYS[0])
    st.session_state["nav_key"] = nav_key

    st.space("small")
    safe_render("auditoria da base", expander_auditoria_base, ctx.df, ctx.cena_sel, ctx.ano_sel)
    VIEW_RENDERERS[nav_key](ctx)
    st.caption(t("app.footer"))


main()
