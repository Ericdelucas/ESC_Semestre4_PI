"""Renderizacao do painel de chat do Assistente CTI."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from src.config.i18n import get_lang
from src.controllers.resilience import resilient_view

from .context import _carregar_engine, _chave_api, _contexto_foco, _fingerprint

_BOAS_VINDAS = "Olá! Sou o consultor virtual da CTI. Como posso ajudar com os cenários hoje?"


def _inicializar_historico() -> None:
    if "chat_history" in st.session_state and isinstance(st.session_state.chat_history, list):
        return
    legado = st.session_state.get("ai_chat_history")
    st.session_state.chat_history = legado if isinstance(legado, list) and legado else [
        {"role": "assistant", "content": _BOAS_VINDAS}
    ]


def _render_mensagens() -> None:
    chat_container = st.container(height=450, border=True)
    with chat_container:
        for msg in st.session_state.chat_history:
            papel = msg.get("role", "assistant")
            if papel not in {"user", "assistant"}:
                papel = "assistant"
            with st.chat_message(papel):
                st.write(msg.get("content", ""))


def _render_formulario() -> tuple[bool, str]:
    with st.form("cti_chat_form", clear_on_submit=True, border=False):
        prompt = st.text_area("Mensagem", placeholder="Pergunte ao Assistente CTI...", label_visibility="collapsed", height=90)
        enviar = st.form_submit_button("Enviar", type="primary", width="stretch")
    return enviar, str(prompt or "").strip()


def render_chat_panel(
    ranking: pd.DataFrame,
    n_cenarios: int,
    p_ruina: float,
    cena_sel: str,
    k: pd.Series,
    ano_enc: int,
    ano_sel: str | int = "Todos",
) -> None:
    col_title, col_close = st.columns([4, 1])
    with col_title:
        st.subheader("🤖 Assistente CTI")
    with col_close:
        if st.button("✖", key="close_chat_btn"):
            st.session_state.show_chat = False
            st.rerun()

    with st.expander("⚙️ Configurações da API & Dados", expanded=False):
        st.text_input("Chave API Gemini", type="password", key="gemini_api_key_input")
        if st.button("Limpar Conversa"):
            st.session_state.chat_history = []
            st.rerun()

    _inicializar_historico()
    _render_mensagens()
    enviar, texto = _render_formulario()
    if not enviar or not texto:
        return

    st.session_state.chat_history.append({"role": "user", "content": texto})
    try:
        engine = _carregar_engine(ranking, _fingerprint(ranking))
        with st.spinner("Consultando cenários e manuais…"):
            resposta, fontes = engine.ask(
                texto,
                lang=get_lang(),
                history=st.session_state.chat_history[:-1],
                api_key=_chave_api(),
                extra_context=_contexto_foco(ranking, n_cenarios, p_ruina, cena_sel, k, ano_enc, ano_sel),
                cena_sel=cena_sel,
            )
        if fontes:
            resposta = f"{resposta}\n\nFontes: {' · '.join(fontes[:8])}"
    except Exception as exc:
        resposta = f"Não consegui responder agora: {exc}"
    st.session_state.chat_history.append({"role": "assistant", "content": resposta})
    st.session_state.ai_chat_history = st.session_state.chat_history
    st.rerun()


def render_chat(
    ranking: pd.DataFrame,
    n_cenarios: int,
    p_ruina: float,
    cena_sel: str,
    k: pd.Series,
    ano_enc: int,
    ano_sel: str | int = "Todos",
    *,
    compact: bool = False,
) -> None:
    _ = compact
    render_chat_panel(ranking, n_cenarios, p_ruina, cena_sel, k, ano_enc, ano_sel)


@resilient_view("aba Assistente de IA CTI")
def render(
    ranking: pd.DataFrame,
    n_cenarios: int,
    p_ruina: float,
    cena_sel: str,
    k: pd.Series,
    ano_enc: int,
    ano_sel: str | int = "Todos",
) -> None:
    render_chat_panel(ranking, n_cenarios, p_ruina, cena_sel, k, ano_enc, ano_sel)
