"""Renderizacao de tabelas nativas com formato numerico PT/EN."""

from __future__ import annotations

import re

import pandas as pd
import streamlit as st

from src.config.i18n import get_lang

_MONEY_HINTS = (
    "valor",
    "receita",
    "custo",
    "opex",
    "ebitda",
    "ebit",
    "lucro",
    "caixa",
    "ncg",
    "tesouraria",
    "capex",
    "dividendo",
    "retido",
    "eva",
    "disponivel",
    "investimento",
)
_PCT_HINTS = ("%", "margem", "yoy", "rentabilidade", "dy", "roic", "roe", "wacc")
_RATIO_HINTS = ("liquidez", "cobertura", "endividamento", "ltv", "cac")

def _is_numeric(series: pd.Series) -> bool:
    return pd.api.types.is_numeric_dtype(series)


def _normalize(nome: str) -> str:
    return str(nome).strip().lower()


def _money_format() -> str:
    return "R$ %,.2f"


def _pct_format() -> str:
    return "%.2f%%"


def _ratio_format() -> str:
    return "%.2fx"


def infer_column_kind(nome: str) -> str | None:
    n = _normalize(nome)
    if n in {"ano", "ano_num", "year"} or n.startswith("ano "):
        return "year"
    if any(h in n for h in _PCT_HINTS):
        return "pct"
    if any(h in n for h in _RATIO_HINTS):
        return "ratio"
    if any(h in n for h in _MONEY_HINTS):
        return "money"
    return None


def dataframe_column_config(df: pd.DataFrame) -> dict[str, object]:
    config: dict[str, object] = {}
    for col in df.columns:
        serie = df[col]
        kind = infer_column_kind(str(col))
        if kind == "year" and _is_numeric(serie):
            config[col] = st.column_config.NumberColumn(str(col), format="%d", step=1)
            continue
        if not _is_numeric(serie):
            continue
        if kind == "pct":
            config[col] = st.column_config.NumberColumn(str(col), format=_pct_format())
        elif kind == "ratio":
            config[col] = st.column_config.NumberColumn(str(col), format=_ratio_format())
        elif kind == "money":
            config[col] = st.column_config.NumberColumn(str(col), format=_money_format())
        else:
            config[col] = st.column_config.NumberColumn(str(col), format="%,.2f")
    _ = get_lang()
    return config


def render_table(df: pd.DataFrame, *, hide_index: bool = True) -> None:
    visao = df.copy()
    st.dataframe(
        visao,
        width="stretch",
        hide_index=hide_index,
        column_config=dataframe_column_config(visao),
    )


def parse_markdown_table(bloco: str) -> pd.DataFrame | None:
    linhas = [ln.strip() for ln in bloco.strip().splitlines() if ln.strip().startswith("|")]
    if len(linhas) < 2:
        return None
    def split_row(linha: str) -> list[str]:
        return [c.strip() for c in linha.strip("|").split("|")]

    cabecalho = split_row(linhas[0])
    corpo = []
    for linha in linhas[1:]:
        if re.match(r"^\s*\|?\s*:?-{2,}", linha):
            continue
        corpo.append(split_row(linha))
    if not cabecalho:
        return None
    n = len(cabecalho)
    linhas_ok = [row + [""] * (n - len(row)) for row in corpo if any(row)]
    linhas_ok = [row[:n] for row in linhas_ok]
    tabela = pd.DataFrame(linhas_ok, columns=cabecalho)
    for col in tabela.columns:
        convertida = pd.to_numeric(
            tabela[col].astype(str).str.replace("%", "", regex=False).str.replace("R$", "", regex=False).str.replace(".", "", regex=False).str.replace(",", ".", regex=False),
            errors="ignore",
        )
        if pd.api.types.is_numeric_dtype(convertida):
            tabela[col] = convertida
    return tabela


_TABLE_BLOCK = re.compile(r"(?:^[ \t]*\|.+\|[ \t]*$\n?){2,}", re.MULTILINE)


def render_markdown_with_tables(texto: str) -> None:
    """Renderiza markdown e converte tabelas GFM em st.dataframe sem quebrar o layout."""
    if not texto:
        return
    cursor = 0
    encontrou = False
    for match in _TABLE_BLOCK.finditer(texto):
        prefixo = texto[cursor:match.start()]
        if prefixo.strip():
            st.markdown(prefixo)
        tabela = parse_markdown_table(match.group(0))
        if tabela is not None and not tabela.empty:
            render_table(tabela)
            encontrou = True
        else:
            st.markdown(match.group(0))
        cursor = match.end()
    resto = texto[cursor:]
    if resto.strip() or not encontrou:
        if resto.strip() or cursor == 0:
            st.markdown(texto if cursor == 0 else resto)
