"""Resolucao resiliente de colunas financeiras."""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Iterable

import pandas as pd


def repair_mojibake(text: object) -> str:
    """Tenta desfazer mojibake comum de UTF-8 lido como Latin-1."""
    value = str(text).strip()
    for _ in range(3):
        try:
            repaired = value.encode("latin1").decode("utf-8")
        except (UnicodeEncodeError, UnicodeDecodeError):
            break
        if repaired == value:
            break
        value = repaired
    return value


FRIENDLY_CONTAS: dict[str, str] = {
    "receita": "DRE - Receita",
    "receita bruta": "DRE - Receita",
    "receita liquida": "DRE - Receita",
    "dre receita": "DRE - Receita",
    "ebitda": "DRE - EBITDA",
    "ebitda operacional": "DRE - EBITDA",
    "dre ebitda": "DRE - EBITDA",
    "receita operacional": "DRE - Receita",
    "custos": "DRE - Custos",
    "custo": "DRE - Custos",
    "dre custos": "DRE - Custos",
    "resultado": "DRE - Resultado Líquido",
    "resultado liquido": "DRE - Resultado Líquido",
    "lucro liquido": "DRE - Resultado Líquido",
    "disponivel": "BAL - Disponível",
    "caixa": "BAL - Disponível",
    "ativo circulante": "BAL - Ativo Circulante",
    "passivo circulante": "BAL - Passivo Circulante",
    "total ativo": "BAL - Total do Ativo",
    "total passivo": "BAL - Total do Passivo",
    "estoques": "BAL - Estoques Diversos",
    "fornecedores": "BAL - Fornecedores",
    "emprestimos": "BAL - Empréstimos",
    "patrimonio liquido": "BAL - Patrimônio Líquido",
    "geracao de caixa": "FLU - Geração de Caixa",
    "investimentos": "FLU - Investimentos",
    "capex": "FLU - Investimentos",
    "distribuicao": "FLU - Distribuição para Acionista",
    "saldo final": "FLU - Saldo Final",
    "caixa final": "FLU - Saldo Final",
}


def resolve_account_name(value: object, official_names: Iterable[str] | None = None) -> str:
    """Traduz cabecalhos amigaveis (Receita Bruta, EBITDA) para contas oficiais CTI."""
    bruto = str(value).strip()
    key = normalize_label(bruto)
    candidatos = [key]
    for sufixo in (" r", " rs", " brl", " pct"):
        if key.endswith(sufixo):
            candidatos.append(key[: -len(sufixo)].strip())
    oficiais = {normalize_label(nome): str(nome) for nome in official_names or []}
    amigos = sorted(FRIENDLY_CONTAS.items(), key=lambda item: -len(item[0]))
    for candidato in candidatos:
        if candidato in oficiais:
            return oficiais[candidato]
        if candidato in FRIENDLY_CONTAS:
            return FRIENDLY_CONTAS[candidato]
        for amigo, destino in amigos:
            if candidato == amigo or candidato.startswith(f"{amigo} "):
                return destino
    return bruto


def normalize_label(text: object) -> str:
    """Normaliza texto removendo acentos, simbolos e espacos redundantes."""
    repaired = repair_mojibake(text).casefold()
    ascii_text = unicodedata.normalize("NFKD", repaired).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", " ", ascii_text).strip()


def resolve_column(df: pd.DataFrame, aliases: Iterable[str], *, required: bool = True) -> str | None:
    """Retorna a coluna que corresponde a qualquer alias normalizado."""
    index = {normalize_label(col): col for col in df.columns}
    for alias in aliases:
        key = normalize_label(alias)
        if key in index:
            return str(index[key])
    if required:
        raise KeyError(f"Coluna nao encontrada. Aliases tentados: {list(aliases)}")
    return None


def series_by_alias(df: pd.DataFrame, aliases: Iterable[str], default: float = 0.0) -> pd.Series:
    """Recupera serie numerica por aliases, com fallback constante."""
    col = resolve_column(df, aliases, required=False)
    if col is None:
        return pd.Series(default, index=df.index, dtype="float64")
    return pd.to_numeric(df[col], errors="coerce").fillna(default)
