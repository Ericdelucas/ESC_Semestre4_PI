"""Cliente HTTP do Frontend para a API FastAPI."""

from __future__ import annotations

import json
import logging
import sys
import urllib.error
import urllib.parse
import urllib.request

from src.config import resolve_api_base_url

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


def _url(caminho: str, params: dict[str, object] | None = None) -> str:
    base = f"{resolve_api_base_url()}{caminho}"
    if not params:
        return base
    query = urllib.parse.urlencode({k: v for k, v in params.items() if v is not None})
    return f"{base}?{query}"


def _ler(resposta) -> dict[str, object]:
    bruto = resposta.read().decode("utf-8", errors="replace")
    if not bruto:
        return {}
    dados = json.loads(bruto)
    return dados if isinstance(dados, dict) else {"data": dados}


def request_json(
    method: str,
    caminho: str,
    *,
    payload: dict[str, object] | None = None,
    params: dict[str, object] | None = None,
    timeout: float = 8,
) -> tuple[dict[str, object], int]:
    url = _url(caminho, params)
    _emit(f"a chamar {method} {url} timeout={timeout}s payload={payload} params={params}")
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
            _emit(f"resposta {method} {url} status={resp.status} keys={list(dados)}")
            return dados, int(resp.status)
    except urllib.error.HTTPError as exc:
        try:
            dados = _ler(exc)
        except Exception as read_exc:  # noqa: BLE001
            dados = {"detail": str(exc.reason)}
            _emit(f"HTTPError sem corpo {method} {url} status={exc.code} read_exc={read_exc}")
        _emit(f"HTTPError {method} {url} status={exc.code} reason={exc.reason} body={dados}")
        return dados, int(exc.code)
    except TimeoutError as exc:
        _emit(f"TimeoutError {method} {url} {exc}")
        return {"detail": f"Timeout em {url}: {exc}"}, 503
    except urllib.error.URLError as exc:
        _emit(f"URLError {method} {url} reason={exc.reason!r} tipo={type(exc.reason).__name__}")
        return {"detail": f"Backend indisponivel em {url}: {exc.reason}"}, 503
    except Exception as exc:  # noqa: BLE001
        _emit(f"ERRO {type(exc).__name__} {method} {url}: {exc}")
        return {"detail": f"{type(exc).__name__} em {url}: {exc}"}, 503


def post_json(
    caminho: str,
    payload: dict[str, object],
    params: dict[str, object] | None = None,
    timeout: float = 8,
) -> tuple[dict[str, object], int]:
    return request_json("POST", caminho, payload=payload, params=params, timeout=timeout)


def get_json(caminho: str, params: dict[str, object] | None = None) -> tuple[dict[str, object], int]:
    return request_json("GET", caminho, params=params)
