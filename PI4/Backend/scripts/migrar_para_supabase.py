"""Envia Cti.csv para a tabela cti_dados no PostgreSQL do Supabase, em lotes."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from urllib.parse import quote_plus

import pandas as pd
from sqlalchemy import create_engine, text

BACKEND = Path(__file__).resolve().parents[1]
PI4_ROOT = BACKEND.parent
if str(PI4_ROOT) not in sys.path:
    sys.path.insert(0, str(PI4_ROOT))

from Backend.data_loader.csv_reader import CTI_COLUMNS, CSV_PATH, _preparar_chunk

CHUNK_SIZE = 10_000
DEFAULT_URL = (
    "postgresql://postgres:CtiDashboard2026!@db.rvpfnqaiwqzwhrnruspj.supabase.co:5432/postgres"
)

DDL = """
CREATE TABLE IF NOT EXISTS cti_dados (
    id BIGSERIAL PRIMARY KEY,
    "ANO" TEXT,
    "CENA" TEXT,
    "CONTA" TEXT,
    "VALOR" DOUBLE PRECISION,
    ano_num INTEGER
)
"""


def connection_url() -> str:
    raw = (os.environ.get("SUPABASE_DB_URL") or DEFAULT_URL).strip()
    if "sslmode=" not in raw:
        raw = f"{raw}{'&' if '?' in raw else '?'}sslmode=require"
    if "CtiDashboard2026!" in raw:
        raw = raw.replace("CtiDashboard2026!", quote_plus("CtiDashboard2026!"))
    if raw.startswith("postgresql://"):
        raw = "postgresql+psycopg2://" + raw[len("postgresql://") :]
    return raw


def main() -> None:
    csv_path = Path(os.environ.get("CTI_CSV_PATH") or CSV_PATH)
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV nao encontrado: {csv_path}")

    engine = create_engine(connection_url(), pool_pre_ping=True)
    print(f"[migrar] CSV={csv_path}", flush=True)
    print("[migrar] destino=cti_dados @ Supabase", flush=True)

    with engine.begin() as conn:
        conn.execute(text(DDL))
        conn.execute(text("TRUNCATE TABLE cti_dados RESTART IDENTITY"))
    print("[migrar] tabela cti_dados pronta (truncate)", flush=True)

    leitor = pd.read_csv(
        csv_path,
        header=None,
        names=CTI_COLUMNS,
        dtype=str,
        engine="c",
        chunksize=CHUNK_SIZE,
        low_memory=False,
    )

    enviados = 0
    lote = 0
    for bruto in leitor:
        lote += 1
        bloco = _preparar_chunk(bruto)
        bloco["ano_num"] = pd.to_numeric(bloco["ano_num"], errors="coerce")
        bloco.to_sql(
            "cti_dados",
            engine,
            if_exists="append",
            index=False,
            method="multi",
        )
        enviados += len(bloco)
        print(f"[migrar] lote {lote} enviado ({len(bloco):,} linhas) | total={enviados:,}", flush=True)

    print(f"[migrar] concluido: {enviados:,} linhas em {lote} lotes", flush=True)


if __name__ == "__main__":
    main()
