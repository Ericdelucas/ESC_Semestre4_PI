"""Constantes e caminhos do painel CTI."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CSV_PATH = ROOT / "Cti.csv"
CACHE_DIR = ROOT / "cache"
DOCS_DIR = ROOT / "documentos"
REPO_DOCS_DIR = ROOT.parent / "documentos"
VENV_PY = ROOT / ".venv" / "bin" / "python"

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
    "geral",
    "cfo",
    "acionistas",
    "concedente",
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
    "comparar",
    "assistente",
    "como_ler",
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
