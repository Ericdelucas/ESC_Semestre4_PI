"""Ponto de entrada FastAPI, compativel com uvicorn main:app e Backend.main:app."""
from __future__ import annotations

import sys
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI

# Mantem a resolucao de imports e a precedencia de .env usadas na Render.
_BACKEND = Path(__file__).resolve().parent
_PI4 = _BACKEND.parent
load_dotenv(_BACKEND / ".env")
load_dotenv(_PI4 / ".env")
if str(_PI4) not in sys.path:
    sys.path.insert(0, str(_PI4))

from Backend.runtime import configure_application, lifespan
from Backend.routers.email import router as email_router
from Backend.routers.users import router as users_router
from Backend.routers.health_router import router as health_router
from Backend.routers.auth_router import router as auth_router
from Backend.routers.chat_router import router as chat_router

app = FastAPI(title="CTI Assistente", lifespan=lifespan)
app.include_router(users_router)
app.include_router(email_router)
app.include_router(health_router)
app.include_router(auth_router)
app.include_router(chat_router)
configure_application(app)
