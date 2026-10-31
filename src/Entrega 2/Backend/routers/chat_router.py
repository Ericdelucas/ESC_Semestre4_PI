"""Endpoint de chat com o contrato original de entrada e resposta."""
from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field

from Backend.services.chat_service import responder_chat

router = APIRouter()


class ChatIn(BaseModel):
    message: str
    session_id: str | None = None
    user_role: str | None = None


class ChatOut(BaseModel):
    response: str
    sources: list[str] = Field(default_factory=list)


@router.post("/api/chat", response_model=ChatOut)
def chat(body: ChatIn) -> ChatOut:
    resposta, fontes = responder_chat(body.message, body.session_id, body.user_role)
    return ChatOut(response=resposta, sources=fontes)
