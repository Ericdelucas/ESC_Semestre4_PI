"""API do chat CTI, autenticacao e saude."""

from __future__ import annotations

import sys
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy import func, select

_BACKEND = Path(__file__).resolve().parent
_PI4 = _BACKEND.parent
load_dotenv(_BACKEND / ".env")
load_dotenv(_PI4 / ".env")

if str(_PI4) not in sys.path:
    sys.path.insert(0, str(_PI4))

from Backend.db import init_db, seed_usuarios, session_scope
from Backend.db.auth import autenticar, listar_logs, registrar_log, usuario_publico
from Backend.db.models import Usuario
from Backend.rag_engine import CTIRag
from Backend.routers.email import router as email_router
from Backend.routers.users import router as users_router
from Backend.services.rag_indexer import status_rag
from Backend.services.email_service import smtp_configurado
from Backend.services.risk_alerts import FUNCOES_EXECUTIVAS, disparar_alerta_risco, forcar_alerta_login

APP_VERSION = "1.0.0"
_HEALTH = {"status": "online", "message": "API CTI Backend Ativa"}
_CORS_ORIGINS = [
    "http://localhost:8501",
    "http://127.0.0.1:8501",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    seed_usuarios()
    yield


app = FastAPI(title="CTI Assistente", lifespan=lifespan)
app.include_router(users_router)
app.include_router(email_router)
app.add_middleware(
    CORSMiddleware,
    allow_origins=_CORS_ORIGINS,
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_engine: CTIRag | None = None
_sessoes: dict[str, list[dict[str, str]]] = {}


class ChatIn(BaseModel):
    message: str
    session_id: str | None = None
    user_role: str | None = None


class ChatOut(BaseModel):
    response: str
    sources: list[str] = Field(default_factory=list)


class LoginIn(BaseModel):
    email: str
    password: str


class LogoutIn(BaseModel):
    email: str


def _rag() -> CTIRag:
    global _engine
    if _engine is None:
        _engine = CTIRag()
    return _engine


def _ip_cliente(request: Request) -> str:
    encaminhado = request.headers.get("x-forwarded-for", "")
    if encaminhado:
        return encaminhado.split(",")[0].strip()
    if request.client:
        return request.client.host
    return ""


def _status_banco() -> dict[str, object]:
    try:
        with session_scope() as db:
            total = int(db.scalar(select(func.count()).select_from(Usuario)) or 0)
        return {"ok": True, "usuarios": total}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}


@app.get("/")
@app.get("/api/health")
def health_root() -> dict[str, str]:
    return dict(_HEALTH)


@app.get("/json/version")
def json_version() -> dict[str, str]:
    return {"version": APP_VERSION, "status": "ok"}


@app.get("/api/v1/health")
def health_v1() -> dict[str, object]:
    banco = _status_banco()
    rag = status_rag()
    online = bool(banco.get("ok")) and bool(rag.get("ok"))
    return {
        "status": "online" if online else "degraded",
        "message": "API CTI Backend Ativa",
        "version": APP_VERSION,
        "database": banco,
        "rag": {
            "ok": rag.get("ok"),
            "count": rag.get("count"),
            "globs": rag.get("globs"),
            "directory": rag.get("directory"),
        },
        "email": {
            "smtp_configured": smtp_configurado(),
            "force_alert_on_login": forcar_alerta_login(),
            "routes": [
                "POST /api/v1/email/testar",
                "GET /api/v1/email/status",
                "GET /api/v1/email/riscos",
                "POST /api/v1/email/varrer-risco",
            ],
        },
    }


@app.post("/api/v1/auth/login")
def login(body: LoginIn, request: Request) -> dict[str, object]:
    with session_scope() as db:
        usuario, mensagem = autenticar(db, body.email, body.password, ip_origem=_ip_cliente(request))
        publico = usuario_publico(usuario) if usuario is not None else None
    if usuario is None or publico is None:
        raise HTTPException(status_code=401, detail=mensagem)
    risco: dict[str, object] | None = None
    if str(publico.get("funcao") or "") in FUNCOES_EXECUTIVAS or bool(publico.get("is_super_admin")):
        try:
            risco = disparar_alerta_risco(
                str(publico.get("email") or body.email),
                forcar=False,
                simular=forcar_alerta_login(),
                origem="login",
            )
        except Exception as exc:  # noqa: BLE001
            risco = {"critical": False, "sent": False, "summary": f"Varredura indisponivel: {type(exc).__name__}: {exc}"}
    return {"ok": True, "message": mensagem, "user": publico, "risk_alert": risco}


@app.post("/api/v1/auth/logout")
def logout(body: LogoutIn, request: Request) -> dict[str, object]:
    email = body.email.strip().lower()
    with session_scope() as db:
        usuario = db.scalar(select(Usuario).where(Usuario.email == email))
        registrar_log(
            db,
            email=email,
            sucesso=True,
            mensagem="Logout efetuado",
            funcao=usuario.funcao if usuario is not None else None,
            ip_origem=_ip_cliente(request),
        )
    return {"ok": True, "message": "Logout efetuado"}


@app.get("/api/v1/auth/logs")
def logs_acesso(email: str, limite: int = 200) -> dict[str, object]:
    email_norm = email.strip().lower()
    with session_scope() as db:
        solicitante = db.scalar(select(Usuario).where(Usuario.email == email_norm))
        if solicitante is None or solicitante.funcao != "CEO" or not solicitante.ativo:
            raise HTTPException(status_code=403, detail="Apenas o CEO pode consultar os logs de acesso.")
        registros = listar_logs(db, limite)
        return {
            "ok": True,
            "logs": [
                {
                    "id": item.id,
                    "email_usuario": item.email_usuario,
                    "funcao": item.funcao,
                    "sucesso": item.sucesso,
                    "data_hora": item.data_hora.isoformat(sep=" ", timespec="seconds") if item.data_hora else None,
                    "ip_origem": item.ip_origem,
                    "mensagem": item.mensagem,
                }
                for item in registros
            ],
        }


@app.post("/api/chat", response_model=ChatOut)
def chat(body: ChatIn) -> ChatOut:
    texto = body.message.strip()
    if not texto:
        return ChatOut(response="Escreva uma pergunta sobre os cenários da CTI.", sources=[])
    chave = (body.session_id or "default").strip() or "default"
    historico = _sessoes.setdefault(chave, [])
    resposta, fontes = _rag().responder(texto, historico, user_role=body.user_role)
    historico.append({"role": "user", "content": texto})
    historico.append({"role": "assistant", "content": resposta})
    _sessoes[chave] = historico[-12:]
    return ChatOut(response=resposta, sources=fontes)
