"""Logs verbosos para o Live Tail da Render. Nunca imprime senhas."""

from __future__ import annotations

import os
import time
from urllib.parse import urlparse


def diag(tag: str, mensagem: str) -> None:
    print(f"[{tag}] {time.strftime('%H:%M:%S')} {mensagem}", flush=True)


def mascarar_url(url: str) -> str:
    if not url:
        return "<vazia>"
    parsed = urlparse(url)
    user = parsed.username or ""
    host = parsed.hostname or ""
    port = parsed.port or ""
    db = (parsed.path or "").lstrip("/")
    return f"{parsed.scheme}://{user}:***@{host}:{port}/{db}"


def log_ambiente(tag: str = "env") -> None:
    chaves = (
        "RENDER",
        "PORT",
        "API_HOST",
        "API_PORT",
        "API_BIND",
        "BACKEND_URL",
        "CTI_API_URL",
        "SUPABASE_REGION",
    )
    for chave in chaves:
        diag(tag, f"{chave}={os.environ.get(chave)!r}")
    for chave in ("DATABASE_URL", "SUPABASE_DB_URL", "DATABASE_URL_POOLER", "SUPABASE_POOLER_URL"):
        valor = (os.environ.get(chave) or "").strip()
        if valor:
            diag(tag, f"{chave} presente={True} url={mascarar_url(valor)}")
        else:
            diag(tag, f"{chave} presente={False}")
