"""Cliente HTTP do Frontend para a API FastAPI."""

from __future__ import annotations

import json
import logging
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

import streamlit as st

from src.config import resolve_api_base_url

HEALTH_PATH = "/api/v1/health"
_RETRY_SLEEP = 2.0

_log = logging.getLogger("cti.api_client")
if not _log.handlers:
    _handler = logging.StreamHandler(sys.stdout)
    _handler.setFormatter(logging.Formatter("%(asctime)s [api_client] %(levelname)s %(message)s"))
    _log.addHandler(_handler)
    _log.setLevel(logging.INFO)
    _log.propagate = False


def _emit(message: str) -> None:
    print(f"[api_client] {message}", flush=True)
    _log.info(message)


def _ler(resposta) -> dict[str, object]:
    bruto = resposta.read().decode("utf-8", errors="replace")
    if not bruto:
        return {}
    dados = json.loads(bruto)
    return dados if isinstance(dados, dict) else {"data": dados}


class ApiClient:
    """Sessao HTTP reutilizada. Health check no maximo uma vez por processo."""

    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")
        self._health_done = False
        self._health_ok = False
        self._health_status = 0

    def _url(self, caminho: str, params: dict[str, object] | None = None) -> str:
        base = f"{self.base_url}{caminho}"
        if not params:
            return base
        query = urllib.parse.urlencode({k: v for k, v in params.items() if v is not None})
        return f"{base}?{query}"

    def request_json(
        self,
        method: str,
        caminho: str,
        *,
        payload: dict[str, object] | None = None,
        params: dict[str, object] | None = None,
        timeout: float = 8,
    ) -> tuple[dict[str, object], int]:
        if method.upper() == "HEAD" or caminho in {"", "/"}:
            method = "GET"
            caminho = HEALTH_PATH if caminho in {"", "/"} else caminho
        url = self._url(caminho, params)
        seguro = dict(payload) if isinstance(payload, dict) else payload
        if isinstance(seguro, dict) and "password" in seguro:
            senha = str(seguro.get("password") or "")
            seguro = {**seguro, "password": f"***len={len(senha)}"}
        _emit(f"ANTES DE ENVIAR {method} {url} timeout={timeout}s payload={seguro} params={params}")
        corpo = None if payload is None else json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=corpo,
            method=method,
            headers={"Content-Type": "application/json", "Accept": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                dados = _ler(resp)
                _emit(
                    f"RESPOSTA OK {method} {url} status={resp.status} "
                    f"headers={dict(resp.headers)} corpo={dados}"
                )
                return dados, int(resp.status)
        except urllib.error.HTTPError as exc:
            try:
                dados = _ler(exc)
            except Exception as read_exc:
                dados = {"detail": str(exc.reason)}
                _emit(f"HTTPError sem corpo {type(read_exc).__name__}: {read_exc}")
            _emit(
                f"HTTPError {type(exc).__name__} {method} {url} status={exc.code} "
                f"reason={exc.reason!r} headers={dict(exc.headers or {})} corpo={dados}"
            )
            if int(exc.code) == 429:
                _emit(f"STATUS 429 Too Many Requests em {url} — sleep {_RETRY_SLEEP}s, sem novo loop")
                time.sleep(_RETRY_SLEEP)
            return dados, int(exc.code)
        except TimeoutError as exc:
            _emit(f"TimeoutError {method} {url}: {exc} — sleep {_RETRY_SLEEP}s")
            time.sleep(_RETRY_SLEEP)
            return {"detail": f"Timeout em {url}: {exc}"}, 503
        except urllib.error.URLError as exc:
            _emit(
                f"URLError/ConnectionError {method} {url} reason={exc.reason!r} "
                f"tipo={type(exc.reason).__name__} — sleep {_RETRY_SLEEP}s"
            )
            time.sleep(_RETRY_SLEEP)
            return {"detail": f"Backend indisponivel em {url}: {exc.reason}"}, 503
        except OSError as exc:
            _emit(f"OSError {method} {url}: {exc} — sleep {_RETRY_SLEEP}s")
            time.sleep(_RETRY_SLEEP)
            return {"detail": f"Backend indisponivel em {url}: {exc}"}, 503

    def check_health(self, timeout: float = 5) -> tuple[bool, int]:
        if self._health_done:
            return self._health_ok, self._health_status
        _payload, status = self.request_json("GET", HEALTH_PATH, timeout=timeout)
        if status != 200:
            time.sleep(_RETRY_SLEEP)
            _payload, status = self.request_json("GET", HEALTH_PATH, timeout=timeout)
        self._health_done = True
        self._health_ok = status == 200
        self._health_status = status
        return self._health_ok, self._health_status


@st.cache_resource
def get_api_client() -> ApiClient:
    """Uma instancia por processo Streamlit — nao reabre sessao a cada clique."""
    client = ApiClient(resolve_api_base_url())
    _emit(f"cliente HTTP em cache: {client.base_url}")
    return client


def request_json(
    method: str,
    caminho: str,
    *,
    payload: dict[str, object] | None = None,
    params: dict[str, object] | None = None,
    timeout: float = 8,
) -> tuple[dict[str, object], int]:
    return get_api_client().request_json(
        method, caminho, payload=payload, params=params, timeout=timeout
    )


def post_json(
    caminho: str,
    payload: dict[str, object],
    params: dict[str, object] | None = None,
    timeout: float = 8,
) -> tuple[dict[str, object], int]:
    return get_api_client().request_json(
        "POST", caminho, payload=payload, params=params, timeout=timeout
    )


def get_json(
    caminho: str,
    params: dict[str, object] | None = None,
    timeout: float = 8,
) -> tuple[dict[str, object], int]:
    return get_api_client().request_json(
        "GET", caminho, params=params, timeout=timeout
    )


def check_health(timeout: float = 5) -> tuple[bool, int]:
    return get_api_client().check_health(timeout=timeout)
