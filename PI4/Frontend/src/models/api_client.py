"""Cliente HTTP do Frontend. Um pedido por acao do utilizador, sem retentativas."""

from __future__ import annotations

import json
import logging
import sys
import urllib.error
import urllib.parse
import urllib.request

from src.config import resolve_api_base_url

HEALTH_PATH = "/api/v1/health"

logging.basicConfig(
    level=logging.INFO,
    stream=sys.stdout,
    format="%(asctime)s [api_client] %(levelname)s %(message)s",
    force=False,
)
_log = logging.getLogger("cti.api_client")
_log.setLevel(logging.INFO)
if not _log.handlers:
    _handler = logging.StreamHandler(sys.stdout)
    _handler.setFormatter(logging.Formatter("%(asctime)s [api_client] %(levelname)s %(message)s"))
    _log.addHandler(_handler)
_log.propagate = False

_CLIENT = None


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
    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")

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
        url = self._url(caminho, params)
        seguro = dict(payload) if isinstance(payload, dict) else payload
        if isinstance(seguro, dict) and "password" in seguro:
            senha = str(seguro.get("password") or "")
            seguro = {**seguro, "password": f"***len={len(senha)}"}
        _emit(f"ANTES DE ENVIAR {method} {url} timeout={timeout}s payload={seguro}")
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
                    f"RESPOSTA {method} {url} status={resp.status} "
                    f"headers={dict(resp.headers)} corpo={dados}"
                )
                return dados, int(resp.status)
        except urllib.error.HTTPError as exc:
            try:
                dados = _ler(exc)
            except Exception:
                dados = {"detail": str(exc.reason)}
            _emit(
                f"HTTPError {method} {url} status={exc.code} reason={exc.reason!r} "
                f"headers={dict(exc.headers or {})} corpo={dados}"
            )
            return dados, int(exc.code)
        except TimeoutError as exc:
            _emit(f"TimeoutError {method} {url}: {exc}")
            return {"detail": f"Timeout em {url}: {exc}"}, 503
        except urllib.error.URLError as exc:
            _emit(f"URLError {method} {url} reason={exc.reason!r}")
            return {"detail": f"Backend indisponivel em {url}: {exc.reason}"}, 503
        except OSError as exc:
            _emit(f"OSError {method} {url}: {exc}")
            return {"detail": f"Backend indisponivel em {url}: {exc}"}, 503


def get_api_client() -> ApiClient:
    global _CLIENT
    if _CLIENT is None:
        _CLIENT = ApiClient(resolve_api_base_url())
        _emit(f"cliente unico criado: {_CLIENT.base_url}")
    return _CLIENT


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
