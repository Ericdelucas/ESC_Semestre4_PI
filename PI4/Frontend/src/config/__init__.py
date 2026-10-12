"""Constantes e caminhos do painel CTI."""

from __future__ import annotations

import os
from pathlib import Path

_LOOPBACK = {"127.0.0.1", "localhost", "::1"}
_BIND_ALL = {"0.0.0.0", "::"}
_PUBLIC_HINTS = ("onrender.com",)
_INTERNAL_FALLBACK = "http://127.0.0.1:8081"


def default_api_port() -> str:
    return os.environ.get("API_PORT") or "8081"


def _normalize_url(value: str) -> str:
    url = (value or "").strip().rstrip("/")
    if not url:
        return ""
    if "://" not in url:
        host = url.split("/")[0].split(":")[0].lower()
        scheme = "http" if host in _LOOPBACK or host in _BIND_ALL else (
            "https" if os.environ.get("RENDER") else "http"
        )
        url = f"{scheme}://{url}"
    return url


def _is_public_render_url(url: str) -> bool:
    lowered = url.lower()
    return any(hint in lowered for hint in _PUBLIC_HINTS)


def _rewrite_bind_all(url: str) -> str:
    """0.0.0.0 e URL publica nao servem para o cliente no mesmo container."""
    from urllib.parse import urlparse, urlunparse

    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    port = parsed.port or int(default_api_port())
    if host in _BIND_ALL or (os.environ.get("RENDER") and _is_public_render_url(url)):
        return f"http://127.0.0.1:{port if not _is_public_render_url(url) else default_api_port()}"
    if host in _LOOPBACK and parsed.scheme == "https":
        netloc = f"{host}:{port}" if parsed.port else host
        return urlunparse(("http", netloc, parsed.path, "", "", "")).rstrip("/")
    return url


def resolve_api_base_url() -> str:
    """Em producao o cliente fala com o FastAPI no mesmo container (loopback)."""
    if os.environ.get("RENDER"):
        return f"http://127.0.0.1:{default_api_port()}"
    for name in ("BACKEND_URL", "CTI_API_URL"):
        raw = (os.environ.get(name) or "").strip()
        if not raw:
            continue
        url = _rewrite_bind_all(_normalize_url(raw))
        if url and not _is_public_render_url(url):
            return url
    host = os.environ.get("API_HOST", "127.0.0.1")
    if host in _BIND_ALL:
        host = "127.0.0.1"
    return _rewrite_bind_all(_normalize_url(f"http://{host}:{default_api_port()}")) or _INTERNAL_FALLBACK


_FRONTEND = Path(__file__).resolve().parents[2]
PI4 = _FRONTEND.parent
ROOT = PI4
BACKEND = PI4 / "Backend"
CSV_PATH = BACKEND / "Cti.csv"
CACHE_DIR = BACKEND / "cache"
DOCS_DIR = BACKEND / "documentos"
VENV_PY = ROOT / ".venv" / "bin" / "python"
API_HOST = os.environ.get("API_HOST", "127.0.0.1")
API_PORT = default_api_port()
API_BASE_URL = resolve_api_base_url()

COR = "#1F4E45"
COR_SUAVE = "#5B8A7A"
COR_ALERTA = "#A65D3F"
COR_OK = "#2F6B4F"
COR_ANCORA = "#E8C07A"
COR_AMARELO = "#C4A35A"
COR_LARANJA = "#D17A3A"
COR_ROXO = "#6B4C7A"
COR_VERMELHO = "#B33A3A"
COR_VERDE_ESCURO = "#1A4D3E"
COR_VERDE_CLARO = "#7BA17B"

SELOS_NEGOCIO = [
    "Alta Rentabilidade & Alta Liquidez",
    "Alta Rentabilidade & Baixa Liquidez",
    "Retorno Moderado & Baixo Risco",
    "Forte Pressão de Investimentos",
    "Elevada Distribuição & Baixa Disponibilidade",
    "Encerramento com Caixa Insuficiente",
]

CORES_SELO = {
    "Alta Rentabilidade & Alta Liquidez": COR_VERDE_ESCURO,
    "Alta Rentabilidade & Baixa Liquidez": COR_AMARELO,
    "Retorno Moderado & Baixo Risco": COR_VERDE_CLARO,
    "Forte Pressão de Investimentos": COR_LARANJA,
    "Elevada Distribuição & Baixa Disponibilidade": COR_ROXO,
    "Encerramento com Caixa Insuficiente": COR_VERMELHO,
}

PERSONAS = [
    "ceo",
    "cfo",
    "acionistas",
    "concedente",
    "teste",
]

METRICAS_NUVEM: dict[str, tuple[str, bool]] = {
    "metric.cash_available": ("disponivel", True),
    "metric.cash_generation": ("geracao_caixa", True),
    "metric.treasury": ("Saldo_Tesouraria", True),
    "metric.ncg": ("NCG", False),
}

NAV_KEYS = [
    "capital_giro",
    "prazos",
    "mapeamento",
    "distribuicao",
    "faixa",
    "como_ler",
    "comparar",
]

CORES_COMPARA = [COR, COR_ALERTA, "#3D6B5A"]

CONTAS_RECEBER = [
    "BAL - Contas a Receber - Clientes",
    "BAL - Contas a Receber - Partes Relacionadas",
    "BAL - Contas a Receber - SWAP",
]

PECAS_CONTAS: dict[str, list[str]] = {
    "estoques": ["BAL - Estoques Diversos"],
    "creditos_tributarios": ["BAL - Créditos Tributários"],
    "fornecedores": ["BAL - Fornecedores"],
    "encargos_sociais": ["BAL - Encargos Sociais e Trabalhistas"],
    "tributos_a_pagar": ["BAL - Tributos a pagar"],
    "disponivel": ["BAL - Disponível"],
    "emprestimos_cp": ["BAL - Empréstimos"],
    "ativo_circ": ["BAL - Ativo Circulante"],
    "passivo_circ": ["BAL - Passivo Circulante"],
    "total_ativo": ["BAL - Total do Ativo"],
    "total_passivo": ["BAL - Total do Passivo"],
    "dre_receita": ["DRE - Receita"],
    "dre_custos": ["DRE - Custos"],
    "resultado": ["DRE - Resultado Líquido"],
    "ebitda": ["DRE - EBITDA"],
    "geracao_caixa": ["FLU - Geração de Caixa"],
    "investimentos": ["FLU - Investimentos"],
    "distribuicao": ["FLU - Distribuição para Acionista"],
    "saldo_final": ["FLU - Saldo Final"],
}
