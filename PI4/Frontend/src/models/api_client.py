"""Cliente HTTP do Frontend para a API FastAPI."""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request

from src.config import API_BASE_URL


def _url(caminho: str, params: dict[str, object] | None = None) -> str:
    base = f"{API_BASE_URL}{caminho}"
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
    corpo = None if payload is None else json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        _url(caminho, params),
        data=corpo,
        method=method,
        headers={"Content-Type": "application/json", "Accept": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return _ler(resp), int(resp.status)
    except urllib.error.HTTPError as exc:
        try:
            dados = _ler(exc)
        except Exception:
            dados = {"detail": str(exc.reason)}
        return dados, int(exc.code)
    except urllib.error.URLError as exc:
        return {"detail": f"Backend indisponivel em {API_BASE_URL}: {exc.reason}"}, 503


def post_json(
    caminho: str,
    payload: dict[str, object],
    params: dict[str, object] | None = None,
    timeout: float = 8,
) -> tuple[dict[str, object], int]:
    return request_json("POST", caminho, payload=payload, params=params, timeout=timeout)


def get_json(caminho: str, params: dict[str, object] | None = None) -> tuple[dict[str, object], int]:
    return request_json("GET", caminho, params=params)
