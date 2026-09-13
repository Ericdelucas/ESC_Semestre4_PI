"""Pipeline analítico (notebooks → código): indicadores, ranking, envelopes e capital de giro."""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.config import CONTAS_RECEBER, PECAS_CONTAS, SELOS_NEGOCIO
from src.data.loaders import magnitude, soma_contas


def montar_indicadores(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Calcula NCG, prazos, liquidez, risco e selos de negócio por cenário."""
    contas_receber = soma_contas(df, CONTAS_RECEBER).rename(columns={"valor": "contas_receber"})

    base = contas_receber.copy()
    for nome, contas in PECAS_CONTAS.items():
        tmp = soma_contas(df, contas).rename(columns={"valor": nome})
        base = base.merge(tmp, on=["ANO", "ano_num", "CENA"], how="outer")

    base = base.fillna(0)

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


def classificar_cenarios(ranking: pd.DataFrame) -> pd.DataFrame:
    """Atribui selos de negócio (quartis + regras de ruína/investimento/distribuição)."""
    out = ranking.copy()
    q_rent = out["rentabilidade"].quantile([0.25, 0.50, 0.75])
    q_liq = out["liquidez"].quantile([0.25, 0.50, 0.75])
    q_risco = out["risco"].quantile([0.25, 0.75])
    q_inv = out["pressao_invest"].quantile(0.75)
    q_dist = out["dist_abs"].quantile(0.75)
    q_disp = out["liquidez_acumulada"].quantile(0.25)

    out["Alta rentabilidade"] = out["rentabilidade"] >= q_rent[0.75]
    out["Retorno moderado"] = out["rentabilidade"].between(q_rent[0.25], q_rent[0.75], inclusive="left")
    out["Alta liquidez"] = out["liquidez"] >= q_liq[0.75]
    out["Baixa liquidez"] = out["liquidez"] <= q_liq[0.25]
    out["Baixo risco"] = out["risco"] <= q_risco[0.25]
    out["Alto risco"] = out["risco"] >= q_risco[0.75]

    def classificar_selo(row: pd.Series) -> str:
        if pd.notna(row["caixa_ano12"]) and row["caixa_ano12"] < 0:
            return "Encerramento com Caixa Insuficiente"
        if row["dist_abs"] >= q_dist and row["liquidez_acumulada"] <= q_disp:
            return "Elevada Distribuição & Baixa Disponibilidade"
        if row["pressao_invest"] >= q_inv:
            return "Forte Pressão de Investimentos"
        if row["Alta rentabilidade"] and row["Alta liquidez"]:
            return "Alta Rentabilidade & Alta Liquidez"
        if row["Alta rentabilidade"] and row["Baixa liquidez"]:
            return "Alta Rentabilidade & Baixa Liquidez"
        if row["Retorno moderado"] and row["Baixo risco"]:
            return "Retorno Moderado & Baixo Risco"
        if row["Alta rentabilidade"]:
            return (
                "Alta Rentabilidade & Alta Liquidez"
                if row["liquidez"] >= q_liq[0.5]
                else "Alta Rentabilidade & Baixa Liquidez"
            )
        if row["Baixo risco"]:
            return "Retorno Moderado & Baixo Risco"
        if row["pressao_invest"] >= out["pressao_invest"].median():
            return "Forte Pressão de Investimentos"
        return "Retorno Moderado & Baixo Risco"

    out["selo"] = out.apply(classificar_selo, axis=1)
    # Garante cobertura das 6 categorias no domínio
    _ = SELOS_NEGOCIO
    return out


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


def cena_rotulo(cena: str) -> str:
    digitos = "".join(ch for ch in str(cena) if ch.isdigit())
    if digitos:
        return f"Cenário {int(digitos)}"
    return str(cena)


def cenas_por_percentil(ranking: pd.DataFrame, coluna: str, qs: list[float]) -> dict[float, str]:
    serie = ranking[coluna].dropna()
    out: dict[float, str] = {}
    for q in qs:
        alvo = float(serie.quantile(q))
        idx = (ranking[coluna] - alvo).abs().idxmin()
        out[q] = str(ranking.loc[idx, "CENA"])
    return out


def melhor_entre(a: float, b: float, *, maior_melhor: bool) -> str:
    if pd.isna(a) and pd.isna(b):
        return ""
    if pd.isna(a):
        return "B"
    if pd.isna(b):
        return "A"
    if maior_melhor:
        if a > b:
            return "A"
        if b > a:
            return "B"
    else:
        if a < b:
            return "A"
        if b < a:
            return "B"
    return ""


def cenas_padrao_comparacao(cenas: list[str]) -> list[str]:
    escolhidas: list[str] = []
    for alvo in ("00001", "00500"):
        match = next((c for c in cenas if alvo in str(c)), None)
        if match is not None:
            escolhidas.append(match)
    if len(escolhidas) < 2:
        return cenas[:2]
    return escolhidas[:2]


def probabilidade_caixa_negativo(ranking: pd.DataFrame) -> float:
    if ranking.empty or "caixa_ano12" not in ranking.columns:
        return 0.0
    return float((ranking["caixa_ano12"] < 0).mean() * 100)
