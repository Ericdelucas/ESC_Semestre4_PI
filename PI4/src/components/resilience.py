"""Isolamento de falhas na renderização Streamlit."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, TypeVar

import streamlit as st

T = TypeVar("T")


def safe_render(label: str, fn: Callable[..., T], *args: Any, **kwargs: Any) -> T | None:
    """Executa um bloco de UI sem derrubar o restante do painel."""
    try:
        return fn(*args, **kwargs)
    except Exception as exc:  # noqa: BLE001 — isolamento deliberado por componente
        st.error(f"Não foi possível carregar **{label}** no momento.")
        with st.expander("Detalhe técnico", expanded=False):
            st.code(f"{type(exc).__name__}: {exc}")
        return None
