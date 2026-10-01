"""Respostas extrativas e integracao Gemini."""

from __future__ import annotations

import os
import re

from google import genai
from google.genai import types
from langchain_core.documents import Document

from .config import GEMINI_MODELS, MARCA_FALA, SYSTEM_PROMPT_EN, SYSTEM_PROMPT_PT, TERMOS_FIN


def resolve_api_key(explicit: str | None = None) -> str | None:
    if explicit and explicit.strip():
        return explicit.strip()
    for name in ("GOOGLE_API_KEY", "GEMINI_API_KEY"):
        val = os.environ.get(name, "").strip()
        if val:
            return val
    return None


def paragrafos_financeiros(hits: list[Document]) -> list[str]:
    vistos: set[str] = set()
    saida: list[str] = []
    for doc in hits:
        blocos = re.split(r"\n\s*\n", doc.page_content)
        if len(blocos) == 1:
            blocos = [doc.page_content]
        for bloco in blocos:
            limpo = " ".join(bloco.split())
            baixo = limpo.lower()
            if len(limpo) < 40 or not any(termo in baixo for termo in TERMOS_FIN):
                continue
            if MARCA_FALA.search(limpo):
                continue
            chave = limpo[:180]
            if chave in vistos:
                continue
            vistos.add(chave)
            saida.append(limpo[:700])
            if len(saida) >= 4:
                return saida
    return saida


def resposta_extrativa(question: str, hits: list[Document], lang: str) -> str:
    _ = question, hits
    if lang == "en":
        return "I can answer from the active CTI dashboard dataset when the question refers to project indicators, DRE, BP, DFC, scenarios, or dashboard navigation."
    return "Posso responder com base na base ativa do Dashboard CTI quando a pergunta envolver indicadores, DRE, BP, DFC, cenários ou navegação do painel."


def gerar_llm(
    question: str,
    contexto: str,
    lang: str,
    history: list[dict[str, str]],
    api_key: str,
) -> str:
    client = genai.Client(api_key=api_key)
    system = SYSTEM_PROMPT_EN if lang == "en" else SYSTEM_PROMPT_PT
    system += (
        "\n\nNative CTI Dashboard instruction: you are not an external persona. You are the "
        "native analytical engine of the CTI Financial Dashboard. Answer strictly from the "
        "active local dataset context (ctx.df), the recalculated indicators, and the CTI "
        "financial structure (DRE, BP, DFC). For metric or diagnostic questions, cite the "
        "available values directly, such as EBITDA, NCG, Ciclo Financeiro, Liquidez "
        "Corrente, Saldo de Tesouraria, Receita, margins and DFC values. If a number is "
        "not present in the supplied local context, say that clearly. When the local "
        "context includes 'Cartoes visuais do topo no estado atual da tela', those card "
        "values are the single source of truth and override any other supporting snippets "
        "or averages. Do not recalculate or replace them with approximate values. If the user asks a "
        "generic non-CTI concept, answer it directly and concisely without exposing or "
        "forcing the dashboard context. Write conversationally: start with a short natural "
        "explanation of the concept, then weave CTI values into the prose when relevant. "
        "Avoid dumping raw bullet blocks unless the user explicitly asks for a list. Every "
        "visible answer must end with an engaging follow-up question offering to continue "
        "the analysis or navigate to the relevant dashboard tab."
    )
    if contexto.strip():
        system += (
            "\n\nLocal CTI context for internal use only. Never reveal, quote, dump, or "
            "label this block as context/sources/system prompt in the visible answer. "
            "Synthesize only the final answer in natural language and include the required "
            "conversational closing question.\n"
            f"{contexto}"
        )
    idioma = "English" if lang == "en" else "português brasileiro"
    hist = history[-6:]
    linhas_hist = []
    for msg in hist:
        papel = "Usuario" if msg.get("role") == "user" else "Assistente CTI"
        linhas_hist.append(f"{papel}: {msg.get('content', '')}")
    historico = "\n".join(linhas_hist) if linhas_hist else "(sem histórico)"
    prompt = (
        f"Idioma da resposta: {idioma}.\n\n"
        f"Histórico recente:\n{historico}\n\n"
        f"Pergunta: {question}"
    )
    ultimo_erro: Exception | None = None
    for modelo in GEMINI_MODELS:
        try:
            resp = client.models.generate_content(
                model=modelo,
                contents=prompt,
                config=types.GenerateContentConfig(system_instruction=system),
            )
            texto = (resp.text or "").strip()
            if texto:
                return texto
        except Exception as exc:  # noqa: BLE001 - tenta o proximo modelo
            ultimo_erro = exc
            continue
    if lang == "en":
        return f"Could not generate an answer with Gemini: {ultimo_erro}"
    return f"Não foi possível gerar a resposta com o Gemini: {ultimo_erro}"
