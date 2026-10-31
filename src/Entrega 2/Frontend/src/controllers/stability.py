"""Trocas rapidas de visao sem derrubar o websocket do Streamlit."""

from __future__ import annotations

import streamlit as st

from src.controllers.modals import close_chat, close_relatorio

PENDING_PROMPT_KEY = "cti_chat_pending_prompt"
_SIG_KEY = "_cti_view_sig"
_LIGHT_KEY = "_cti_light_switch"


def cancelar_assistente_em_curso() -> None:
    """Abandona a resposta a meio para a troca de ecran nao competir com a IA."""
    if st.session_state.pop(PENDING_PROMPT_KEY, None):
        from Backend.diag import log_ia

        log_ia("troca de ecran — pergunta pendente do assistente cancelada")


def troca_leve_ativa() -> bool:
    return bool(st.session_state.get(_LIGHT_KEY))


def preparar_troca_vista(persona: str, ano_sel: object, cena_sel: object) -> bool:
    """True no primeiro rerun depois de mudar persona/filtro — so mostra um placeholder."""
    sig = (str(persona), str(ano_sel), str(cena_sel))
    last = st.session_state.get(_SIG_KEY)
    if last is None:
        st.session_state[_SIG_KEY] = sig
        st.session_state[_LIGHT_KEY] = False
        return False
    if last == sig:
        st.session_state[_LIGHT_KEY] = False
        return False
    cancelar_assistente_em_curso()
    if last and last[0] != str(persona):
        close_chat()
    close_relatorio()
    st.session_state[_SIG_KEY] = sig
    st.session_state[_LIGHT_KEY] = True
    return True
