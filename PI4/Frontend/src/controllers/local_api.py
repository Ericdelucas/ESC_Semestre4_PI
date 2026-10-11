"""Sonda unica e cacheada da API. Nao inicia o Uvicorn e nao entra em loop."""

from __future__ import annotations

import streamlit as st

from src.config import resolve_api_base_url
from src.models.api_client import check_health, get_api_client

HEALTH_PATH = "/api/v1/health"


@st.cache_resource
def _cached_boot_probe() -> bool:
    """Corre uma vez por processo. Se falhar, espera 2s e tenta so mais uma vez."""
    get_api_client()
    print(f"[local_api] GET {resolve_api_base_url()}{HEALTH_PATH}", flush=True)
    ok, status = check_health()
    print(f"[local_api] health cacheado status={status} ok={ok}", flush=True)
    return ok


def dump_api_env() -> str:
    return resolve_api_base_url()


def probe_api(url: str | None = None, timeout: float = 3.0) -> bool:
    del url, timeout
    return _cached_boot_probe()
