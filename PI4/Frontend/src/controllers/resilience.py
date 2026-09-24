"""Isolamento de falhas na renderização Streamlit."""

from __future__ import annotations

import traceback
from collections.abc import Callable
from functools import wraps
from typing import Any, TypeVar

import streamlit as st

T = TypeVar("T")


def safe_render(label: str, fn: Callable[..., T], *args: Any, **kwargs: Any) -> T | None:
    """Executa um bloco de UI sem derrubar o restante do painel."""
    try:
        return fn(*args, **kwargs)
    except Exception as exc:  # noqa: BLE001 — isolamento deliberado por componente
        # Evita shortcodes :nome: do Markdown engolirem a mensagem
        detalhe = f"{type(exc).__name__}: {exc}".replace(":", "∶")
        st.error(f"Erro ao renderizar **{label}** — {detalhe}")
        with st.expander("Detalhe técnico (traceback)", expanded=True):
            st.code(traceback.format_exc())
        return None


def resilient_view(label: str) -> Callable[[Callable[..., T]], Callable[..., T | None]]:
    """Decorator para isolar falhas de uma aba inteira."""

    def decorator(fn: Callable[..., T]) -> Callable[..., T | None]:
        @wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> T | None:
            return safe_render(label, fn, *args, **kwargs)

        return wrapper

    return decorator
