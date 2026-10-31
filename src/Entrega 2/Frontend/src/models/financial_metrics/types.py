"""Tipos compartilhados das metricas financeiras."""

from __future__ import annotations

from collections.abc import Callable
from typing import TypedDict

import pandas as pd


class FinancialMetric(TypedDict):
    categoria: str
    nome: str
    formula: Callable[[pd.DataFrame], pd.Series]
    format: str
