"""API do chat CTI."""

from __future__ import annotations

import sys
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

_BACKEND = Path(__file__).resolve().parent
_PI4 = _BACKEND.parent
load_dotenv(_BACKEND / ".env")
load_dotenv(_PI4 / ".env")

if str(_PI4) not in sys.path:
    sys.path.insert(0, str(_PI4))

from Backend.rag_engine import CTIRag

app = FastAPI(title="CTI Assistente")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_engine: CTIRag | None = None
_sessoes: dict[str, list[dict[str, str]]] = {}


class ChatIn(BaseModel):
    message: str
    session_id: str | None = None


class ChatOut(BaseModel):
    response: str
    sources: list[str] = Field(default_factory=list)


def _rag() -> CTIRag:
    global _engine
    if _engine is None:
        _engine = CTIRag()
    return _engine


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/chat", response_model=ChatOut)
def chat(body: ChatIn) -> ChatOut:
    texto = body.message.strip()
    if not texto:
        return ChatOut(response="Escreva uma pergunta sobre os cenários da CTI.", sources=[])
    chave = (body.session_id or "default").strip() or "default"
    historico = _sessoes.setdefault(chave, [])
    resposta, fontes = _rag().responder(texto, historico)
    historico.append({"role": "user", "content": texto})
    historico.append({"role": "assistant", "content": resposta})
    _sessoes[chave] = historico[-12:]
    return ChatOut(response=resposta, sources=fontes)
