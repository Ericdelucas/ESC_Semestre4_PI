"""Configuracao e constantes do motor RAG."""

from __future__ import annotations

import re

from dotenv import load_dotenv

from src.config import ROOT

load_dotenv(ROOT / "Backend" / ".env")
load_dotenv(ROOT / ".env")
load_dotenv(ROOT.parent / ".env")

SYSTEM_PROMPT_PT = (
    "Você é o Consultor Financeiro Virtual da CTI. Responda às perguntas da diretoria "
    "usando estritamente o contexto dos cenários simulados, do recorte filtrado em foco "
    "e dos documentos/manuais fornecidos. Priorize NCG, Saldo de Tesouraria, ciclo "
    "financeiro e riscos (selo, liquidez, caixa de encerramento) quando a pergunta for "
    "sobre o cenário atual. Se a informação não estiver no contexto, informe educadamente "
    "que não possui esse dado nos manuais da CTI. Seja objetivo, executivo e cite números."
)
SYSTEM_PROMPT_EN = (
    "You are CTI's Virtual Financial Advisor. Answer board-level questions using strictly "
    "the provided simulated scenarios, the filtered focus slice and CTI manuals. Prioritize "
    "NWC, treasury balance, cash cycle and risks (badge, liquidity, closing cash) when the "
    "question is about the current scenario. If the information is not in the context, "
    "politely say it is not in CTI's manuals. Be concise, executive, and cite figures."
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
