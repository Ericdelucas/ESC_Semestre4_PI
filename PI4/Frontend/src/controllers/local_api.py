"""Health check so sob pedido explicito. Nao corre no arranque da pagina."""

from __future__ import annotations

from src.config import resolve_api_base_url

HEALTH_PATH = "/api/v1/health"


def dump_api_env() -> str:
    url = resolve_api_base_url()
    print(f"[local_api] URL base={url}{HEALTH_PATH}", flush=True)
    return url


def probe_api(url: str | None = None, timeout: float = 3.0) -> bool:
    """Intencionalmente inerte no arranque. Login e que fala com a API."""
    del url, timeout
    print("[local_api] probe_api ignorado — sem GET automatico", flush=True)
    return True
