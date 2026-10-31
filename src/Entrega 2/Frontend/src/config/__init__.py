"""Constantes e caminhos do painel CTI."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from urllib.parse import urlparse, urlunparse

_FRONTEND = Path(__file__).resolve().parents[2]
load_dotenv(_FRONTEND / ".env")
load_dotenv(_FRONTEND.parent / ".env")

_LOOPBACK = {"127.0.0.1", "localhost", "::1"}
_BIND_ALL = {"0.0.0.0", "::"}


def default_api_port() -> str:
    return os.environ.get("API_PORT") or "8000"


def _normalize_url(value: str) -> str:
    url = (value or "").strip().rstrip("/")
    if url and "://" not in url:
        host = url.split("/")[0].split(":")[0].lower()
        scheme = "http" if host in _LOOPBACK or host in _BIND_ALL else (
            "https" if os.environ.get("RENDER") else "http"
        )
        url = f"{scheme}://{url}"
    return url


def _rewrite_bind_all(url: str) -> str:
    """Converte enderecos de bind em enderecos locais acessiveis."""
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    if host in _BIND_ALL:
        return f"http://127.0.0.1:{parsed.port or default_api_port()}"
    if host in _LOOPBACK and parsed.scheme == "https":
        return urlunparse(parsed._replace(scheme="http")).rstrip("/")
    return url


def resolve_api_base_url() -> str:
    """Usa a API publica configurada, com fallback local na porta 8000."""
    for name in ("BACKEND_URL", "API_URL", "CTI_API_URL"):
        raw = (os.environ.get(name) or "").strip()
        if raw:
            return _rewrite_bind_all(_normalize_url(raw))
    host = os.environ.get("API_HOST") or "localhost"
    return _rewrite_bind_all(_normalize_url(f"http://{host}:{default_api_port()}"))


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
