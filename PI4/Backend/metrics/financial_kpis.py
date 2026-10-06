"""Calculo de indicadores financeiros e regras de negocio CTI."""

from __future__ import annotations

import numpy as np
import pandas as pd

from Backend.data_loader import magnitude
from Backend.metrics.column_resolver import normalize_label


WACC = 0.10
PAYOUT = 0.35
ALIQUOTA_IR_FALLBACK = 0.34

CONTAS_RECEBER = [
    "BAL - Contas a Receber - Clientes",
    "BAL - Contas a Receber - Partes Relacionadas",
    "BAL - Contas a Receber - SWAP",
]

PECAS_CONTAS: dict[str, list[str]] = {
    "estoques": ["BAL - Estoques Diversos"],
    "creditos_tributarios": ["BAL - CrÃ©ditos TributÃ¡rios"],
    "fornecedores": ["BAL - Fornecedores"],
    "encargos_sociais": ["BAL - Encargos Sociais e Trabalhistas"],
    "tributos_a_pagar": ["BAL - Tributos a pagar"],
    "disponivel": ["BAL - DisponÃ­vel"],
    "emprestimos_cp": ["BAL - EmprÃ©stimos"],
    "ativo_circ": ["BAL - Ativo Circulante"],
    "passivo_circ": ["BAL - Passivo Circulante"],
    "total_ativo": ["BAL - Total do Ativo"],
    "total_passivo": ["BAL - Total do Passivo"],
    "dre_receita": ["DRE - Receita"],
    "dre_custos": ["DRE - Custos"],
    "resultado": ["DRE - Resultado LÃ­quido"],
    "ebitda": ["DRE - EBITDA"],
    "geracao_caixa": ["FLU - GeraÃ§Ã£o de Caixa"],
    "investimentos": ["FLU - Investimentos"],
    "distribuicao": ["FLU - DistribuiÃ§Ã£o para Acionista"],
    "saldo_final": ["FLU - Saldo Final"],
}

RECORTE_KPI_COLUMNS = [
    "NCG",
    "Saldo_Tesouraria",
    "Ciclo_Financeiro",
    "PMR",
    "PME",
    "PMP",
    "liquidez",
    "rentabilidade",
    "risco",
    "resultado",
    "ebitda",
    "dre_receita",
    "dre_custos",
    "investimentos",
    "total_ativo",
    "total_passivo",
]


def safe_div(num: float | pd.Series, den: float | pd.Series) -> float | pd.Series:
    """Divide evitando divisao por zero."""
    if isinstance(num, pd.Series) or isinstance(den, pd.Series):
        index = num.index if isinstance(num, pd.Series) else den.index
        numerador = pd.to_numeric(num, errors="coerce")
        denominador = pd.to_numeric(den, errors="coerce")
        if not isinstance(numerador, pd.Series):
            numerador = pd.Series(numerador, index=index)
        if not isinstance(denominador, pd.Series):
            denominador = pd.Series(denominador, index=index)
        return numerador / denominador.replace(0, pd.NA)
    return float("nan") if pd.isna(den) or float(den) == 0 else num / den


def compactar_indicadores(df: pd.DataFrame) -> pd.DataFrame:
    """Compacta DataFrames derivados para memoria reduzida."""
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


def mapa_contas() -> dict[str, str]:
    """Mapeia conta original para coluna canonica."""
    mapa: dict[str, str] = {conta: "contas_receber" for conta in CONTAS_RECEBER}
    for nome, contas in PECAS_CONTAS.items():
        for conta in contas:
            mapa[conta] = nome
    return mapa


def classificar_cenarios(ranking: pd.DataFrame) -> pd.DataFrame:
    """Classifica cenarios por risco, liquidez e retorno."""
    out = ranking.copy()
    q_rent = out["rentabilidade"].quantile([0.25, 0.50, 0.75])
    q_liq = out["liquidez"].quantile([0.25, 0.50, 0.75])
    q_risco = out["risco"].quantile([0.25, 0.75])
    q_invest = float(out["pressao_invest"].quantile(0.75))
    q_dist = float(out["dist_abs"].quantile(0.75))
    q_disp = float(out["liquidez_acumulada"].quantile(0.25))

    alta_rent = out["rentabilidade"] >= q_rent[0.75]
    retorno_moderado = out["rentabilidade"].between(q_rent[0.25], q_rent[0.75], inclusive="left")
    alta_liq = out["liquidez"] >= q_liq[0.75]
    baixa_liq = out["liquidez"] <= q_liq[0.25]
    baixo_risco = out["risco"] <= q_risco[0.25]
    investimento_alto = out["pressao_invest"] >= q_invest
    distribuicao_alta = (out["dist_abs"] >= q_dist) & (out["liquidez_acumulada"] <= q_disp)
    caixa_negativo = out["caixa_ano12"] < 0

    condicoes = [
        caixa_negativo,
        investimento_alto,
        distribuicao_alta,
        alta_rent & alta_liq,
        alta_rent & baixa_liq,
        retorno_moderado & baixo_risco,
        alta_rent & (out["liquidez"] >= q_liq[0.5]),
        alta_rent & (out["liquidez"] < q_liq[0.5]),
        baixo_risco,
    ]
    escolhas = [
        "Encerramento com Caixa Insuficiente",
        "Forte PressÃ£o de Investimentos",
        "Elevada DistribuiÃ§Ã£o & Baixa Disponibilidade",
        "Alta Rentabilidade & Alta Liquidez",
        "Alta Rentabilidade & Baixa Liquidez",
        "Retorno Moderado & Baixo Risco",
        "Alta Rentabilidade & Alta Liquidez",
        "Alta Rentabilidade & Baixa Liquidez",
        "Retorno Moderado & Baixo Risco",
    ]
    out["selo"] = np.select(condicoes, escolhas, default="Retorno Moderado & Baixo Risco")
    return out


def montar_indicadores(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Calcula NCG, prazos, liquidez, risco e ranking de cenarios."""
    mapa = mapa_contas()
    slim = df.loc[df["CONTA"].isin(set(mapa)), ["ANO", "ano_num", "CENA", "CONTA", "VALOR"]].copy()
    slim["campo"] = slim["CONTA"].map(mapa)
    wide = (
        slim.groupby(["ANO", "ano_num", "CENA", "campo"], as_index=False, observed=True)["VALOR"]
        .sum()
        .pivot(index=["ANO", "ano_num", "CENA"], columns="campo", values="VALOR")
        .reset_index()
    )
    wide.columns.name = None
    metric_cols = [col for col in wide.columns if col not in {"ANO", "ano_num", "CENA"}]
    if metric_cols:
        wide[metric_cols] = wide[metric_cols].fillna(0)
    for col in set(mapa.values()):
        if col not in wide.columns:
            wide[col] = 0.0

    base = wide
    base["ACO"] = magnitude(base["contas_receber"]) + magnitude(base["estoques"]) + magnitude(base["creditos_tributarios"])
    base["PCO"] = magnitude(base["fornecedores"] + base["encargos_sociais"] + base["tributos_a_pagar"])
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
    base["caixa_final_sinal"] = np.where(base["saldo_final"].abs() > 1e-9, base["saldo_final"], base["disponivel"])

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
    if "selo" in ranking.columns:
        ranking["selo"] = ranking["selo"].astype("category")
    return compactar_indicadores(base), compactar_indicadores(ranking)


def probabilidade_caixa_negativo(ranking: pd.DataFrame) -> float:
    """Calcula percentual de cenarios com caixa final negativo."""
    if ranking.empty or "caixa_ano12" not in ranking.columns:
        return 0.0
    return float((pd.to_numeric(ranking["caixa_ano12"], errors="coerce") < 0).mean() * 100)


def calcular_kpis_recorte(foco: pd.DataFrame, foco_ano: pd.DataFrame) -> pd.Series:
    """Calcula medias de KPIs para o recorte ja filtrado no backend."""
    base = foco_ano if not foco_ano.empty else foco
    presentes = [col for col in RECORTE_KPI_COLUMNS if col in base.columns]
    return base[presentes].mean(numeric_only=True) if presentes else pd.Series(dtype=float)


def _wide(df: pd.DataFrame, cena: str, contas: list[str]) -> pd.DataFrame:
    conta_keys = {normalize_label(conta): conta for conta in contas}
    source = df.loc[df["CENA"] == cena, ["ano_num", "CONTA", "VALOR"]].copy()
    source["CONTA"] = source["CONTA"].map(lambda value: conta_keys.get(normalize_label(value)))
    base = source.loc[source["CONTA"].notna()].copy()
    if base.empty:
        return pd.DataFrame(columns=["ano_num", *contas])
    base["ano_num"] = pd.to_numeric(base["ano_num"], errors="coerce")
    base["VALOR"] = pd.to_numeric(base["VALOR"], errors="coerce")
    out = (
        base.groupby(["ano_num", "CONTA"], as_index=False)["VALOR"]
        .sum()
        .pivot(index="ano_num", columns="CONTA", values="VALOR")
        .reset_index()
        .sort_values("ano_num")
    )
    out.columns.name = None
    for conta in contas:
        if conta not in out.columns:
            out[conta] = 0.0
    out["ano_num"] = out["ano_num"].astype(int)
    return out


def _conta(dados: pd.DataFrame, nome: str) -> pd.Series:
    return pd.to_numeric(dados.get(nome, 0.0), errors="coerce").fillna(0.0)


def _conta_alias(dados: pd.DataFrame, *nomes: str) -> pd.Series:
    index = {normalize_label(col): col for col in dados.columns}
    for nome in nomes:
        col = index.get(normalize_label(nome))
        if col is not None:
            return pd.to_numeric(dados[col], errors="coerce").fillna(0.0)
    return pd.Series(0.0, index=dados.index, dtype="float64")


def build_dre(df: pd.DataFrame, cena: str) -> pd.DataFrame:
    """Monta DRE derivada para um cenario."""
    contas = [
        "DRE - Receita",
        "DRE - Tributos",
        "DRE - Custos",
        "DRE - Depreciação e Amortização",
        "DRE - Resultado Operacional",
        "DRE - Resultado Financeiro",
        "DRE - Despesas Financeiras",
        "DRE - Outros Resultados Operacionais",
        "DRE - Resultado Antes do Imposto de Renda",
        "DRE - Imposto de Renda e Contribuição Social",
        "DRE - Resultado Líquido",
        "DRE - EBITDA",
    ]
    dados = _wide(df, cena, contas)
    if dados.empty:
        return dados
    receita = _conta_alias(dados, "DRE - Receita")
    tributos = _conta_alias(dados, "DRE - Tributos")
    custos = _conta_alias(dados, "DRE - Custos")
    ebitda = _conta_alias(dados, "DRE - EBITDA")
    resultado_financeiro = _conta_alias(dados, "DRE - Resultado Financeiro")
    ir_cs = _conta_alias(dados, "DRE - Imposto de Renda e Contribuição Social")
    lucro_informado = _conta_alias(dados, "DRE - Resultado Líquido")

    dados["Receita Líquida"] = receita + tributos
    dados["Margem Bruta"] = dados["Receita Líquida"] + custos
    dados["OPEX"] = ebitda - dados["Margem Bruta"]
    dados["EBITDA"] = ebitda
    dados["EBIT"] = _conta_alias(dados, "DRE - Resultado Operacional")
    dados["Resultado Financeiro"] = resultado_financeiro
    dados["EBT"] = _conta_alias(dados, "DRE - Resultado Antes do Imposto de Renda")
    lucro_derivado = dados["EBIT"] + resultado_financeiro + ir_cs
    dados["Lucro Líquido"] = lucro_informado.where(lucro_informado.abs() > 1e-9, lucro_derivado)
    dados["Custos"] = custos
    dados["Depreciação"] = _conta_alias(dados, "DRE - Depreciação e Amortização")
    dados["Outros Operacionais"] = _conta_alias(dados, "DRE - Outros Resultados Operacionais")
    dados["Despesas Financeiras"] = _conta_alias(dados, "DRE - Despesas Financeiras")
    return dados
def _balanco_fluxo(df: pd.DataFrame, cena: str) -> pd.DataFrame:
    contas = [
        "BAL - Total do Ativo",
        "BAL - Total do Passivo",
        "BAL - Ativo Circulante",
        "BAL - Passivo Circulante",
        "BAL - RealizÃ¡vel a Longo Prazo",
        "BAL - ExigÃ­vel a Longo Prazo",
        "BAL - PatrimÃ´nio LÃ­quido",
        "BAL - EmprÃ©stimos",
        "BAL - DisponÃ­vel",
        "BAL - Investimentos - Imobilizado",
        "BAL - Investimentos - IntangÃ­vel",
        "BAL - DepreciaÃ§Ã£o Acumulada",
        "BAL - AmortizaÃ§Ã£o Acumulada",
        "FLU - Investimentos",
        "FLU - DistribuiÃ§Ã£o para Acionista",
    ]
    return _wide(df, cena, contas)


def build_financial_statement(df: pd.DataFrame, cena: str) -> pd.DataFrame:
    """Calcula ROIC, EVA, dividendos e estrutura de capital."""
    dre = build_dre(df, cena)
    bal = _balanco_fluxo(df, cena)
    dados = dre.merge(bal, on="ano_num", how="outer").sort_values("ano_num").fillna(0.0)
    patrimonio = _conta(dados, "BAL - PatrimÃ´nio LÃ­quido").abs()
    divida = _conta(dados, "BAL - EmprÃ©stimos").abs()
    caixa = _conta(dados, "BAL - DisponÃ­vel").abs()
    ativo_total = _conta(dados, "BAL - Total do Ativo").abs()
    divida_liquida = (divida - caixa).clip(lower=0)
    capital_base = patrimonio + divida_liquida
    capital = capital_base.where(capital_base > 0, ativo_total)
    ir_cs = _conta_alias(dados, "DRE - Imposto de Renda e Contribuição Social")
    aliquota_ir = safe_div(ir_cs.abs(), dados["EBIT"].abs()).clip(lower=0, upper=ALIQUOTA_IR_FALLBACK).fillna(ALIQUOTA_IR_FALLBACK)
    nopat = dados["EBIT"] * (1 - aliquota_ir)
    lucro = dados["Lucro Líquido"]
    capital_divisor = capital.replace(0, pd.NA)
    dados["DÃ­vida LÃ­quida"] = divida_liquida
    dados["Capital Investido"] = capital.fillna(0)
    dados["NOPAT"] = nopat
    dados["ROIC"] = safe_div(nopat, capital_divisor).fillna(0)
    dados["ROE"] = safe_div(lucro, patrimonio.replace(0, pd.NA)).fillna(0)
    dados["WACC"] = WACC
    dados["Custo do Capital"] = capital.fillna(0) * WACC
    dados["EVA"] = (nopat - dados["Custo do Capital"]).fillna(0)
    dados["Dividendos"] = (lucro.clip(lower=0) * PAYOUT).fillna(0)
    dados["Retido"] = (lucro.clip(lower=0) - dados["Dividendos"]).fillna(0)
    dados["DY"] = safe_div(dados["Dividendos"], capital_divisor).fillna(0)
    return dados


def build_break_even(df: pd.DataFrame, cena: str) -> pd.DataFrame:
    """Calcula break-even e margem de seguranca por ano."""
    dados = build_dre(df, cena)
    if dados.empty:
        return dados
    receita = dados["Receita Líquida"].replace(0, pd.NA)
    custos_variaveis = dados["Custos"].abs()
    custos_fixos = dados["Outros Operacionais"].abs() + dados["Depreciação"].abs() + dados["Despesas Financeiras"].abs()
    margem_contrib = (dados["Receita Líquida"] - custos_variaveis) / receita
    dados["Custos Fixos"] = custos_fixos
    dados["Margem de Contribuição (%)"] = margem_contrib
    dados["Break-Even"] = custos_fixos / margem_contrib.replace(0, pd.NA)
    dados["Margem de Segurança (%)"] = (dados["Receita Líquida"] - dados["Break-Even"]) / receita
    return dados

