"""Engine SQLAlchemy (SQLite por padrao, PostgreSQL via DATABASE_URL)."""

from __future__ import annotations

import os
from contextlib import contextmanager
from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from urllib.parse import urlparse

from Backend.data_loader.db import USAR_SUPABASE, ipv4_de, is_postgres_url, preferred_database_url
from Backend.diag import diag, mascarar_url

_BACKEND = Path(__file__).resolve().parents[1]
_DEFAULT_SQLITE = _BACKEND / "cache" / "cti_auth.db"

Base = declarative_base()
_engine = None
_SessionLocal = None

def database_url() -> str:
    return (os.environ.get("DATABASE_URL") or f"sqlite:///{_DEFAULT_SQLITE.as_posix()}").strip().strip("\"'")


def _sqlite_url() -> str:
    return f"sqlite:///{_DEFAULT_SQLITE.as_posix()}"


def _bind_engine(url: str, *, postgres: bool) -> None:
    global _engine, _SessionLocal
    if postgres:
        host = urlparse(url).hostname or ""
        ipv4 = ipv4_de(host)
        args: dict[str, object] = {"sslmode": "require", "connect_timeout": 12}
        if ipv4:
            args["hostaddr"] = ipv4
            diag("auth", f"Postgres IPv4 host={host} hostaddr={ipv4}")
        else:
            diag("auth", f"Postgres sem IPv4 host={host} — a Render pode falhar em IPv6")
        _engine = create_engine(
            url,
            future=True,
            pool_pre_ping=True,
            pool_recycle=300,
            pool_size=3,
            max_overflow=2,
            pool_timeout=30,
            connect_args=args,
        )
    else:
        _engine = create_engine(
            url,
            future=True,
            connect_args={"check_same_thread": False},
        )
    _SessionLocal = sessionmaker(
        bind=_engine,
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
        future=True,
    )


def _usar_sqlite(motivo: str) -> None:
    global _engine, _SessionLocal
    diag("auth", f"aviso: a usar SQLite ({motivo})")
    if _engine is not None:
        try:
            _engine.dispose()
        except Exception as exc:  # noqa: BLE001
            print(f"[auth] aviso dispose ({type(exc).__name__}: {exc})", flush=True)
    _engine = None
    _SessionLocal = None
    _DEFAULT_SQLITE.parent.mkdir(parents=True, exist_ok=True)
    _bind_engine(_sqlite_url(), postgres=False)


def get_engine():
    global _engine, _SessionLocal
    if _engine is None:
        _DEFAULT_SQLITE.parent.mkdir(parents=True, exist_ok=True)
        url = database_url()
        if USAR_SUPABASE and is_postgres_url(url):
            resolvida = preferred_database_url()
            if resolvida:
                diag("auth", f"PostgreSQL {mascarar_url(resolvida)}")
                _bind_engine(resolvida, postgres=True)
            else:
                _usar_sqlite("DATABASE_URL sem DNS resolvivel")
        else:
            diag("auth", "SQLite local (Supabase desligado)")
            _bind_engine(_sqlite_url(), postgres=False)
    return _engine


def _ensure_sqlite_columns(engine) -> None:
    if engine.dialect.name != "sqlite":
        return
    with engine.begin() as conn:
        colunas = {row[1] for row in conn.execute(text("PRAGMA table_info(usuarios)"))}
        if colunas and "is_super_admin" not in colunas:
            conn.execute(text("ALTER TABLE usuarios ADD COLUMN is_super_admin BOOLEAN NOT NULL DEFAULT 0"))


def init_db() -> None:
    """Cria tabelas. Se o Postgres falhar (DNS), cai para SQLite e a API sobe."""
    from . import models as _models  # noqa: F401

    try:
        engine = get_engine()
        Base.metadata.create_all(bind=engine)
        _ensure_sqlite_columns(engine)
        diag("auth", f"init_db OK dialect={engine.dialect.name}")
    except Exception as exc:  # noqa: BLE001
        diag("auth", f"aviso: Postgres falhou no init ({type(exc).__name__}: {exc})")
        _usar_sqlite(str(exc))
        engine = get_engine()
        Base.metadata.create_all(bind=engine)
        _ensure_sqlite_columns(engine)
        diag("auth", "init_db OK dialect=sqlite (fallback)")


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
