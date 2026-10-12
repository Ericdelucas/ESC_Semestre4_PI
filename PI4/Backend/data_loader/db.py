"""Conexao PostgreSQL (Supabase) via DATABASE_URL, com SSL e reconexao."""

from __future__ import annotations

import os
from pathlib import Path
from urllib.parse import parse_qsl, quote_plus, urlencode, urlparse, urlunparse

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

_BACKEND = Path(__file__).resolve().parents[1]
load_dotenv(_BACKEND / ".env")
load_dotenv(_BACKEND.parent / ".env")

_engine: Engine | None = None


def is_postgres_url(url: str | None) -> bool:
    raw = (url or "").strip().lower()
    return raw.startswith("postgres://") or raw.startswith("postgresql")


def database_url_raw() -> str:
    return (os.environ.get("DATABASE_URL") or os.environ.get("SUPABASE_DB_URL") or "").strip()


def postgres_disponivel() -> bool:
    return is_postgres_url(database_url_raw())


def normalize_database_url(raw: str) -> str:
    """psycopg2 + sslmode=require. Re-codifica a senha apos o parse."""
    url = (raw or "").strip()
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://") :]
    parsed = urlparse(url)
    user = quote_plus(parsed.username or "")
    password = quote_plus(parsed.password or "")
    host = parsed.hostname or ""
    port = f":{parsed.port}" if parsed.port else ""
    if user:
        netloc = f"{user}:{password}@{host}{port}"
    else:
        netloc = f"{host}{port}"
    query = dict(parse_qsl(parsed.query, keep_blank_values=True))
    query.setdefault("sslmode", "require")
    scheme = parsed.scheme or "postgresql"
    if scheme in {"postgresql", "postgres"}:
        scheme = "postgresql+psycopg2"
    elif scheme == "postgresql+psycopg" and "psycopg2" not in scheme:
        scheme = "postgresql+psycopg2"
    return urlunparse((scheme, netloc, parsed.path, parsed.params, urlencode(query), parsed.fragment))


def dispose_engine() -> None:
    global _engine
    if _engine is not None:
        try:
            _engine.dispose()
        except Exception as exc:  # noqa: BLE001
            print(f"[db] aviso ao libertar pool ({type(exc).__name__}: {exc})", flush=True)
        _engine = None


def get_cti_engine() -> Engine:
    """Pool pequeno, pre_ping e recycle — sobrevive a cortes do Supabase/Render."""
    global _engine
    if _engine is not None:
        return _engine
    raw = database_url_raw()
    if not is_postgres_url(raw):
        raise RuntimeError("DATABASE_URL PostgreSQL nao configurada")
    url = normalize_database_url(raw)
    print("[db] a criar engine PostgreSQL sslmode=require pool_pre_ping=1", flush=True)
    _engine = create_engine(
        url,
        future=True,
        pool_pre_ping=True,
        pool_recycle=300,
        pool_size=2,
        max_overflow=2,
        pool_timeout=30,
        connect_args={"sslmode": "require", "connect_timeout": 20},
    )
    return _engine
