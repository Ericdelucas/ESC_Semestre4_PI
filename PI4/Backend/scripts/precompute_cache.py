"""Gera os parquets do dashboard CTI durante o build do Render."""

from __future__ import annotations

import sys
from pathlib import Path


BACKEND = Path(__file__).resolve().parents[1]
PI4_ROOT = BACKEND.parent
FRONTEND = PI4_ROOT / "Frontend"
sys.path.insert(0, str(FRONTEND))

from src.config import CACHE_DIR, CSV_PATH  # noqa: E402
from src.models.analytics import montar_indicadores  # noqa: E402
from src.models.loaders import load_cti_csv  # noqa: E402


def main() -> None:
    if not CSV_PATH.exists():
        raise FileNotFoundError(f"Arquivo base nao encontrado: {CSV_PATH}")

    CACHE_DIR.mkdir(exist_ok=True)
    print(f"[precompute] Lendo base: {CSV_PATH}")
    df = load_cti_csv(CSV_PATH)
    print(f"[precompute] Base compactada: {len(df):,} linhas")

    print("[precompute] Calculando indicadores e ranking...")
    ind, ranking = montar_indicadores(df)

    ind_path = CACHE_DIR / "indicadores.parquet"
    rank_path = CACHE_DIR / "ranking.parquet"
    ind.to_parquet(ind_path, index=False)
    ranking.to_parquet(rank_path, index=False)

    print(f"[precompute] Cache salvo em: {CACHE_DIR}")
    print(f"[precompute] indicadores={ind_path.stat().st_size:,} bytes")
    print(f"[precompute] ranking={rank_path.stat().st_size:,} bytes")


if __name__ == "__main__":
    main()
