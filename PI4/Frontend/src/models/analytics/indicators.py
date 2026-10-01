"""Montagem dos indicadores analiticos derivados das demonstracoes."""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.config import CONTAS_RECEBER, PECAS_CONTAS
from src.models.classifiers import classificar_cenarios
from src.models.loaders import magnitude


def _compactar_indicadores(df: pd.DataFrame) -> pd.DataFrame:
    out = df
    if "CENA" in out.columns:
        out["CENA"] = out["CENA"].astype("category")
    if "ANO" in out.columns:
        out["ANO"] = out["ANO"].astype("category")
    if "ano_num" in out.columns:
        out["ano_num"] = pd.to_numeric(out["ano_num"], errors="coerce").fillna(0).astype("int8")
    for col in out.select_dtypes(include=["float64", "int64", "Int64"]).columns:
        if col != "ano_num":
            out[col] = pd.to_numeric(out[col], errors="coerce").astype("float32")
    return out


def _mapa_contas() -> dict[str, str]:
    """CONTA original -> nome canonico da coluna no wide."""
    mapa: dict[str, str] = {c: "contas_receber" for c in CONTAS_RECEBER}
    for nome, contas in PECAS_CONTAS.items():
        for c in contas:
            mapa[c] = nome
    return mapa


def montar_indicadores(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Calcula NCG, prazos, liquidez e risco; delega selos a classifiers.

    Usa um unico pivot (em vez de dezenas de merges) sobre as contas necessarias.
    """
    mapa = _mapa_contas()
    needed = set(mapa)
    slim = df.loc[df["CONTA"].isin(needed), ["ANO", "ano_num", "CENA", "CONTA", "VALOR"]].copy()
    slim["campo"] = slim["CONTA"].map(mapa)
    wide = (
        slim.groupby(["ANO", "ano_num", "CENA", "campo"], as_index=False, observed=True)["VALOR"]
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
        base.groupby("CENA", as_index=False, observed=True)
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
        .groupby("CENA", as_index=False, observed=True)
        .agg(caixa_ano12=("caixa_final_sinal", "mean"), disponivel_ano12=("caixa_mag", "mean"))
    )
    ranking = ranking.merge(encerramento, on="CENA", how="left")
    ranking = classificar_cenarios(ranking)
    ranking["ano_encerramento"] = ano_max
    base = _compactar_indicadores(base)
    ranking = _compactar_indicadores(ranking)
    if "selo" in ranking.columns:
        ranking["selo"] = ranking["selo"].astype("category")
    return base, ranking
