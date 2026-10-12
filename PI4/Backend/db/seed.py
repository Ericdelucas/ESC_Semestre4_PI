"""Carga inicial da tabela usuarios."""

from __future__ import annotations

from .auth import seed_usuarios as _seed
from .database import init_db, session_scope


def seed_usuarios() -> None:
    init_db()
    with session_scope() as db:
        _seed(db)
