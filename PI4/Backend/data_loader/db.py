"""Conexao PostgreSQL (Supabase) via DATABASE_URL, com SSL, IPv4 e reconexao."""

from __future__ import annotations

import os
import socket
from pathlib import Path
from urllib.parse import parse_qsl, quote_plus, urlencode, urlparse, urlunparse

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from Backend.diag import diag, log_ambiente, mascarar_url

_BACKEND = Path(__file__).resolve().parents[1]
load_dotenv(_BACKEND / ".env")
load_dotenv(_BACKEND.parent / ".env")

_engine: Engine | None = None
_sql_ok = False
_sql_aviso: str | None = None
_dns_esgotado = False
_candidatos_cache: list[str] | None = None

# Host directo antigo (sem o 'r') nao resolve — o projecto correcto tem ...rnruspj...
_HOST_FIXES = {
    "db.rvpfnqaiwqzwhrnuspj.supabase.co": "db.rvpfnqaiwqzwhrnruspj.supabase.co",
}
_ENV_POOLER = ("DATABASE_URL_POOLER", "SUPABASE_POOLER_URL")
_ENV_DIRECT = ("DATABASE_URL", "SUPABASE_DB_URL")
_dns_cache: dict[tuple[str, int], list[str]] = {}


def _limpar_url(valor: str | None) -> str:
    return (valor or "").strip().strip("\"'").replace("\n", "").replace("\r", "").replace("\t", "").strip()


def is_postgres_url(url: str | None) -> bool:
    raw = _limpar_url(url).lower()
    return raw.startswith("postgres://") or raw.startswith("postgresql")


def database_url_raw() -> str:
    for chave in (*_ENV_POOLER, *_ENV_DIRECT):
        valor = _limpar_url(os.environ.get(chave))
        if is_postgres_url(valor):
            diag("db", f"database_url_raw escolheu {chave}")
            return valor
    return ""


def postgres_disponivel() -> bool:
    return is_postgres_url(database_url_raw())


def postgres_ipv4_disponivel() -> bool:
    """True so se alguma URL configurada (pooler ou directa) tiver A/IPv4."""
    for url in candidate_urls():
        host = urlparse(url).hostname or ""
        if ipv4_de(host):
            return True
    diag("db", "nenhuma URL configurada tem IPv4 — a saltar Postgres")
    return False


def sql_conectado() -> bool:
    return _sql_ok


def sql_aviso() -> str | None:
    return _sql_aviso


def _corrigir_host(host: str) -> str:
    corrigido = _HOST_FIXES.get((host or "").lower(), host)
    if corrigido != host:
        diag("db", f"host corrigido {host} -> {corrigido}")
    return corrigido


def _project_ref(host: str) -> str:
    nome = (host or "").lower()
    if nome.startswith("db.") and nome.endswith(".supabase.co"):
        return _corrigir_host(nome)[3 : -len(".supabase.co")]
    return ""


def _listar_ips(host: str, family: int) -> list[str]:
    chave = (host, family)
    if chave in _dns_cache:
        return _dns_cache[chave]
    try:
        ips = sorted({item[4][0] for item in socket.getaddrinfo(host, None, family, socket.SOCK_STREAM)})
    except socket.gaierror:
        ips = []
    _dns_cache[chave] = ips
    return ips


def log_dns(host: str) -> None:
    ipv4 = _listar_ips(host, socket.AF_INET)
    ipv6 = _listar_ips(host, socket.AF_INET6)
    diag("db", f"DNS host={host} IPv4={ipv4 or 'NENHUM'} IPv6={ipv6 or 'NENHUM'}")


def ipv4_de(host: str) -> str | None:
    if not host:
        return None
    ips = _listar_ips(host, socket.AF_INET)
    if ips:
        diag("db", f"IPv4 escolhido host={host} ip={ips[0]}")
        return ips[0]
    log_dns(host)
    return None


def _host_resolves(host: str) -> bool:
    if not host:
        return False
    if _listar_ips(host, socket.AF_INET):
        return True
    if _listar_ips(host, socket.AF_INET6):
        diag("db", f"host={host} so tem IPv6 — a Render nao liga")
        return True
    diag("db", f"DNS falhou host={host}")
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
    for chave in (*_ENV_POOLER, *_ENV_DIRECT):
        valor = _limpar_url(os.environ.get(chave))
        if not is_postgres_url(valor):
            continue
        variante = normalize_database_url(valor)
        if variante not in vistos:
            vistos.add(variante)
            saida.append(variante)
            parsed = urlparse(variante)
            diag(
                "db",
                f"candidato env {chave} host={parsed.hostname} port={parsed.port} "
                f"user={parsed.username} url={mascarar_url(variante)}",
            )
    return saida


def candidate_urls() -> list[str]:
    """So URLs do ambiente. Nao adivinhar dezenas de poolers (isso causava 429)."""
    global _candidatos_cache
    if _candidatos_cache is not None:
        return _candidatos_cache
    saida = _urls_ambiente()
    diag("db", f"total candidatos={len(saida)} (apenas env, sem varredura DNS)")
    _candidatos_cache = saida
    return saida


def preferred_database_url() -> str:
    """Primeira URL com IPv4. Host so-IPv6 e inutil na Render."""
    for url in candidate_urls():
        host = urlparse(url).hostname or ""
        if not _host_resolves(host):
            continue
        if ipv4_de(host):
            diag("db", f"preferred host={host} (IPv4)")
            return url
        diag("db", f"a ignorar host so-IPv6 {host}")
    diag("db", "aviso: nenhum host PostgreSQL com IPv4")
    return ""


def dispose_engine() -> None:
    global _engine
    if _engine is not None:
        try:
            _engine.dispose()
            diag("db", "pool libertado")
        except Exception as exc:  # noqa: BLE001
            diag("db", f"aviso ao libertar pool ({type(exc).__name__}: {exc})")
        _engine = None


def _criar_engine(url: str, hostaddr: str | None = None) -> Engine:
    args: dict[str, object] = {"sslmode": "require", "connect_timeout": 12}
    if hostaddr:
        args["hostaddr"] = hostaddr
        diag("db", f"connect_args hostaddr={hostaddr} (forcar IPv4 na Render)")
    return create_engine(
        url,
        future=True,
        pool_pre_ping=True,
        pool_recycle=300,
        pool_size=2,
        max_overflow=2,
        pool_timeout=30,
        connect_args=args,
    )


def _falha_sem_retry(exc: BaseException) -> bool:
    texto = str(exc).lower()
    return any(
        chave in texto
        for chave in (
            "translate host",
            "name or service not known",
            "network is unreachable",
            "resolvivel",
            "ipv4",
        )
    )


def get_cti_engine() -> Engine:
    """Tenta host directo em IPv4; se falhar, pooler. Nao imprime senha."""
    global _engine, _sql_ok, _sql_aviso, _dns_esgotado
    if _engine is not None:
        diag("db", "reutilizar engine ja ligada")
        return _engine
    if _dns_esgotado:
        diag("db", f"a saltar novas tentativas — {_sql_aviso}")
        raise RuntimeError(_sql_aviso or "nenhum host PostgreSQL resolvivel (DNS)")
    log_ambiente("db")
    ultimo: Exception | None = None
    for url in candidate_urls():
        parsed = urlparse(url)
        host = parsed.hostname or ""
        porta = parsed.port
        if not _host_resolves(host):
            continue
        ipv4 = ipv4_de(host)
        if not ipv4:
            diag("db", f"a saltar host={host} sem IPv4 (Render nao fala IPv6)")
            continue
        diag("db", f"a criar engine host={host} port={porta} ipv4={ipv4} sslmode=require")
        engine = _criar_engine(url, hostaddr=ipv4)
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            _engine = engine
            _sql_ok = True
            _sql_aviso = None
            diag("db", f"PostgreSQL OK host={host} ipv4={ipv4}")
            return engine
        except Exception as exc:  # noqa: BLE001
            ultimo = exc
            diag("db", f"ligacao falhou host={host} ipv4={ipv4} {type(exc).__name__}: {exc}")
            try:
                engine.dispose()
            except Exception:
                pass
    _sql_ok = False
    _sql_aviso = (
        f"{type(ultimo).__name__}: {ultimo}" if ultimo else "nenhum host PostgreSQL com IPv4"
    )
    _dns_esgotado = ultimo is None or _falha_sem_retry(ultimo)
    diag("db", f"aviso: Supabase indisponivel — {_sql_aviso}")
    raise RuntimeError(_sql_aviso)
