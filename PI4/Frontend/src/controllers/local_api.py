"""Sonda de observabilidade da API local. Nao inicia o Uvicorn."""

from __future__ import annotations

import logging
import os
import sys
import urllib.error
import urllib.request

from src.config import default_api_port, resolve_api_base_url

logging.basicConfig(
    level=logging.INFO,
    stream=sys.stdout,
    format="%(asctime)s [local_api] %(levelname)s %(message)s",
    force=False,
)
_log = logging.getLogger("cti.local_api")


def _emit(message: str) -> None:
    print(f"[local_api] {message}", flush=True)
    _log.info(message)


def dump_api_env() -> str:
    url = resolve_api_base_url()
    _emit("=== Streamlit a resolver a URL da API ===")
    _emit(f"cwd={os.getcwd()}")
    _emit(f"RENDER={os.environ.get('RENDER')} PORT_publica={os.environ.get('PORT')}")
    _emit(f"API_HOST={os.environ.get('API_HOST')} API_PORT={os.environ.get('API_PORT')} default_api_port={default_api_port()}")
    _emit(f"BACKEND_URL={os.environ.get('BACKEND_URL')}")
    _emit(f"CTI_API_URL={os.environ.get('CTI_API_URL')}")
    _emit(f"URL base que o Streamlit vai usar AGORA: {url}")
    if os.environ.get("PORT") and os.environ.get("PORT") == default_api_port():
        _emit("CONFLITO: PORT publica da Render e igual a API_PORT")
    return url


def probe_api(url: str | None = None, timeout: float = 3.0) -> bool:
    target = (url or resolve_api_base_url()).rstrip("/")
    health = f"{target}/api/v1/health"
    _emit(f"tentativa HTTP GET {health} timeout={timeout}s")
    try:
        with urllib.request.urlopen(health, timeout=timeout) as resp:
            body = resp.read()[:300]
            _emit(f"health OK status={resp.status} headers={dict(resp.headers)} body={body!r}")
            return True
    except urllib.error.HTTPError as exc:
        _emit(f"health HTTPError status={exc.code} reason={exc.reason} url={exc.url}")
        return False
    except urllib.error.URLError as exc:
        _emit(f"health URLError reason={exc.reason!r} tipo={type(exc.reason).__name__}")
        return False
    except TimeoutError as exc:
        _emit(f"health TimeoutError {exc}")
        return False
    except Exception as exc:  # noqa: BLE001
        _emit(f"health ERRO {type(exc).__name__}: {exc}")
        return False
