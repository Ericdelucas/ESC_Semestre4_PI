"""Tabelas usuarios e logs_acesso."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


class Usuario(Base):
    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    senha_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    funcao: Mapped[str] = mapped_column(String(64), nullable=False)
    ativo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_super_admin: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    criado_em: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)


class LogAcesso(Base):
    __tablename__ = "logs_acesso"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email_usuario: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    funcao: Mapped[str | None] = mapped_column(String(64), nullable=True)
    sucesso: Mapped[bool] = mapped_column(Boolean, nullable=False)
    data_hora: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    ip_origem: Mapped[str | None] = mapped_column(String(64), nullable=True)
    mensagem: Mapped[str] = mapped_column(String(255), nullable=False)
