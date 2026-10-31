"""Compatibilidade publica da view do Assistente CTI."""

from __future__ import annotations

from typing import Any

__all__ = ["render", "render_chat", "render_chat_panel", "render_floating_chat"]


def render_floating_chat(*args: Any, **kwargs: Any) -> Any:
    from .panel import render_floating_chat as _render_floating_chat

    return _render_floating_chat(*args, **kwargs)


def render_chat_panel(*args: Any, **kwargs: Any) -> Any:
    from .panel import render_chat_panel as _render_chat_panel

    return _render_chat_panel(*args, **kwargs)


def render_chat(*args: Any, **kwargs: Any) -> Any:
    from .panel import render_chat as _render_chat

    return _render_chat(*args, **kwargs)


def render(*args: Any, **kwargs: Any) -> Any:
    from .panel import render as _render

    return _render(*args, **kwargs)
