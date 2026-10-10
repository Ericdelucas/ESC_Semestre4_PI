"""Construcao do contexto do recorte em foco."""

from __future__ import annotations

import pandas as pd

from .formatters import dias, pct, rs


def serie_val(k: pd.Series | None, col: str) -> float:
    if k is None or col not in k.index:
        return float("nan")
    try:
        return float(k[col])
    except (TypeError, ValueError):
        return float("nan")


def build_focus_context(
    ranking: pd.DataFrame,
    *,
    cena_sel: str,
    n_cenarios: int,
    p_ruina: float,
    ano_enc: int,
    k: pd.Series | None = None,
    ano_sel: str | int = "Todos",
    lang: str = "pt",
) -> str:
    """Texto de contexto do cenario/recorte em foco (NCG, tesouraria e riscos)."""
    en = lang == "en"
    recorte_todos = str(ano_sel) in {"Todos", "All", "__all__"}
    if recorte_todos:
        recorte = "all years in the horizon" if en else "todos os anos do horizonte"
    else:
        recorte = f"Year {ano_sel}" if en else f"Ano {ano_sel}"

    ncg = serie_val(k, "NCG")
    tes = serie_val(k, "Saldo_Tesouraria")
    ciclo = serie_val(k, "Ciclo_Financeiro")
    liq = serie_val(k, "liquidez")
    rent = serie_val(k, "rentabilidade")
    risco = serie_val(k, "risco")
    liq_txt = f"{liq:.2f}x" if pd.notna(liq) else "—"

    if en:
        linhas = [
            f"Dashboard focus: scenario {cena_sel}; slice {recorte}; "
            f"{n_cenarios} simulated scenarios; probability of negative cash in Year {ano_enc}: {p_ruina:.1f}%.",
            "Filtered-slice indicators (NWC / Treasury / Risk): "
            f"NWC {rs(ncg)}; treasury balance {rs(tes)}; cash cycle {dias(ciclo)}; "
            f"current liquidity {liq_txt}; profitability {pct(rent)}; risk {pct(risco)}.",
        ]
    else:
        linhas = [
            f"Foco atual do painel: cenário {cena_sel}; recorte {recorte}; "
            f"{n_cenarios} cenários simulados; prob. de caixa negativo no Ano {ano_enc}: {p_ruina:.1f}%.",
            "Indicadores do recorte filtrado (NCG / Tesouraria / Riscos): "
            f"NCG {rs(ncg)}; saldo de tesouraria {rs(tes)}; ciclo financeiro {dias(ciclo)}; "
            f"liquidez corrente {liq_txt}; rentabilidade {pct(rent)}; risco {pct(risco)}.",
        ]

    from src.models.formatting.scenarios import is_all_scenarios

    if "CENA" not in ranking.columns:
        bloco = ranking.iloc[0:0]
    elif is_all_scenarios(cena_sel):
        bloco = ranking
    else:
        bloco = ranking.loc[ranking["CENA"] == cena_sel]
    if not bloco.empty:
        row = bloco.mean(numeric_only=True) if is_all_scenarios(cena_sel) else bloco.iloc[0]
        selo = "—" if is_all_scenarios(cena_sel) else (row["selo"] if "selo" in bloco.columns else "—")
        caixa = row["caixa_ano12"] if "caixa_ano12" in getattr(row, "index", bloco.columns) else float("nan")
        if en:
            linhas.append(
                f"Focus scenario row: badge {selo}; Year-12 cash {rs(float(caixa)) if pd.notna(caixa) else '—'}; "
                f"NWC {rs(float(row['NCG'])) if 'NCG' in bloco.columns else '—'}; "
                f"treasury {rs(float(row['Saldo_Tesouraria'])) if 'Saldo_Tesouraria' in bloco.columns else '—'}."
            )
        else:
            linhas.append(
                f"Linha do cenário em foco: selo {selo}; caixa Ano 12 {rs(float(caixa)) if pd.notna(caixa) else '—'}; "
                f"NCG {rs(float(row['NCG'])) if 'NCG' in bloco.columns else '—'}; "
                f"tesouraria {rs(float(row['Saldo_Tesouraria'])) if 'Saldo_Tesouraria' in bloco.columns else '—'}."
            )
    return "\n".join(linhas)
