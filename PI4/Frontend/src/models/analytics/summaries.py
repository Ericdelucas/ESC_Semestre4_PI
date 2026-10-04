"""Resumos estatisticos e selecao de cenarios."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

PI4_ROOT = Path(__file__).resolve().parents[4]
if str(PI4_ROOT) not in sys.path:
    sys.path.insert(0, str(PI4_ROOT))

from Backend.metrics import probabilidade_caixa_negativo  # noqa: E402


def resumo_envelope(ind: pd.DataFrame, coluna: str, maior_e_melhor: bool) -> pd.DataFrame:
    g = ind.groupby("ano_num")[coluna]
    out = pd.DataFrame(
        {
            "ano_num": g.mean().index.astype(int),
            "media": g.mean().to_numpy(),
            "mediana": g.median().to_numpy(),
            "p5": g.quantile(0.05).to_numpy(),
            "p95": g.quantile(0.95).to_numpy(),
            "minimo": g.min().to_numpy(),
            "maximo": g.max().to_numpy(),
        }
    )
    if maior_e_melhor:
        out["otimista"] = out["maximo"]
        out["pessimista"] = out["minimo"]
    else:
        out["otimista"] = out["minimo"]
        out["pessimista"] = out["maximo"]
    return out


def resumo_estatistico(serie: pd.Series) -> dict[str, float]:
    """Resumo descritivo alinhado a EDA do analise.ipynb."""
    s = pd.to_numeric(serie, errors="coerce").dropna()
    if s.empty:
        return {"n": 0}
    return {
        "n": float(s.shape[0]),
        "media": float(s.mean()),
        "mediana": float(s.median()),
        "desvio_padrao": float(s.std(ddof=1)),
        "minimo": float(s.min()),
        "maximo": float(s.max()),
        "q1": float(s.quantile(0.25)),
        "q3": float(s.quantile(0.75)),
        "p5": float(s.quantile(0.05)),
        "p95": float(s.quantile(0.95)),
    }


def cenas_por_percentil(ranking: pd.DataFrame, coluna: str, qs: list[float]) -> dict[float, str]:
    serie = ranking[coluna].dropna()
    out: dict[float, str] = {}
    for q in qs:
        alvo = float(serie.quantile(q))
        idx = (ranking[coluna] - alvo).abs().idxmin()
        out[q] = str(ranking.loc[idx, "CENA"])
    return out


