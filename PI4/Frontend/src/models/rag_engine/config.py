"""Configuracao e constantes do motor RAG."""

from __future__ import annotations

import re

from dotenv import load_dotenv

from src.config import ROOT

load_dotenv(ROOT / "Backend" / ".env")
load_dotenv(ROOT / ".env")
load_dotenv(ROOT.parent / ".env")

SYSTEM_PROMPT_PT = (
    "Voce e o motor analitico nativo do Dashboard Financeiro CTI. Nao assuma nome, "
    "personagem ou identidade fora do dashboard. Responda estritamente com base no dataset ativo "
    "recalculado no dashboard, nos indicadores derivados e na estrutura financeira CTI "
    "(DRE, BP e DFC). Ao tratar de metricas ou diagnosticos, cite diretamente os valores "
    "disponiveis no contexto local, como EBITDA, NCG, Ciclo Financeiro, Liquidez Corrente, "
    "Saldo de Tesouraria, Receita, margens e valores de DFC. Se o dado nao estiver no "
    "contexto local fornecido, diga isso claramente."
)
SYSTEM_PROMPT_EN = (
    "You are the native analytical engine of the CTI Financial Dashboard. Do not assume "
    "any external name, character, or persona. Answer strictly from the active dataset "
    "recalculated in the dashboard, derived indicators, and CTI financial structure "
    "(Income Statement/DRE, Balance Sheet/BP, and Cash Flow/DFC). For metric or diagnostic "
    "questions, cite directly the values available in the local context, such as EBITDA, "
    "NWC, cash cycle, current liquidity, treasury balance, revenue, margins, and DFC values. "
    "If the data is not in the supplied local context, say that clearly."
)

PLACEHOLDER_NAMES = {"venha para a fecap!"}
TEXT_SUFFIXES = {".md", ".txt", ".markdown"}
PDF_SUFFIXES = {".pdf"}
MAX_FILE_BYTES = 12 * 1024 * 1024
GEMINI_MODELS = ("gemini-2.0-flash", "gemini-1.5-flash", "gemini-2.5-flash")
NOME_TRANSCRICAO = re.compile(
    r"transcri|aula|reuni[aã]o|conversa|anota[cç]|dito_na|o_que_foi",
    re.IGNORECASE,
)
MARCA_FALA = re.compile(
    r"\b(professor|eh,|né\?|beleza|tá pensando|pode falar)\b",
    re.IGNORECASE,
)
TERMOS_FIN = (
    "ncg",
    "tesouraria",
    "selo",
    "ebitda",
    "liquidez",
    "caixa",
    "rentabilidade",
    "ciclo",
    "risco",
    "receita",
)
