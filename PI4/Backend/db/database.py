"""Engine SQLAlchemy (SQLite por padrao, PostgreSQL via DATABASE_URL)."""

from __future__ import annotations

import os
from contextlib import contextmanager
from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, declarative_base, sessionmaker

_BACKEND = Path(__file__).resolve().parents[1]
_DEFAULT_SQLITE = _BACKEND / "cache" / "cti_auth.db"

Base = declarative_base()
_engine = None
_SessionLocal = None


def database_url() -> str:
    return os.environ.get("DATABASE_URL", f"sqlite:///{_DEFAULT_SQLITE.as_posix()}")


def get_engine():
    global _engine, _SessionLocal
    if _engine is None:
        _DEFAULT_SQLITE.parent.mkdir(parents=True, exist_ok=True)
        url = database_url()
        connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
        _engine = create_engine(url, future=True, connect_args=connect_args)
        _SessionLocal = sessionmaker(
            bind=_engine,
            autoflush=False,
            autocommit=False,
            expire_on_commit=False,
            future=True,
        )
    return _engine


def _ensure_sqlite_columns(engine) -> None:
    if engine.dialect.name != "sqlite":
        return
    with engine.begin() as conn:
        colunas = {row[1] for row in conn.execute(text("PRAGMA table_info(usuarios)"))}
        if colunas and "is_super_admin" not in colunas:
            conn.execute(text("ALTER TABLE usuarios ADD COLUMN is_super_admin BOOLEAN NOT NULL DEFAULT 0"))


def init_db() -> None:
    from . import models as _models  # noqa: F401

    engine = get_engine()
    Base.metadata.create_all(bind=engine)
    _ensure_sqlite_columns(engine)


def get_db() -> Session:
    get_engine()
    assert _SessionLocal is not None
    return _SessionLocal()


@contextmanager
def session_scope():
    session = get_db()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
