"""Motor RAG e historico de sessoes partilhado pelos pedidos de chat."""
from __future__ import annotations

from threading import Lock
from typing import TYPE_CHECKING

from Backend.diag import log_ia

if TYPE_CHECKING:
    from Backend.rag_engine import CTIRag

_engine: CTIRag | None = None
_engine_lock = Lock()
_sessoes: dict[str, list[dict[str, str]]] = {}


def _rag() -> CTIRag:
    global _engine
    if _engine is None:
        with _engine_lock:
            if _engine is None:
                # O RAG e as suas dependencias so sao carregados no primeiro chat.
                from Backend.rag_engine import CTIRag

                _engine = CTIRag()
    return _engine


def responder_chat(
    message: str, session_id: str | None = None, user_role: str | None = None,
) -> tuple[str, list[str]]:
    """Mantem a inicializacao lazy do RAG e as ultimas 12 mensagens por sessao."""
    texto = message.strip()
    log_ia(f"API /api/chat: chegou session={session_id!r} role={user_role} chars={len(texto)}")
    if not texto:
        return "Escreva uma pergunta sobre os cenários da CTI.", []
    chave = (session_id or "default").strip() or "default"
    historico = _sessoes.setdefault(chave, [])
    resposta, fontes = _rag().responder(texto, historico, user_role=user_role)
    log_ia(f"API /api/chat: resposta chars={len(resposta)} fontes={len(fontes)}")
    historico.append({"role": "user", "content": texto})
    historico.append({"role": "assistant", "content": resposta})
    _sessoes[chave] = historico[-12:]
    return resposta, fontes
