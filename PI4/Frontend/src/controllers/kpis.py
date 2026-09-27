"""Cards de KPI e selos de negocio com metricas nativas do Streamlit."""

from __future__ import annotations

from html import escape
from typing import TypeAlias

import pandas as pd
import streamlit as st

from src.config import COR, CORES_SELO
from src.config.glossary import help_text
from src.config.i18n import t, translate_selo
from src.models.formatting import fmt_dias, fmt_pct, fmt_rs

KpiItem: TypeAlias = tuple[str, str, str | None] | tuple[str, str, str | None, str | None]

CONTA_EBITDA = "DRE - EBITDA"
CONTA_RECEITA = "DRE - Receita"
CONTA_TRIBUTOS = "DRE - Tributos"
CONTA_CUSTOS = "DRE - Custos"
CONTA_OUTROS_RESULTADOS = "DRE - Outros Resultados Operacionais"
CONTA_RESULTADO_OPERACIONAL = "DRE - Resultado Operacional"
CONTA_IR_CS = "DRE - Imposto de Renda e Contribuição Social"
CONTA_RESULTADO_LIQUIDO = "DRE - Resultado Líquido"
CONTA_FLU_INVESTIMENTOS = "FLU - Investimentos"
CONTA_PATRIMONIO_LIQUIDO = "BAL  - Patrimônio Líquido"
CONTA_EMPRESTIMOS = "BAL - Empréstimos"
CONTA_DISPONIVEL = "BAL - Disponível"
CONTA_ATIVO_CIRCULANTE = "BAL - Ativo Circulante"
CONTA_PASSIVO_CIRCULANTE = "BAL - Passivo Circulante"
CONTA_REALIZAVEL_LP = "BAL - Realizável a Longo Prazo"
CONTA_EXIGIVEL_LP = "BAL - Exigível a Longo Prazo"
CONTA_TOTAL_ATIVO = "BAL - Total do Ativo"

WACC_FALLBACK = 0.10
ALIQUOTA_IR_FALLBACK = 0.34

CEO_LTV_CAC_FALLBACK = {
    "Investimento em Vendas e Mkt (R$)": 100_000.0,
    "Novos Clientes Adquiridos (un)": 1_000.0,
    "Ticket Médio (R$)": 4_500.0,
    "Tempo Médio de Retenção (Meses)": 10.0,
}

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


def _safe_div(numerador: float, denominador: float) -> float:
    if pd.isna(numerador) or pd.isna(denominador) or float(denominador) == 0:
        return float("nan")
    return float(numerador) / float(denominador)


def _valor_conta_raw(df: pd.DataFrame | None, cena: str | None, conta: str, ano_sel: str | int) -> float:
    if df is None or cena is None or df.empty:
        return float("nan")
    recorte = df.loc[(df["CENA"] == cena) & (df["CONTA"] == conta)]
    if ano_sel != "Todos":
        recorte = recorte.loc[pd.to_numeric(recorte["ano_num"], errors="coerce") == int(ano_sel)]
    if recorte.empty:
        return float("nan")
    return float(pd.to_numeric(recorte["VALOR"], errors="coerce").mean())


def _valor_premissa_comercial(
    df: pd.DataFrame | None,
    cena: str | None,
    nomes: list[str],
    ano_sel: str | int,
    fallback: float,
) -> float:
    if df is None or cena is None or df.empty:
        return fallback
    recorte = df.loc[(df["CENA"] == cena) & (df["CONTA"].isin(nomes))]
    if ano_sel != "Todos":
        recorte = recorte.loc[pd.to_numeric(recorte["ano_num"], errors="coerce") == int(ano_sel)]
    if recorte.empty:
        return fallback
    valor = float(pd.to_numeric(recorte["VALOR"], errors="coerce").mean())
    return valor if pd.notna(valor) else fallback


def _kpis_ceo(df: pd.DataFrame | None, cena: str | None, ano_sel: str | int) -> list[KpiItem]:
    receita = _valor_conta_raw(df, cena, CONTA_RECEITA, ano_sel)
    ebitda = _valor_conta_raw(df, cena, CONTA_EBITDA, ano_sel)
    tributos = _valor_conta_raw(df, cena, CONTA_TRIBUTOS, ano_sel)
    custos = _valor_conta_raw(df, cena, CONTA_CUSTOS, ano_sel)
    outros = _valor_conta_raw(df, cena, CONTA_OUTROS_RESULTADOS, ano_sel)

    margem_ebitda = _safe_div(ebitda, receita)
    margem_contribuicao_rs = (receita - abs(tributos)) - abs(custos)
    margem_contribuicao_pct = _safe_div(margem_contribuicao_rs, receita)
    break_even = _safe_div(abs(outros), margem_contribuicao_pct)

    investimento = _valor_premissa_comercial(
        df,
        cena,
        ["Investimento em Vendas e Mkt (R$)", "Investimento em Vendas e Marketing (R$)"],
        ano_sel,
        CEO_LTV_CAC_FALLBACK["Investimento em Vendas e Mkt (R$)"],
    )
    novos_clientes = _valor_premissa_comercial(
        df,
        cena,
        ["Novos Clientes Adquiridos (un)", "Novos Clientes Adquiridos"],
        ano_sel,
        CEO_LTV_CAC_FALLBACK["Novos Clientes Adquiridos (un)"],
    )
    ticket = _valor_premissa_comercial(
        df,
        cena,
        ["Ticket Médio (R$)", "Ticket Medio (R$)", "Ticket MÃ©dio (R$)"],
        ano_sel,
        CEO_LTV_CAC_FALLBACK["Ticket Médio (R$)"],
    )
    retencao = _valor_premissa_comercial(
        df,
        cena,
        ["Tempo Médio de Retenção (Meses)", "Tempo Medio de Retencao (Meses)", "Tempo MÃ©dio de RetenÃ§Ã£o (Meses)"],
        ano_sel,
        CEO_LTV_CAC_FALLBACK["Tempo Médio de Retenção (Meses)"],
    )
    cac = _safe_div(investimento, novos_clientes)
    ltv_cac = _safe_div(ticket * retencao, cac)

    return [
        (
            "EBITDA Operacional",
            fmt_rs(ebitda),
            f"Margem: {margem_ebitda * 100:.1f}%" if pd.notna(margem_ebitda) else "Margem: —",
            None,
        ),
        (
            "Ponto de Equilíbrio (Break-Even)",
            fmt_rs(break_even),
            "Faturamento mínimo exigido para cobrir despesas fixas",
            None,
        ),
        (
            "Eficiência Comercial (LTV / CAC)",
            f"{ltv_cac:.1f}x" if pd.notna(ltv_cac) else "—",
            "Multiplicador de retorno por cliente atraído",
            None,
        ),
    ]


def _kpis_acionistas(df: pd.DataFrame | None, cena: str | None, ano_sel: str | int) -> list[KpiItem]:
    resultado_operacional = _valor_conta_raw(df, cena, CONTA_RESULTADO_OPERACIONAL, ano_sel)
    ir_cs = _valor_conta_raw(df, cena, CONTA_IR_CS, ano_sel)
    resultado_liquido = _valor_conta_raw(df, cena, CONTA_RESULTADO_LIQUIDO, ano_sel)
    receita = _valor_conta_raw(df, cena, CONTA_RECEITA, ano_sel)
    patrimonio = abs(_valor_conta_raw(df, cena, CONTA_PATRIMONIO_LIQUIDO, ano_sel))
    divida = abs(_valor_conta_raw(df, cena, CONTA_EMPRESTIMOS, ano_sel))
    caixa = abs(_valor_conta_raw(df, cena, CONTA_DISPONIVEL, ano_sel))
    divida_liquida = max(divida - caixa, 0) if pd.notna(divida) and pd.notna(caixa) else float("nan")
    capital_investido = patrimonio + divida_liquida if pd.notna(patrimonio) and pd.notna(divida_liquida) else float("nan")

    aliquota_ir = _safe_div(abs(ir_cs), abs(resultado_operacional))
    if pd.isna(aliquota_ir):
        aliquota_ir = ALIQUOTA_IR_FALLBACK
    aliquota_ir = min(max(aliquota_ir, 0), ALIQUOTA_IR_FALLBACK)
    nopat = resultado_operacional * (1 - aliquota_ir) if pd.notna(resultado_operacional) else float("nan")
    roic = _safe_div(nopat, capital_investido)
    eva = nopat - (capital_investido * WACC_FALLBACK) if pd.notna(nopat) and pd.notna(capital_investido) else float("nan")
    margem_liquida = _safe_div(resultado_liquido, receita)

    return [
        (
            "Retorno sobre o Capital Investido (ROIC %)",
            fmt_pct(roic) if pd.notna(roic) else "—",
            "Retorno gerado sobre o capital total operado",
            None,
        ),
        (
            "Criação de Valor Econômico (EVA)",
            fmt_rs(eva),
            "Lucro econômico acima do custo de capital",
            None,
        ),
        (
            "Lucro Líquido & Margem Líquida (%)",
            fmt_rs(resultado_liquido),
            f"Margem: {margem_liquida * 100:.1f}%" if pd.notna(margem_liquida) else "Margem: —",
            None,
        ),
    ]


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


def kpis_por_persona(
    persona: str,
    k: pd.Series,
    ranking: pd.DataFrame,
    df: pd.DataFrame | None = None,
    cena_sel: str | None = None,
    ano_sel: str | int = "Todos",
) -> list[KpiItem]:
    if persona == "ceo":
        return _kpis_ceo(df, cena_sel, ano_sel)

    if persona == "cfo":
        liq = k["liquidez"] if "liquidez" in k.index else float("nan")
        ciclo = k["Ciclo_Financeiro"] if "Ciclo_Financeiro" in k.index else float("nan")
        return [
            ("Necessidade de Capital de Giro (NCG)", fmt_rs(k["NCG"]) if "NCG" in k.index else "—", help_text("ncg")),
            (
                "Saldo de Tesouraria",
                fmt_rs(k["Saldo_Tesouraria"]) if "Saldo_Tesouraria" in k.index else "—",
                help_text("treasury"),
            ),
            (
                "Ciclo Financeiro",
                fmt_dias(ciclo) if pd.notna(ciclo) else "—",
                help_text("cycle"),
            ),
            (
                "Liquidez Corrente (LC)",
                f"{liq:.2f}x" if pd.notna(liq) else "—",
                help_text("liquidity"),
            ),
        ]

    if persona == "acionistas":
        return _kpis_acionistas(df, cena_sel, ano_sel)

    return _kpis_poder_concedente(df, cena_sel, ano_sel)


def render_metric_card(label: str, value: str, dica: str | None = None) -> None:
    """Uma metrica nativa + CSS de contraste; tooltip unico via ``help``."""
    _garantir_css_metricas()
    if dica:
        st.metric(label, value, help=dica)
    else:
        st.metric(label, value)


def render_kpi_row(itens: list[KpiItem]) -> None:
    """Linha de KPIs com ``st.metric`` e contraste forcado no Dark Mode."""
    if not itens:
        return
    st.markdown(_KPI_FORCE_CSS, unsafe_allow_html=True)
    st.session_state["_cti_kpi_css_ok"] = True
    cols = st.columns(len(itens))
    for col, item in zip(cols, itens, strict=True):
        if len(item) == 4:
            rotulo, valor, delta, dica = item
        else:
            rotulo, valor, dica = item
            delta = None
        with col:
            if dica:
                st.metric(rotulo, valor, delta=delta, help=dica, delta_color="off")
            else:
                st.metric(rotulo, valor, delta=delta, delta_color="off")
