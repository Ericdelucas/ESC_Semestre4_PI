"""KPIs da visao do poder concedente."""

from __future__ import annotations

import pandas as pd

from src.models.formatting import fmt_rs

from .constants import (
    CONTA_ATIVO_CIRCULANTE,
    CONTA_EXIGIVEL_LP,
    CONTA_FLU_INVESTIMENTOS,
    CONTA_PASSIVO_CIRCULANTE,
    CONTA_REALIZAVEL_LP,
    CONTA_TOTAL_ATIVO,
    KpiItem,
)
from .helpers import _safe_div, _valor_conta_raw


def _kpis_poder_concedente(df: pd.DataFrame | None, cena: str | None, ano_sel: str | int) -> list[KpiItem]:
    investimentos = abs(_valor_conta_raw(df, cena, CONTA_FLU_INVESTIMENTOS, ano_sel))
    ativo_circ = abs(_valor_conta_raw(df, cena, CONTA_ATIVO_CIRCULANTE, ano_sel))
    realizavel_lp = abs(_valor_conta_raw(df, cena, CONTA_REALIZAVEL_LP, ano_sel))
    passivo_circ = abs(_valor_conta_raw(df, cena, CONTA_PASSIVO_CIRCULANTE, ano_sel))
    exigivel_lp = abs(_valor_conta_raw(df, cena, CONTA_EXIGIVEL_LP, ano_sel))
    ativo_total = abs(_valor_conta_raw(df, cena, CONTA_TOTAL_ATIVO, ano_sel))

    liquidez_geral = _safe_div(ativo_circ + realizavel_lp, passivo_circ + exigivel_lp)

    return [
        (
            "CAPEX Investido (Infraestrutura)",
            fmt_rs(investimentos),
            "Investimento acumulado na concessão de serviço público",
            None,
        ),
        (
            "Liquidez Geral (Solvência de Longo Prazo)",
            f"{liquidez_geral:.2f}x" if pd.notna(liquidez_geral) else "—",
            "Capacidade de cumprir obrigações contratuais até o fim da concessão",
            None,
        ),
        (
            "Base de Ativos Reversíveis (Ativo Total)",
            fmt_rs(ativo_total),
            "Patrimônio total afetado à prestação do serviço público",
            None,
        ),
    ]
