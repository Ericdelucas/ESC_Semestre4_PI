"""Filtros laterais, idioma e seletor de persona."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from src.config import CSV_PATH, PERSONAS
from src.config.glossary import help_text
from src.config.i18n import LANG_OPTIONS, get_lang, set_lang, t
from src.controllers.auth import allowed_personas, can_access_persona
from src.models.formatting import cena_rotulo, cena_sort_key


def render_language_selector() -> str:
    """Seletor no topo da sidebar; persiste em ``st.session_state['lang']``."""
    set_lang(get_lang())
    labels = list(LANG_OPTIONS.values())
    codes = list(LANG_OPTIONS.keys())
    atual = get_lang()
    idx = codes.index(atual) if atual in codes else 0

    with st.sidebar:
        st.markdown(
            """
<div style="display:flex;align-items:center;gap:0.65rem;margin:0.15rem 0 0.9rem 0;">
  <div style="width:2.25rem;height:2.25rem;border-radius:999px;background:var(--primary-color);color:var(--background-color);display:flex;align-items:center;justify-content:center;font-weight:800;letter-spacing:0.02em;">ESC</div>
  <div style="font-weight:750;line-height:1.1;">Grupo ESC<br><span style="font-size:0.8rem;font-weight:500;opacity:0.75;">Dashboard CTI</span></div>
</div>
""",
            unsafe_allow_html=True,
        )
        escolha = st.selectbox(
            t("lang.label"),
            options=labels,
            index=idx,
            key=f"lang_select_label_{atual}",
        )
        novo = codes[labels.index(escolha)]
        if novo != atual:
            set_lang(novo)
            st.rerun()
    return get_lang()


ALL_FILTER_SENTINELS = frozenset({"__all__", "Todos", "All", "All Scenarios", None})


def _valores_unicos(frame: pd.DataFrame, coluna: str) -> list:
    if frame is None or frame.empty or coluna not in frame.columns:
        return []
    return [valor for valor in frame[coluna].dropna().tolist() if valor is not None and str(valor).strip() not in {"", "None", "nan"}]


def _eh_filtro_todos(valor: object) -> bool:
    return valor in ALL_FILTER_SENTINELS or str(valor).strip() in ALL_FILTER_SENTINELS


def _rotulo_ano(valor: object) -> str:
    return t("filter.all") if _eh_filtro_todos(valor) else str(valor)


def _rotulo_cena(valor: object) -> str:
    return t("filter.all_scenarios") if _eh_filtro_todos(valor) else cena_rotulo(str(valor))


def _sincronizar_filtro(widget_key: str, legado_key: str, opcoes: list, padrao: object) -> None:
    atual = st.session_state.get(widget_key, st.session_state.get(legado_key, padrao))
    if _eh_filtro_todos(atual):
        atual = padrao
    if atual not in opcoes:
        atual = padrao
    st.session_state[widget_key] = atual
    st.session_state[legado_key] = atual


def render_sidebar(df: pd.DataFrame, ind: pd.DataFrame, n_cenarios: int) -> tuple[str | int, str, list[int], list[str]]:
    lang = get_lang()
    with st.sidebar:
        st.header(t("sidebar.filters"))
        if "CENA" not in getattr(ind, "columns", []):
            st.warning(t("sidebar.missing_cena"))
        anos = sorted({int(float(a)) for a in _valores_unicos(ind, "ano_num") if pd.notna(a)})
        # Valor interno estável "__all__" — o rótulo segue o idioma sem perder o filtro
        ano_opts: list[str | int] = ["__all__", *anos]
        ano_key = f"filtro_ano_{lang}"
        _sincronizar_filtro(ano_key, "filtro_ano", ano_opts, "__all__")
        ano_choice = st.selectbox(
            t("sidebar.year"),
            options=ano_opts,
            format_func=_rotulo_ano,
            key=ano_key,
            help=help_text("sidebar_year"),
        )
        st.session_state["filtro_ano"] = ano_choice
        ano_sel: str | int = "Todos" if _eh_filtro_todos(ano_choice) else int(ano_choice)

        cenas_brutas = _valores_unicos(ind, "CENA")
        if not cenas_brutas:
            cenas_brutas = _valores_unicos(df, "CENA")
        cenas = sorted(cenas_brutas, key=cena_sort_key)
        if not cenas:
            st.warning(t("sidebar.no_scenarios"))
            cena_sel = "Todos"
        else:
            cena_opts = ["__all__", *cenas]
            cena_key = f"filtro_cena_{lang}"
            _sincronizar_filtro(cena_key, "filtro_cena", cena_opts, "__all__")
            cena_choice = st.selectbox(
                t("sidebar.scenario"),
                options=cena_opts,
                format_func=_rotulo_cena,
                key=cena_key,
                help=help_text("sidebar_scenario"),
            )
            st.session_state["filtro_cena"] = cena_choice
            cena_sel = "Todos" if _eh_filtro_todos(cena_choice) else str(cena_choice)

        st.markdown("---")
        active_base = st.session_state.get("cti_active_dataset_name", Path(CSV_PATH).name)
        n_anos = int(ind["ano_num"].nunique()) if isinstance(ind, pd.DataFrame) and "ano_num" in ind.columns else 0
        n_linhas = st.session_state.get("cti_row_count")
        if n_linhas is None:
            n_linhas = len(df) if isinstance(df, pd.DataFrame) else 0
        st.markdown(
            f"**{t('sidebar.base')}:** `{active_base}`  \n"
            f"**{t('sidebar.rows')}:** {int(n_linhas):,}  \n"
            f"**{t('sidebar.scenarios')}:** {n_cenarios:,}  \n"
            f"**{t('sidebar.years')}:** {n_anos}"
        )
    return ano_sel, cena_sel, anos, cenas


def render_persona() -> str:
    lang = get_lang()
    visoes = allowed_personas() or [p for p in PERSONAS if p != "teste"]
    labels = [t(f"persona.{p}") for p in visoes]
    label_to_id = dict(zip(labels, visoes, strict=True))
    legado = {"geral": "ceo", "docente": "concedente"}
    pending_persona = st.session_state.pop("pending_persona_id", None)
    if pending_persona in visoes and can_access_persona(pending_persona):
        st.session_state["persona_id"] = pending_persona
    atual = st.session_state.get("persona_id", visoes[0])
    if atual not in visoes:
        st.session_state["persona_id"] = legado.get(str(atual), visoes[0])
        if st.session_state["persona_id"] not in visoes:
            st.session_state["persona_id"] = visoes[0]
    default_label = t(f"persona.{st.session_state['persona_id']}")
    persona_widget_key = f"persona_visao_v3_{lang}_{'_'.join(visoes)}"
    if pending_persona in visoes:
        st.session_state.pop(persona_widget_key, None)
    with st.container(key="cti_persona_header"):
        escolha = st.segmented_control(
            t("persona.label"),
            options=labels,
            default=default_label if default_label in labels else labels[0],
            key=persona_widget_key,
            help=help_text("persona"),
        )
    persona_id = label_to_id.get(escolha or default_label, visoes[0])
    st.session_state["persona_id"] = persona_id
    return persona_id
