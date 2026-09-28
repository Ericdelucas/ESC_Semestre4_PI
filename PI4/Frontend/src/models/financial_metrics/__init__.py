"""Compatibilidade publica das metricas financeiras dinamicas."""

from .catalog import FINANCIAL_METRICS_DICT
from .series import contas_necessarias, format_metric_value, metric_timeseries
from .types import FinancialMetric
from .utils import _normalizar_aliases, _safe_div, _to_number

__all__ = [
    "FINANCIAL_METRICS_DICT",
    "FinancialMetric",
    "_normalizar_aliases",
    "_safe_div",
    "_to_number",
    "contas_necessarias",
    "format_metric_value",
    "metric_timeseries",
]
