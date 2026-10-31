"""Compatibilidade visual para dados financeiros calculados no Backend."""

from __future__ import annotations

import sys
from pathlib import Path


PI4_ROOT = Path(__file__).resolve().parents[4]
if str(PI4_ROOT) not in sys.path:
    sys.path.insert(0, str(PI4_ROOT))

import pandas as pd  # noqa: E402
import streamlit as st  # noqa: E402

from Backend.metrics.financial_kpis import (  # noqa: E402
    ALIQUOTA_IR_FALLBACK,
    PAYOUT,
    WACC,
    _balanco_fluxo,
    _conta,
    build_break_even,
    build_dre,
    build_financial_statement as _financeiro,
    safe_div as _safe_div,
)


@st.cache_data(show_spinner=False)
def _dre_padrao(cena: str) -> pd.DataFrame:
    from src.controllers.bootstrap import carregar_pipeline

    df, _, _ = carregar_pipeline()
    return build_dre(df, cena)


@st.cache_data(show_spinner=False)
def _be_padrao(cena: str) -> pd.DataFrame:
    from src.controllers.bootstrap import carregar_pipeline

    df, _, _ = carregar_pipeline()
    return build_break_even(df, cena)


def _ltv_from_be(be: pd.DataFrame) -> pd.DataFrame:
    """LTV/CAC a partir do Break-Even já cacheado — sem varrer 1M de linhas."""
    dados = be.copy()
    if dados.empty:
        return dados
    margem = None
    for nome in ("Margem de Contribuição (%)", "Margem de Contribuicao (%)"):
        if nome in dados.columns:
            margem = pd.to_numeric(dados[nome], errors="coerce")
            break
    if margem is None:
        margem = pd.Series(0.0, index=dados.index)
    dados["CAC"] = 100.0
    dados["LTV"] = 4_500.0 * margem.fillna(0.0) * 10.0
    dados["LTV/CAC"] = dados["LTV"] / pd.to_numeric(dados["CAC"], errors="coerce").replace(0, pd.NA)
    return dados


@st.cache_data(show_spinner=False)
def _ltv_padrao(cena: str) -> pd.DataFrame:
    return _ltv_from_be(_be_padrao(cena))


def _dre(df: pd.DataFrame, cena: str) -> pd.DataFrame:
    from src.controllers.data_input import has_custom_data

    if not has_custom_data():
        return _dre_padrao(str(cena))
    return build_dre(df, cena)


def _break_even_df(df: pd.DataFrame, cena: str) -> pd.DataFrame:
    from src.controllers.data_input import has_custom_data

    if not has_custom_data():
        return _be_padrao(str(cena))
    return build_break_even(df, cena)


def _ltv_df(df: pd.DataFrame, cena: str) -> pd.DataFrame:
    from src.controllers.data_input import has_custom_data

    if not has_custom_data():
        return _ltv_padrao(str(cena))
    return _ltv_from_be(_break_even_df(df, cena))

__all__ = [
    "ALIQUOTA_IR_FALLBACK",
    "PAYOUT",
    "WACC",
    "_break_even_df",
    "_balanco_fluxo",
    "_conta",
    "_dre",
    "_financeiro",
    "_ltv_df",
    "_safe_div",
]
