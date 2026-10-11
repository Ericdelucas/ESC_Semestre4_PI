"""Sonda unica da API local. Nao inicia o Uvicorn e nao usa HEAD /."""

from __future__ import annotations

import logging
import os
import sys
import time
import urllib.error
import urllib.request

from src.config import default_api_port, resolve_api_base_url

_log = logging.getLogger("cti.local_api")
if not _log.handlers:
    _handler = logging.StreamHandler(sys.stdout)
    _handler.setFormatter(logging.Formatter("%(asctime)s [local_api] %(levelname)s %(message)s"))
    _log.addHandler(_handler)
    _log.setLevel(logging.INFO)
    _log.propagate = False

HEALTH_PATH = "/api/v1/health"
_COOLDOWN_SECONDS = 60.0
_LAST_PROBE_AT = 0.0
_LAST_PROBE_OK: bool | None = None


def _emit(message: str) -> None:
    print(f"[local_api] {message}", flush=True)
    _log.info(message)


def dump_api_env() -> str:
    url = resolve_api_base_url()
    _emit(f"URL base do cliente: {url}")
    _emit(f"health GET {url}{HEALTH_PATH} (nunca HEAD /)")
    _emit(
        f"BACKEND_URL={os.environ.get('BACKEND_URL')} "
        f"CTI_API_URL={os.environ.get('CTI_API_URL')} "
        f"API_PORT={default_api_port()} PORT={os.environ.get('PORT')}"
    )
    return url


def probe_api(url: str | None = None, timeout: float = 3.0) -> bool:
    """Um GET /api/v1/health por janela de cooldown. Sucesso so com HTTP 200."""
    global _LAST_PROBE_AT, _LAST_PROBE_OK
    now = time.monotonic()
    if _LAST_PROBE_OK is not None and (now - _LAST_PROBE_AT) < _COOLDOWN_SECONDS:
        _emit(f"health ignorado (cooldown {_COOLDOWN_SECONDS:.0f}s, ultimo_ok={_LAST_PROBE_OK})")
        return _LAST_PROBE_OK

    target = (url or resolve_api_base_url()).rstrip("/")
    health = f"{target}{HEALTH_PATH}"
    req = urllib.request.Request(
        health,
        method="GET",
        headers={"Accept": "application/json"},
    )
    _emit(f"GET {health} timeout={timeout}s")
    _LAST_PROBE_AT = now
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            status = int(resp.status)
            _emit(f"health status={status}")
            _LAST_PROBE_OK = status == 200
            return _LAST_PROBE_OK
    except urllib.error.HTTPError as exc:
        _emit(f"health HTTPError status={exc.code} reason={exc.reason} method=GET path={HEALTH_PATH}")
        _LAST_PROBE_OK = False
        if exc.code == 429:
            time.sleep(2)
        return False
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        _emit(f"health falhou {type(exc).__name__}: {exc}")
        _LAST_PROBE_OK = False
        return False
