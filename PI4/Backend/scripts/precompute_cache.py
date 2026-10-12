"""Gera os parquets completos do dashboard CTI durante o build da Render."""

from __future__ import annotations

import sys
from pathlib import Path


BACKEND = Path(__file__).resolve().parents[1]
PI4_ROOT = BACKEND.parent
sys.path.insert(0, str(PI4_ROOT))

from Backend.data_loader import CACHE_DIR, CSV_PATH, load_cti_csv, otimizar_base_cti  # noqa: E402
from Backend.metrics import montar_indicadores  # noqa: E402


def _volume(df, nome: str) -> None:
    contas = int(df["CONTA"].nunique()) if "CONTA" in df.columns else 0
    cenas = int(df["CENA"].nunique()) if "CENA" in df.columns else 0
    anos = int(df["ano_num"].nunique()) if "ano_num" in df.columns else 0
    print(
        f"[precompute] {nome} linhas={len(df):,} shape={df.shape} "
        f"contas={contas} cenas={cenas} anos={anos}",
        flush=True,
    )


def main() -> None:
    if not CSV_PATH.exists():
        raise FileNotFoundError(f"Arquivo base nao encontrado: {CSV_PATH}")

    CACHE_DIR.mkdir(exist_ok=True)
    print(f"[precompute] Lendo CSV local (build): {CSV_PATH}", flush=True)
    df = otimizar_base_cti(load_cti_csv(CSV_PATH, forcar_ficheiro=True))
    _volume(df, "base")
    if df.empty or len(df) < 1000:
        raise RuntimeError(f"Precompute recusou base incompleta: {len(df)} linhas")

    print("[precompute] Calculando indicadores e ranking...", flush=True)
    ind, ranking = montar_indicadores(df)
    _volume(ind, "indicadores")
    print(f"[precompute] ranking linhas={len(ranking):,}", flush=True)

    raw_path = CACHE_DIR / "cti_limpo.parquet"
    ind_path = CACHE_DIR / "indicadores.parquet"
    rank_path = CACHE_DIR / "ranking.parquet"
    df.to_parquet(raw_path, index=False)
    ind.to_parquet(ind_path, index=False)
    ranking.to_parquet(rank_path, index=False)

    print(f"[precompute] Cache completo gravado em: {CACHE_DIR}", flush=True)
    print(f"[precompute] cti_limpo={raw_path.stat().st_size:,} bytes (sempre reescrito)", flush=True)
    print(f"[precompute] indicadores={ind_path.stat().st_size:,} bytes", flush=True)
    print(f"[precompute] ranking={rank_path.stat().st_size:,} bytes", flush=True)


if __name__ == "__main__":
    main()
