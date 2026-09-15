"""Regras de negócio e classificação de selos de risco."""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.config import SELOS_NEGOCIO


def classificar_cenarios(ranking: pd.DataFrame) -> pd.DataFrame:
    """Atribui selos de negócio (quartis + regras) de forma vetorizada."""
    out = ranking.copy()
    q_rent = out["rentabilidade"].quantile([0.25, 0.50, 0.75])
    q_liq = out["liquidez"].quantile([0.25, 0.50, 0.75])
    q_risco = out["risco"].quantile([0.25, 0.75])
    q_inv = float(out["pressao_invest"].quantile(0.75))
    q_dist = float(out["dist_abs"].quantile(0.75))
    q_disp = float(out["liquidez_acumulada"].quantile(0.25))
    med_inv = float(out["pressao_invest"].median())

    out["Alta rentabilidade"] = out["rentabilidade"] >= q_rent[0.75]
    out["Retorno moderado"] = out["rentabilidade"].between(q_rent[0.25], q_rent[0.75], inclusive="left")
    out["Alta liquidez"] = out["liquidez"] >= q_liq[0.75]
    out["Baixa liquidez"] = out["liquidez"] <= q_liq[0.25]
    out["Baixo risco"] = out["risco"] <= q_risco[0.25]
    out["Alto risco"] = out["risco"] >= q_risco[0.75]

    caixa_neg = out["caixa_ano12"].notna() & (out["caixa_ano12"] < 0)
    dist_baixa_disp = (out["dist_abs"] >= q_dist) & (out["liquidez_acumulada"] <= q_disp)
    pressao = out["pressao_invest"] >= q_inv
    alta_alta = out["Alta rentabilidade"] & out["Alta liquidez"]
    alta_baixa = out["Alta rentabilidade"] & out["Baixa liquidez"]
    mod_baixo = out["Retorno moderado"] & out["Baixo risco"]
    alta_resto_alta = out["Alta rentabilidade"] & (out["liquidez"] >= q_liq[0.5])
    alta_resto_baixa = out["Alta rentabilidade"] & (out["liquidez"] < q_liq[0.5])
    so_baixo_risco = out["Baixo risco"]
    pressao_med = out["pressao_invest"] >= med_inv

    out["selo"] = np.select(
        [
            caixa_neg,
            dist_baixa_disp,
            pressao,
            alta_alta,
            alta_baixa,
            mod_baixo,
            alta_resto_alta,
            alta_resto_baixa,
            so_baixo_risco,
            pressao_med,
        ],
        [
            "Encerramento com Caixa Insuficiente",
            "Elevada Distribuição & Baixa Disponibilidade",
            "Forte Pressão de Investimentos",
            "Alta Rentabilidade & Alta Liquidez",
            "Alta Rentabilidade & Baixa Liquidez",
            "Retorno Moderado & Baixo Risco",
            "Alta Rentabilidade & Alta Liquidez",
            "Alta Rentabilidade & Baixa Liquidez",
            "Retorno Moderado & Baixo Risco",
            "Forte Pressão de Investimentos",
        ],
        default="Retorno Moderado & Baixo Risco",
    )
    _ = SELOS_NEGOCIO
    return out
