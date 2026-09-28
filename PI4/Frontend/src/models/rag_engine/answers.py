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
    _ = question
    if lang == "en":
        titulo = "📄 Selected excerpts from CTI documentation"
        vazio = "No financial excerpt matched this question in the CTI manuals or simulated scenarios."
        dica = "💡 Tip: add GOOGLE_API_KEY to the Backend .env file for summarized analytical answers."
    else:
        titulo = "📄 Trechos Selecionados da Documentação CTI"
        vazio = "Não há trecho financeiro correspondente a essa pergunta nos manuais da CTI nem nos cenários simulados."
        dica = "💡 Dica: Adicione a GOOGLE_API_KEY no arquivo .env do Backend para respostas resumidas e analíticas pela IA."
    paragrafos = paragrafos_financeiros(hits)
    corpo = "\n\n".join(paragrafos) if paragrafos else vazio
    return f"{titulo}\n\n{corpo}\n\n{dica}"


def gerar_llm(
    question: str,
    contexto: str,
    lang: str,
    history: list[dict[str, str]],
    api_key: str,
) -> str:
    client = genai.Client(api_key=api_key)
    system = SYSTEM_PROMPT_EN if lang == "en" else SYSTEM_PROMPT_PT
    idioma = "English" if lang == "en" else "português brasileiro"
    hist = history[-6:]
    linhas_hist = []
    for msg in hist:
        papel = "Diretoria" if msg.get("role") == "user" else "Consultor"
        linhas_hist.append(f"{papel}: {msg.get('content', '')}")
    historico = "\n".join(linhas_hist) if linhas_hist else "(sem histórico)"
    prompt = (
        f"Idioma da resposta: {idioma}.\n\n"
        f"Histórico recente:\n{historico}\n\n"
        f"Contexto recuperado (cenários e manuais):\n{contexto}\n\n"
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
