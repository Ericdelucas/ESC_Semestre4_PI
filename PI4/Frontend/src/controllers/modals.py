"""Estados independentes dos modais de Relatorio e Assistente IA."""

from __future__ import annotations

import inspect

import streamlit as st

MODAL_RELATORIO_KEY = "modal_relatorio_open"
CHAT_IA_KEY = "chat_ia_open"
_LEGACY_RELATORIO = "show_report_modal"
_LEGACY_CHAT = "chat_open"


def ensure_modal_state() -> None:
    if MODAL_RELATORIO_KEY not in st.session_state:
        st.session_state[MODAL_RELATORIO_KEY] = bool(st.session_state.get(_LEGACY_RELATORIO, False))
    if CHAT_IA_KEY not in st.session_state:
        st.session_state[CHAT_IA_KEY] = bool(st.session_state.get(_LEGACY_CHAT, False))
    st.session_state[_LEGACY_RELATORIO] = bool(st.session_state[MODAL_RELATORIO_KEY])
    st.session_state[_LEGACY_CHAT] = bool(st.session_state[CHAT_IA_KEY])


def is_relatorio_open() -> bool:
    return bool(st.session_state.get(MODAL_RELATORIO_KEY) or st.session_state.get(_LEGACY_RELATORIO))


def is_chat_open() -> bool:
    return bool(st.session_state.get(CHAT_IA_KEY) or st.session_state.get(_LEGACY_CHAT))


def _set_relatorio(open_: bool) -> None:
    st.session_state[MODAL_RELATORIO_KEY] = open_
    st.session_state[_LEGACY_RELATORIO] = open_


def _set_chat(open_: bool) -> None:
    st.session_state[CHAT_IA_KEY] = open_
    st.session_state[_LEGACY_CHAT] = open_


def open_relatorio() -> None:
    ensure_modal_state()
    _set_chat(False)
    _set_relatorio(True)


def close_relatorio() -> None:
    ensure_modal_state()
    _set_relatorio(False)


def open_chat() -> None:
    ensure_modal_state()
    _set_relatorio(False)
    _set_chat(True)


def close_chat() -> None:
    ensure_modal_state()
    _set_chat(False)


def dialog_kwargs(width: str = "large", on_dismiss=None) -> dict[str, object]:
    kwargs: dict[str, object] = {"width": width}
    try:
        params = inspect.signature(st.dialog).parameters
    except (TypeError, ValueError):
        return kwargs
    if on_dismiss is not None and "on_dismiss" in params:
        kwargs["on_dismiss"] = on_dismiss
    return kwargs
