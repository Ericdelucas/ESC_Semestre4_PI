"""
Painel financeiro CTI — orquestrador (< 100 linhas).

Execute:
  py -m streamlit run app.py
"""

from __future__ import annotations

import streamlit as st

from src.components.bootstrap import carregar_estado, montar_contexto
from src.components.kpis import kpis_por_persona, render_kpi_row
from src.data.formatting import texto_ncg, texto_tesouraria, texto_ciclo
from src.components.headers import expander_auditoria_base
from src.components.resilience import safe_render
from src.components.sidebar import render_language_selector, render_sidebar
from src.config import NAV_KEYS
from src.config.i18n import get_lang, t
from src.views import (
    ai_assistant as view_ai_assistant,
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
    "assistente": lambda ctx: view_ai_assistant.render(
        ctx.ranking, ctx.n_cenarios, ctx.p_ruina, ctx.cena_sel, ctx.k, ctx.ano_enc
    ),
    "como_ler": lambda ctx: view_como_ler.render(ctx.n_cenarios, ctx.cena_sel, ctx.k, ctx.ano_enc, ctx.p_ruina),
}


def main() -> None:
    st.html("""
        <style>
        [data-testid="stAppDeployButton"], .stAppDeployButton {
            display: none !important;
        }
        /* Bring the role selector closer to the top, below the app toolbar. */
        [data-testid="stMainBlockContainer"] {
            padding-top: 3.5rem;
        }
        </style>
    """)
    render_language_selector()
    estado = carregar_estado()
    if estado is None:
        st.stop()
    df, ind, ranking = estado

    ano_sel, cena_sel, anos, cenas = render_sidebar(df, ind, int(ranking["CENA"].nunique()))
    # Keep existing profile IDs so the indicators and pages retain their behavior.
    profile_labels = dict(zip(
        ("geral", "cfo", "acionistas", "concedente"),
        ("CEO", "CFO & Creditors", "Shareholders", "Granting Authority")
        if get_lang() == "en" else
        ("CEO", "CFO & Credores", "Acionistas", "Poder concedente"),
    ))
    current_profile = st.session_state.get("persona_id", "geral")
    if current_profile not in profile_labels:
        current_profile = "cfo" if current_profile == "credores" else "geral"
    selected_profile = st.segmented_control(
        "Role / profile" if get_lang() == "en" else "Cargo / perfil",
        options=list(profile_labels), format_func=profile_labels.get,
        default=current_profile, key="profiles_ceo_cfo",
        help="CEO: executive overview; CFO & Creditors: solvency; Shareholders: returns; Granting Authority: continuity."
        if get_lang() == "en" else
        "CEO: visao geral; CFO & Credores: solvencia; Acionistas: retorno; Poder concedente: continuidade.",
    )
    persona = selected_profile or current_profile
    st.session_state["persona_id"] = persona
    ctx = montar_contexto(
        df, ind, ranking, ano_sel=ano_sel, cena_sel=cena_sel, anos=anos, cenas=cenas, persona=persona
    )
    # Cabecalho temporariamente desativado. Para reativar, descomente o bloco
    # e os imports de render_titulo e banner_auditoria_filtro abaixo.
    # from src.components.headers import render_titulo, banner_auditoria_filtro
    # from src.data.formatting import cena_rotulo
    # render_titulo()
    # st.subheader(t("header.focus", cena=cena_rotulo(ctx.cena_sel)))
    # safe_render("banner de auditoria", banner_auditoria_filtro, ctx.cena_sel, ctx.ano_sel)
    # st.write(
    #     t("header.avg_all")
    #     if ctx.ano_sel == "Todos"
    #     else t("header.avg_year", ano=ctx.ano_sel)
    # )

    render_kpi_row(kpis_por_persona(ctx.persona, ctx.k, ctx.ranking))
    if ctx.persona == "geral":
        st.info(texto_ncg(ctx.k["NCG"]))
        a, b = st.columns(2)
        a.success(texto_tesouraria(ctx.k["Saldo_Tesouraria"]))
        b.warning(texto_ciclo(ctx.k["Ciclo_Financeiro"]))
    else:
        st.info(t(f"persona.blurb.{ctx.persona}"))

    lang = get_lang()
    nav_keys = NAV_KEYS
    if st.session_state.get("nav_key") not in nav_keys:
        st.session_state["nav_key"] = nav_keys[0]
    labels = [t(f"nav.{k}") for k in nav_keys]
    label_to_key = dict(zip(labels, nav_keys, strict=True))
    default_label = t(f"nav.{st.session_state['nav_key']}")
    secao_label = st.segmented_control(
        "nav",
        options=labels,
        default=default_label if default_label in labels else labels[0],
        key=f"nav_original_{lang}",
        label_visibility="collapsed",
    )
    nav_key = label_to_key.get(secao_label or default_label, nav_keys[0])
    if nav_key not in nav_keys:
        nav_key = nav_keys[0]
    st.session_state["nav_key"] = nav_key

    st.space("small")
    safe_render("audit", expander_auditoria_base, ctx.df, ctx.cena_sel, ctx.ano_sel)
    VIEW_RENDERERS[nav_key](ctx)
    st.caption(t("app.footer"))


main()
