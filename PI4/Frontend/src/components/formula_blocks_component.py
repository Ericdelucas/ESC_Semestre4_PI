"""Construtor visual de formulas por blocos (st.components.v2: sem iframe nem build npm)."""
from __future__ import annotations

from pathlib import Path
from typing import Callable

import streamlit as st

_ASSETS = Path(__file__).with_name("formula_blocks")
_CSS = (_ASSETS / "blocks.css").read_text(encoding="utf-8")
_JS = (_ASSETS / "blocks.js").read_text(encoding="utf-8")


def edited_formula(key: str) -> dict | None:
    """Ultima edicao enviada pelo JS: {'expression', 'blocks', 'rev'}."""
    state = st.session_state.get(key)
    return state.get("formula") if isinstance(state, dict) else None


def formula_blocks_editor(*, key: str, palette: list[dict], blocks: list[dict] | None,
                          expression: str, on_change: Callable[[], None],
                          status: dict | None = None, sync_error: str | None = None,
                          disabled: bool = False):
    """Monta o editor. blocks=None mantem os blocos atuais (texto sem equivalente)."""
    # O registo vive no Runtime (um novo por AppTest); repetir a mesma definicao e idempotente.
    component = st.components.v2.component("formula_blocks", css=_CSS, js=_JS)
    return component(
        key=key,
        data={"palette": palette, "blocks": blocks, "expression": expression,
              "status": status, "sync_error": sync_error, "disabled": disabled},
        default={"formula": None},
        on_formula_change=on_change,
    )
