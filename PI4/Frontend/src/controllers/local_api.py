"""Garante a API FastAPI local quando o dashboard e o backend partilham o mesmo serviço."""

from __future__ import annotations

import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from urllib.parse import urlparse

from src.config import PI4, resolve_api_base_url

_STARTED = False


def _is_loopback(url: str) -> bool:
    host = (urlparse(url).hostname or "").lower()
    return host in {"127.0.0.1", "localhost", "::1"}


def api_is_up(url: str | None = None, timeout: float = 1.5) -> bool:
    target = (url or resolve_api_base_url()).rstrip("/")
    try:
        urllib.request.urlopen(f"{target}/api/v1/health", timeout=timeout)
        return True
    except (urllib.error.URLError, TimeoutError, OSError):
        return False


def ensure_local_api() -> bool:
    """Sobe uvicorn em background se BACKEND_URL for loopback e o health falhar."""
    global _STARTED
    url = resolve_api_base_url()
    if not _is_loopback(url):
        return api_is_up(url)
    if api_is_up(url):
        return True
    if _STARTED:
        return api_is_up(url, timeout=2)

    parsed = urlparse(url)
    host = parsed.hostname or os.environ.get("API_HOST", "127.0.0.1")
    port = str(parsed.port or os.environ.get("API_PORT", "8081"))
    env = os.environ.copy()
    env["PYTHONPATH"] = str(PI4) + os.pathsep + env.get("PYTHONPATH", "")
    env["BACKEND_URL"] = url
    env["CTI_API_URL"] = url
    log_dir = PI4 / "Backend" / "cache"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "uvicorn-local.log"
    with log_file.open("a", encoding="utf-8") as log:
        log.write(f"\n[local_api] a iniciar uvicorn {host}:{port}\n")
        log.flush()
        subprocess.Popen(
            [
                sys.executable,
                "-m",
                "uvicorn",
                "Backend.main:app",
                "--host",
                host,
                "--port",
                port,
            ],
            cwd=str(PI4),
            env=env,
            stdout=log,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
    _STARTED = True
    for _ in range(40):
        if api_is_up(url, timeout=1.2):
            return True
        time.sleep(0.4)
    return False
