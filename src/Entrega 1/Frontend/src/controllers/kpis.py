"""Cards de KPI e selos de negócio — métricas nativas com contraste forçado."""

from __future__ import annotations

from html import escape

import numpy as np
import pandas as pd
import streamlit as st

from src.config import COR, CORES_SELO
from src.config.glossary import help_text
from src.config.i18n import t, translate_selo
from src.models.formatting import fmt_dias, fmt_pct, fmt_rs

KpiItem = tuple[str, str, str | None]

# CSS injetado no app (não no HTML isolado) — único jeito de vencer o tema.
_KPI_FORCE_CSS = """
<style>
div[data-testid="stMetricValue"],
div[data-testid="stMetricValue"] > div,
div[data-testid="stMetricValue"] span,
div[data-testid="stMetricValue"] p {
  color: #FFFFFF !important;
  -webkit-text-fill-color: #FFFFFF !important;
  opacity: 1 !important;
  filter: none !important;
  font-weight: 700 !important;
}
div[data-testid="stMetricLabel"],
div[data-testid="stMetricLabel"] > div,
div[data-testid="stMetricLabel"] span,
div[data-testid="stMetricLabel"] p,
div[data-testid="stMetricLabel"] label {
  color: rgba(255, 255, 255, 0.92) !important;
  -webkit-text-fill-color: rgba(255, 255, 255, 0.92) !important;
  opacity: 1 !important;
  filter: none !important;
}
div[data-testid="stMetric"] {
  opacity: 1 !important;
  filter: none !important;
  color: #FFFFFF !important;
  -webkit-text-fill-color: #FFFFFF !important;
}
</style>
"""


def _garantir_css_metricas() -> None:
    if st.session_state.get("_cti_kpi_css_ok"):
        return
    st.markdown(_KPI_FORCE_CSS, unsafe_allow_html=True)
    st.session_state["_cti_kpi_css_ok"] = True


def card_selo_html(nome: str, qtd: int, ativo: bool) -> str:
    cor = CORES_SELO.get(nome, COR)
    borda = "3px solid #111" if ativo else f"1px solid {cor}"
    fundo = f"{cor}22" if not ativo else f"{cor}44"
    rotulo = translate_selo(nome)
    return f"""
<div style="
    border:{borda};
    background:{fundo};
    border-radius:10px;
    padding:0.65rem 0.75rem;
    min-height:4.6rem;
    color:#FFFFFF;
    -webkit-text-fill-color:#FFFFFF;
">
  <div style="font-size:0.78rem;font-weight:700;color:{cor};-webkit-text-fill-color:{cor};line-height:1.25;">{escape(rotulo)}</div>
  <div style="font-size:1.15rem;font-weight:700;margin-top:0.35rem;color:#FFFFFF;-webkit-text-fill-color:#FFFFFF;">{escape(t("map.scenarios_n", n=qtd))}</div>
</div>
"""


def kpis_por_persona(persona: str, k: pd.Series, ranking: pd.DataFrame) -> list[KpiItem]:
    n = ranking.shape[0]
    p_ruina = float((ranking["caixa_ano12"] < 0).mean() * 100) if n else 0.0
    rent = float(ranking["rentabilidade"].mean()) if n and "rentabilidade" in ranking.columns else float("nan")

    if persona == "ceo":
        selo = "—"
        if n and "selo" in ranking.columns and not ranking["selo"].empty:
            selo = str(ranking["selo"].value_counts().index[0])
        return [
            (t("kpi.ruin_prob"), f"{p_ruina:.1f}%", help_text("ruin_prob")),
            (t("kpi.profitability"), fmt_pct(rent) if pd.notna(rent) else "—", help_text("profitability")),
            (t("kpi.selo_top"), translate_selo(selo) if selo != "—" else "—", None),
        ]

    if persona == "cfo":
        liq = k["liquidez"] if "liquidez" in k.index else float("nan")
        return [
            (t("kpi.ncg"), fmt_rs(k["NCG"]) if "NCG" in k.index else "—", help_text("ncg")),
            (
                t("kpi.treasury"),
                fmt_rs(k["Saldo_Tesouraria"]) if "Saldo_Tesouraria" in k.index else "—",
                help_text("treasury"),
            ),
            (
                t("kpi.cycle"),
                fmt_dias(k["Ciclo_Financeiro"]) if "Ciclo_Financeiro" in k.index else "—",
                help_text("cycle"),
            ),
            (
                t("kpi.liquidity"),
                f"{liq:.2f}x" if pd.notna(liq) else "—",
                help_text("liquidity"),
            ),
        ]

    if persona == "acionistas":
        margem = float("nan")
        if (
            "ebitda" in k.index
            and "dre_receita" in k.index
            and pd.notna(k.get("dre_receita"))
            and float(k["dre_receita"]) != 0
        ):
            margem = float(k["ebitda"]) / float(k["dre_receita"])
        elif n and "ebitda" in ranking.columns and "receita" in ranking.columns:
            rec = float(ranking["receita"].mean())
            if rec:
                margem = float(ranking["ebitda"].mean()) / rec
        selo_ret = "—"
        if n and "selo" in ranking.columns and "rentabilidade" in ranking.columns:
            medias = ranking.groupby("selo")["rentabilidade"].mean().sort_values(ascending=False)
            if not medias.empty:
                selo_ret = str(medias.index[0])
        return [
            (t("kpi.ebitda_margin"), fmt_pct(margem) if pd.notna(margem) else "—", None),
            (t("kpi.retorno"), fmt_pct(rent) if pd.notna(rent) else "—", help_text("profitability")),
            (t("kpi.selo_ret"), translate_selo(selo_ret) if selo_ret != "—" else "—", None),
        ]

    # docente
    r2 = float("nan")
    cv = float("nan")
    if n and "ebitda" in ranking.columns and "resultado" in ranking.columns:
        base = ranking[["ebitda", "resultado"]].dropna()
        if len(base) >= 3:
            corr = np.corrcoef(base["ebitda"].to_numpy(), base["resultado"].to_numpy())[0, 1]
            if pd.notna(corr):
                r2 = float(corr**2)
    if n and "caixa_ano12" in ranking.columns:
        serie = ranking["caixa_ano12"].dropna()
        if not serie.empty and float(serie.mean()) != 0:
            cv = float(serie.std(ddof=0) / abs(float(serie.mean())))
    horizonte = int(ranking["ano_encerramento"].iloc[0]) if n and "ano_encerramento" in ranking.columns else 12
    return [
        (t("kpi.n_cenarios"), f"{n:,}", None),
        (t("kpi.horizonte"), str(horizonte), None),
        (t("kpi.r2"), f"{r2:.3f}" if pd.notna(r2) else "—", None),
        (t("kpi.cv_caixa"), f"{cv:.2f}" if pd.notna(cv) else "—", None),
    ]


def render_metric_card(label: str, value: str, dica: str | None = None) -> None:
    """Uma métrica nativa + CSS de contraste; tooltip único via ``help``."""
    _garantir_css_metricas()
    if dica:
        st.metric(label, value, help=dica)
    else:
        st.metric(label, value)


def render_kpi_row(itens: list[KpiItem]) -> None:
    """Linha de KPIs com ``st.metric`` e contraste forçado no Dark Mode."""
    if not itens:
        return
    # Sempre reinjeta o CSS (session flag pode impedir se a página mudou de tema).
    st.markdown(_KPI_FORCE_CSS, unsafe_allow_html=True)
    st.session_state["_cti_kpi_css_ok"] = True
    cols = st.columns(len(itens))
    for col, (rotulo, valor, dica) in zip(cols, itens, strict=True):
        with col:
            if dica:
                st.metric(rotulo, valor, help=dica)
            else:
                st.metric(rotulo, valor)
