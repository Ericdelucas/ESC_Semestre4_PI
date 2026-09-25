"""Pipeline analítico: agregações e estatísticas descritivas (sem regras de UI)."""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.config import CONTAS_RECEBER, PECAS_CONTAS
from src.models.classifiers import classificar_cenarios
from src.models.loaders import magnitude


def _mapa_contas() -> dict[str, str]:
    """CONTA original → nome canônico da coluna no wide."""
    mapa: dict[str, str] = {c: "contas_receber" for c in CONTAS_RECEBER}
    for nome, contas in PECAS_CONTAS.items():
        for c in contas:
            mapa[c] = nome
    return mapa


def montar_indicadores(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Calcula NCG, prazos, liquidez e risco; delega selos a classifiers.

    Usa um único pivot (em vez de dezenas de merges) sobre as contas necessárias.
    """
    mapa = _mapa_contas()
    needed = set(mapa)
    slim = df.loc[df["CONTA"].isin(needed), ["ANO", "ano_num", "CENA", "CONTA", "VALOR"]].copy()
    slim["campo"] = slim["CONTA"].map(mapa)
    wide = (
        slim.groupby(["ANO", "ano_num", "CENA", "campo"], as_index=False)["VALOR"]
        .sum()
        .pivot(index=["ANO", "ano_num", "CENA"], columns="campo", values="VALOR")
        .reset_index()
        .fillna(0)
    )
    wide.columns.name = None
    for col in [
        "contas_receber",
        "estoques",
        "creditos_tributarios",
        "fornecedores",
        "encargos_sociais",
        "tributos_a_pagar",
        "disponivel",
        "emprestimos_cp",
        "ativo_circ",
        "passivo_circ",
        "total_ativo",
        "total_passivo",
        "dre_receita",
        "dre_custos",
        "resultado",
        "ebitda",
        "geracao_caixa",
        "investimentos",
        "distribuicao",
        "saldo_final",
    ]:
        if col not in wide.columns:
            wide[col] = 0.0

    base = wide
    base["ACO"] = (
        magnitude(base["contas_receber"])
        + magnitude(base["estoques"])
        + magnitude(base["creditos_tributarios"])
    )
    base["PCO"] = magnitude(
        base["fornecedores"] + base["encargos_sociais"] + base["tributos_a_pagar"]
    )
    base["NCG"] = base["ACO"] - base["PCO"]
    base["Saldo_Tesouraria"] = magnitude(base["disponivel"]) - magnitude(base["emprestimos_cp"])

    custos_abs = base["dre_custos"].abs().replace(0, np.nan)
    receita = base["dre_receita"].replace(0, np.nan)
    base["PMR"] = (magnitude(base["contas_receber"]) / receita) * 365
    base["PME"] = (magnitude(base["estoques"]) / custos_abs) * 365
    base["PMP"] = (magnitude(base["fornecedores"]) / custos_abs) * 365
    base["Ciclo_Financeiro"] = base["PMR"] + base["PME"] - base["PMP"]

    base["rentabilidade"] = base["resultado"] / receita
    base["liquidez"] = magnitude(base["ativo_circ"]) / magnitude(base["passivo_circ"]).replace(0, np.nan)
    base["risco"] = magnitude(base["total_passivo"]) / magnitude(base["total_ativo"]).replace(0, np.nan)
    base["pressao_invest"] = magnitude(base["investimentos"])
    base["dist_abs"] = magnitude(base["distribuicao"])
    base["caixa_mag"] = magnitude(base["disponivel"])
    base["caixa_final_sinal"] = np.where(
        base["saldo_final"].abs() > 1e-9,
        base["saldo_final"],
        base["disponivel"],
    )

    ranking = (
        base.groupby("CENA", as_index=False)
        .agg(
            rentabilidade=("rentabilidade", "mean"),
            liquidez=("liquidez", "mean"),
            risco=("risco", "mean"),
            NCG=("NCG", "mean"),
            Saldo_Tesouraria=("Saldo_Tesouraria", "mean"),
            Ciclo_Financeiro=("Ciclo_Financeiro", "mean"),
            receita=("dre_receita", "mean"),
            resultado=("resultado", "mean"),
            ebitda=("ebitda", "mean"),
            pressao_invest=("pressao_invest", "mean"),
            dist_abs=("dist_abs", "mean"),
            liquidez_acumulada=("caixa_mag", "mean"),
        )
    )

    ano_max = int(base["ano_num"].max()) if base["ano_num"].notna().any() else 12
    encerramento = (
        base.loc[base["ano_num"] == ano_max, ["CENA", "caixa_final_sinal", "caixa_mag"]]
        .groupby("CENA", as_index=False)
        .agg(caixa_ano12=("caixa_final_sinal", "mean"), disponivel_ano12=("caixa_mag", "mean"))
    )
    ranking = ranking.merge(encerramento, on="CENA", how="left")
    ranking = classificar_cenarios(ranking)
    ranking["ano_encerramento"] = ano_max
    return base, ranking


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
    """Resumo descritivo alinhado à EDA do analise.ipynb."""
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


def probabilidade_caixa_negativo(ranking: pd.DataFrame) -> float:
    if ranking.empty or "caixa_ano12" not in ranking.columns:
        return 0.0
    return float((ranking["caixa_ano12"] < 0).mean() * 100)
