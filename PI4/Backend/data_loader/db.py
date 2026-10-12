"""Conexao PostgreSQL (Supabase) via DATABASE_URL, com SSL e reconexao."""

from __future__ import annotations

import os
import socket
from pathlib import Path
from urllib.parse import parse_qsl, quote_plus, urlencode, urlparse, urlunparse

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

_BACKEND = Path(__file__).resolve().parents[1]
load_dotenv(_BACKEND / ".env")
load_dotenv(_BACKEND.parent / ".env")

_engine: Engine | None = None
_sql_ok = False
_sql_aviso: str | None = None
_dns_esgotado = False

# Host directo antigo (sem o 'r') nao resolve — o projecto correcto tem ...rnruspj...
_HOST_FIXES = {
    "db.rvpfnqaiwqzwhrnuspj.supabase.co": "db.rvpfnqaiwqzwhrnruspj.supabase.co",
}
_POOLER_REGIONS = ("sa-east-1", "us-east-1", "us-east-2", "eu-west-1")


def _limpar_url(valor: str | None) -> str:
    return (valor or "").strip().strip("\"'").replace("\n", "").replace("\r", "").replace("\t", "").strip()


def is_postgres_url(url: str | None) -> bool:
    raw = _limpar_url(url).lower()
    return raw.startswith("postgres://") or raw.startswith("postgresql")


def database_url_raw() -> str:
    for chave in ("DATABASE_URL", "SUPABASE_DB_URL", "DATABASE_URL_POOLER", "SUPABASE_POOLER_URL"):
        valor = _limpar_url(os.environ.get(chave))
        if is_postgres_url(valor):
            return valor
    return ""


def postgres_disponivel() -> bool:
    return is_postgres_url(database_url_raw())


def sql_conectado() -> bool:
    return _sql_ok


def sql_aviso() -> str | None:
    return _sql_aviso


def _corrigir_host(host: str) -> str:
    return _HOST_FIXES.get((host or "").lower(), host)


def _project_ref(host: str) -> str:
    nome = (host or "").lower()
    if nome.startswith("db.") and nome.endswith(".supabase.co"):
        return _corrigir_host(nome)[3 : -len(".supabase.co")]
    if ".pooler.supabase.co" in nome:
        return ""
    return ""


def _host_resolves(host: str) -> bool:
    if not host:
        return False
    try:
        socket.getaddrinfo(host, None)
        return True
    except socket.gaierror as exc:
        print(f"[db] DNS falhou host={host} ({exc})", flush=True)
        return False


def normalize_database_url(raw: str, *, host: str | None = None, port: int | None = None, user: str | None = None) -> str:
    """psycopg2 + sslmode=require. Re-codifica a senha apos o parse."""
    url = _limpar_url(raw)
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://") :]
    parsed = urlparse(url)
    username = quote_plus(user if user is not None else (parsed.username or ""))
    password = quote_plus(parsed.password or "")
    hostname = _corrigir_host(host or parsed.hostname or "")
    porta = port if port is not None else parsed.port
    port_txt = f":{porta}" if porta else ""
    if username:
        netloc = f"{username}:{password}@{hostname}{port_txt}"
    else:
        netloc = f"{hostname}{port_txt}"
    query = dict(parse_qsl(parsed.query, keep_blank_values=True))
    query.setdefault("sslmode", "require")
    scheme = parsed.scheme or "postgresql"
    if scheme in {"postgresql", "postgres"}:
        scheme = "postgresql+psycopg2"
    elif scheme == "postgresql+psycopg":
        scheme = "postgresql+psycopg2"
    return urlunparse((scheme, netloc, parsed.path or "/postgres", parsed.params, urlencode(query), parsed.fragment))


def _urls_ambiente() -> list[str]:
    vistos: set[str] = set()
    saida: list[str] = []
    for chave in ("DATABASE_URL", "SUPABASE_DB_URL", "DATABASE_URL_POOLER", "SUPABASE_POOLER_URL"):
        valor = _limpar_url(os.environ.get(chave))
        if not is_postgres_url(valor):
            continue
        variante = normalize_database_url(valor)
        if variante not in vistos:
            vistos.add(variante)
            saida.append(variante)
    return saida


def candidate_urls() -> list[str]:
    """Directo (host corrigido) e, se o DNS falhar, pooler :6543 do Supabase."""
    vistos: set[str] = set()
    saida: list[str] = []

    def add(url: str) -> None:
        if url and url not in vistos:
            vistos.add(url)
            saida.append(url)

    for bruto in _urls_ambiente():
        add(normalize_database_url(bruto))

    base = next((u for u in _urls_ambiente()), "")
    if not base:
        return saida

    parsed = urlparse(base if "://" in base else f"postgresql://{base}")
    host = _corrigir_host(parsed.hostname or "")
    ref = _project_ref(host)
    user = parsed.username or "postgres"
    regioes: list[str] = []
    extra = _limpar_url(os.environ.get("SUPABASE_REGION"))
    if extra:
        regioes.append(extra)
    regioes.extend(_POOLER_REGIONS)

    if ref:
        add(normalize_database_url(base, host=f"db.{ref}.supabase.co", port=5432, user=user.split(".")[0]))
        pooler_user = user if "." in user else f"{user}.{ref}"
        for regio in regioes:
            add(normalize_database_url(base, host=f"aws-0-{regio}.pooler.supabase.co", port=6543, user=pooler_user))
    return saida


def preferred_database_url() -> str:
    """Primeira URL cujo host resolve em DNS. Vazio se nenhum resolver."""
    for url in candidate_urls():
        host = urlparse(url).hostname or ""
        if _host_resolves(host):
            return url
    print("[db] aviso: nenhum host PostgreSQL resolveu DNS", flush=True)
    return ""


def dispose_engine() -> None:
    global _engine
    if _engine is not None:
        try:
            _engine.dispose()
        except Exception as exc:  # noqa: BLE001
            print(f"[db] aviso ao libertar pool ({type(exc).__name__}: {exc})", flush=True)
        _engine = None


def _criar_engine(url: str) -> Engine:
    return create_engine(
        url,
        future=True,
        pool_pre_ping=True,
        pool_recycle=300,
        pool_size=2,
        max_overflow=2,
        pool_timeout=30,
        connect_args={"sslmode": "require", "connect_timeout": 12},
    )


def get_cti_engine() -> Engine:
    """Tenta host directo; se o DNS falhar, usa o pooler. Marca aviso sem derrubar a app."""
    global _engine, _sql_ok, _sql_aviso, _dns_esgotado
    if _engine is not None:
        return _engine
    if _dns_esgotado:
        raise RuntimeError(_sql_aviso or "nenhum host PostgreSQL resolvivel (DNS)")
    ultimo: Exception | None = None
    for url in candidate_urls():
        host = urlparse(url).hostname or ""
        porta = urlparse(url).port
        if not _host_resolves(host):
            continue
        print(f"[db] a criar engine host={host} port={porta} sslmode=require", flush=True)
        engine = _criar_engine(url)
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            _engine = engine
            _sql_ok = True
            _sql_aviso = None
            print(f"[db] PostgreSQL OK host={host}", flush=True)
            return engine
        except Exception as exc:  # noqa: BLE001
            ultimo = exc
            print(f"[db] ligacao falhou host={host} {type(exc).__name__}: {exc}", flush=True)
            try:
                engine.dispose()
            except Exception:
                pass
    _sql_ok = False
    _sql_aviso = (
        f"{type(ultimo).__name__}: {ultimo}" if ultimo else "nenhum host PostgreSQL resolvivel (DNS)"
    )
    _dns_esgotado = "translate host" in _sql_aviso.lower() or "name or service not known" in _sql_aviso.lower() or ultimo is None
    print(f"[db] aviso: Supabase indisponivel — {_sql_aviso}", flush=True)
    raise RuntimeError(_sql_aviso)
