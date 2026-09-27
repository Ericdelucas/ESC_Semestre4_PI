"""Sub-abas especificas por persona do stakeholder."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.config import COR, COR_ALERTA, COR_OK, COR_SUAVE, COR_VERMELHO
from src.models.formatting import cena_rotulo, fmt_dias, fmt_pct, fmt_rs

WACC = 0.10
PAYOUT = 0.35
ALIQUOTA_IR_FALLBACK = 0.34
SERIES_STYLES = {
    "A": {"color": COR, "dash": "solid", "fill": "rgba(31, 78, 69, 0.18)"},
    "B": {"color": COR_ALERTA, "dash": "dash", "fill": "rgba(166, 93, 63, 0.14)"},
    "C": {"color": COR_OK, "dash": "dot", "fill": "rgba(47, 107, 79, 0.10)"},
}


def _safe_div(num: float | pd.Series, den: float | pd.Series) -> float | pd.Series:
    if isinstance(num, pd.Series) or isinstance(den, pd.Series):
        index = num.index if isinstance(num, pd.Series) else den.index
        numerador = pd.to_numeric(num, errors="coerce")
        denominador = pd.to_numeric(den, errors="coerce")
        if not isinstance(numerador, pd.Series):
            numerador = pd.Series(numerador, index=index)
        if not isinstance(denominador, pd.Series):
            denominador = pd.Series(denominador, index=index)
        denominador = denominador.replace(0, pd.NA)
        return numerador / denominador
    return float("nan") if pd.isna(den) or float(den) == 0 else num / den


def _wide(df: pd.DataFrame, cena: str, contas: list[str]) -> pd.DataFrame:
    base = df.loc[(df["CENA"] == cena) & (df["CONTA"].isin(contas)), ["ano_num", "CONTA", "VALOR"]].copy()
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


def _dre(df: pd.DataFrame, cena: str) -> pd.DataFrame:
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
    receita = _conta(dados, "DRE - Receita")
    tributos = _conta(dados, "DRE - Tributos")
    custos = _conta(dados, "DRE - Custos")
    dep = _conta(dados, "DRE - Depreciação e Amortização")
    ebitda = _conta(dados, "DRE - EBITDA")
    ebit = _conta(dados, "DRE - Resultado Operacional")
    fin = _conta(dados, "DRE - Resultado Financeiro")
    ebt = _conta(dados, "DRE - Resultado Antes do Imposto de Renda")
    lucro = _conta(dados, "DRE - Resultado Líquido")
    outros = _conta(dados, "DRE - Outros Resultados Operacionais")
    despesas_fin = _conta(dados, "DRE - Despesas Financeiras")

    dados["Receita Líquida"] = receita + tributos
    dados["Margem Bruta"] = dados["Receita Líquida"] + custos
    dados["OPEX"] = ebitda - dados["Margem Bruta"]
    dados["EBITDA"] = ebitda
    dados["EBIT"] = ebit
    dados["Resultado Financeiro"] = fin
    dados["EBT"] = ebt
    dados["Lucro Líquido"] = lucro
    dados["Custos"] = custos
    dados["Depreciação"] = dep
    dados["Outros Operacionais"] = outros
    dados["Despesas Financeiras"] = despesas_fin
    return dados


def _balanco_fluxo(df: pd.DataFrame, cena: str) -> pd.DataFrame:
    contas = [
        "BAL - Total do Ativo",
        "BAL - Total do Passivo",
        "BAL - Ativo Circulante",
        "BAL - Passivo Circulante",
        "BAL - Realizável a Longo Prazo",
        "BAL - Exigível a Longo Prazo",
        "BAL  - Patrimônio Líquido",
        "BAL - Empréstimos",
        "BAL - Disponível",
        "BAL - Investimentos - Imobilizado",
        "BAL - Investimentos - Intangível",
        "BAL - Depreciação Acumulada",
        "BAL - Amortização Acumulada",
        "FLU - Investimentos",
        "FLU - Distribuição para Acionista",
    ]
    return _wide(df, cena, contas)


def _financeiro(df: pd.DataFrame, cena: str) -> pd.DataFrame:
    dre = _dre(df, cena)
    bal = _balanco_fluxo(df, cena)
    dados = dre.merge(bal, on="ano_num", how="outer").sort_values("ano_num").fillna(0.0)
    patrimonio = _conta(dados, "BAL  - Patrimônio Líquido").abs()
    divida = _conta(dados, "BAL - Empréstimos").abs()
    caixa = _conta(dados, "BAL - Disponível").abs()
    divida_liquida = (divida - caixa).clip(lower=0)
    capital = (patrimonio + divida_liquida).replace(0, pd.NA)
    ir_cs = _conta(dados, "DRE - Imposto de Renda e Contribuição Social")
    aliquota_ir = (_safe_div(ir_cs.abs(), dados["EBIT"].abs())).clip(lower=0, upper=ALIQUOTA_IR_FALLBACK).fillna(ALIQUOTA_IR_FALLBACK)
    nopat = dados["EBIT"] * (1 - aliquota_ir)
    lucro = dados["Lucro Líquido"]
    dados["Dívida Líquida"] = divida_liquida
    dados["Capital Investido"] = capital
    dados["NOPAT"] = nopat
    dados["ROIC"] = nopat / capital
    dados["ROE"] = lucro / patrimonio.replace(0, pd.NA)
    dados["WACC"] = WACC
    dados["Custo do Capital"] = capital * WACC
    dados["EVA"] = nopat - dados["Custo do Capital"]
    dados["Dividendos"] = (lucro.clip(lower=0) * PAYOUT).fillna(0)
    dados["Retido"] = (lucro.clip(lower=0) - dados["Dividendos"]).fillna(0)
    dados["DY"] = dados["Dividendos"] / capital
    return dados


def render_ceo_visao_geral(df: pd.DataFrame, cena: str, ano_sel: str | int) -> None:
    dados = _dre(df, cena)
    if dados.empty:
        st.info("Sem dados de DRE para este cenário.")
        return
    medias = dados.mean(numeric_only=True)
    waterfall = go.Figure(
        go.Waterfall(
            name="DRE média",
            orientation="v",
            measure=["relative", "relative", "relative", "relative", "relative", "relative", "total"],
            x=["Receita Líquida", "Custos", "OPEX", "Depreciação", "Resultado Financeiro", "IR/CS", "Lucro Líquido"],
            y=[
                medias["Receita Líquida"],
                medias["Custos"],
                medias["OPEX"],
                medias["Depreciação"],
                medias["Resultado Financeiro"],
                medias["DRE - Imposto de Renda e Contribuição Social"],
                medias["Lucro Líquido"],
            ],
        )
    )
    waterfall.update_layout(title="Cascata média da DRE", yaxis_title="R$")
    st.plotly_chart(waterfall, width="stretch", theme="streamlit")

    evol = dados[["ano_num", "Receita Líquida", "EBITDA"]].melt("ano_num", var_name="Indicador", value_name="Valor")
    fig = px.line(evol, x="ano_num", y="Valor", color="Indicador", markers=True, title="Receita Líquida vs EBITDA")
    fig.update_layout(xaxis_title="Ano", yaxis_title="R$", hovermode="x unified")
    st.plotly_chart(fig, width="stretch", theme="streamlit")


def render_ceo_dre_operacional(df: pd.DataFrame, cena: str, ano_sel: str | int) -> None:
    dados = _dre(df, cena)
    if dados.empty:
        st.info("Sem dados de DRE operacional para este cenário.")
        return
    receita = dados["Receita Líquida"].replace(0, pd.NA)
    dados["Margem Bruta (%)"] = dados["Margem Bruta"] / receita
    dados["Margem EBITDA (%)"] = dados["EBITDA"] / receita
    dados["Margem EBIT (%)"] = dados["EBIT"] / receita
    dados["YoY OPEX (%)"] = dados["OPEX"].abs().pct_change()
    comp = pd.DataFrame(
        {
            "ano_num": dados["ano_num"],
            "Custos": dados["Custos"].abs() / receita,
            "OPEX": dados["OPEX"].abs() / receita,
            "Depreciação": dados["Depreciação"].abs() / receita,
        }
    ).melt("ano_num", var_name="Conta", value_name="% Receita Líquida")
    fig = px.bar(comp, x="ano_num", y="% Receita Líquida", color="Conta", title="Composição operacional sobre Receita Líquida")
    fig.update_layout(barmode="stack", yaxis_tickformat=".0%", xaxis_title="Ano")
    st.plotly_chart(fig, width="stretch", theme="streamlit")
    tabela = dados[["ano_num", "Receita Líquida", "Custos", "OPEX", "EBITDA", "EBIT", "Lucro Líquido", "Margem Bruta (%)", "Margem EBITDA (%)", "Margem EBIT (%)", "YoY OPEX (%)"]].copy()
    st.dataframe(tabela, width="stretch", hide_index=True)


def _break_even_df(df: pd.DataFrame, cena: str) -> pd.DataFrame:
    dados = _dre(df, cena)
    if dados.empty:
        return dados
    receita = dados["Receita Líquida"].replace(0, pd.NA)
    custos_variaveis = dados["Custos"].abs()
    custos_fixos = dados["Outros Operacionais"].abs() + dados["Depreciação"].abs() + dados["Despesas Financeiras"].abs()
    mc = (dados["Receita Líquida"] - custos_variaveis) / receita
    dados["Custos Fixos"] = custos_fixos
    dados["Margem de Contribuição (%)"] = mc
    dados["Break-Even"] = custos_fixos / mc.replace(0, pd.NA)
    dados["Margem de Segurança (%)"] = (dados["Receita Líquida"] - dados["Break-Even"]) / receita
    return dados


def render_ceo_break_even(df: pd.DataFrame, cena: str, ano_sel: str | int) -> None:
    dados = _break_even_df(df, cena)
    if dados.empty:
        st.info("Sem dados suficientes para Break-Even.")
        return
    media = dados.mean(numeric_only=True)
    eixo = pd.Series([0, media["Break-Even"], media["Receita Líquida"]]).dropna()
    chart = pd.DataFrame({"Receita": eixo})
    chart["Receita Total"] = chart["Receita"]
    chart["Custos Totais"] = media["Custos Fixos"] + (chart["Receita"] * (1 - media["Margem de Contribuição (%)"]))
    fig = px.line(chart.melt("Receita", var_name="Linha", value_name="Valor"), x="Receita", y="Valor", color="Linha", markers=True, title="Ponto de equilíbrio médio")
    fig.add_vline(x=media["Break-Even"], line_dash="dash", line_color=COR_ALERTA, annotation_text="Break-Even")
    st.plotly_chart(fig, width="stretch", theme="streamlit")
    fig_area = px.area(dados, x="ano_num", y="Margem de Segurança (%)", title="Margem de segurança ao longo do horizonte")
    fig_area.update_layout(yaxis_tickformat=".1%")
    st.plotly_chart(fig_area, width="stretch", theme="streamlit")


def render_ceo_ltv_cac(df: pd.DataFrame, cena: str, ano_sel: str | int) -> None:
    dados = _break_even_df(df, cena)
    if dados.empty:
        st.info("Sem dados suficientes para LTV/CAC.")
        return
    ticket = 4_500.0
    retencao = 10.0
    investimento = 100_000.0
    novos = 1_000.0
    dados["CAC"] = investimento / novos
    dados["LTV"] = ticket * dados["Margem de Contribuição (%)"].fillna(0) * retencao
    dados["LTV/CAC"] = dados["LTV"] / dados["CAC"].replace(0, pd.NA)
    c1, c2, c3 = st.columns(3)
    c1.metric("LTV médio", fmt_rs(float(dados["LTV"].mean())))
    c2.metric("CAC médio", fmt_rs(float(dados["CAC"].mean())))
    c3.metric("Razão LTV/CAC", f"{float(dados['LTV/CAC'].mean()):.1f}x")
    comp = dados[["ano_num", "LTV", "CAC"]].melt("ano_num", var_name="Indicador", value_name="Valor")
    fig = px.bar(comp, x="ano_num", y="Valor", color="Indicador", barmode="group", title="LTV vs CAC por ano")
    st.plotly_chart(fig, width="stretch", theme="streamlit")


def render_acionistas_retorno(df: pd.DataFrame, cena: str, ano_sel: str | int) -> None:
    dados = _financeiro(df, cena)
    fig = px.line(dados.melt("ano_num", value_vars=["ROIC", "ROE", "WACC"], var_name="Indicador", value_name="Valor"), x="ano_num", y="Valor", color="Indicador", markers=True, title="ROIC vs ROE vs WACC")
    fig.update_layout(yaxis_tickformat=".1%", xaxis_title="Ano")
    st.plotly_chart(fig, width="stretch", theme="streamlit")


def render_acionistas_eva(df: pd.DataFrame, cena: str, ano_sel: str | int) -> None:
    dados = _financeiro(df, cena)
    fig = px.bar(dados, x="ano_num", y="EVA", color=dados["EVA"] >= 0, color_discrete_map={True: COR_OK, False: COR_ALERTA}, title="EVA ano a ano")
    fig.update_layout(showlegend=False, xaxis_title="Ano", yaxis_title="R$")
    st.plotly_chart(fig, width="stretch", theme="streamlit")


def render_acionistas_dividendos(df: pd.DataFrame, cena: str, ano_sel: str | int) -> None:
    dados = _financeiro(df, cena)
    comp = dados[["ano_num", "Dividendos", "Retido"]].melt("ano_num", var_name="Destino", value_name="Valor")
    fig = px.bar(comp, x="ano_num", y="Valor", color="Destino", title="Lucro líquido: dividendos vs reinvestimento")
    st.plotly_chart(fig, width="stretch", theme="streamlit")
    tabela = dados[["ano_num", "Lucro Líquido", "Dividendos", "Retido", "DY"]].copy()
    st.dataframe(tabela, width="stretch", hide_index=True)


def render_concedente_capex(df: pd.DataFrame, cena: str, ano_sel: str | int) -> None:
    dados = _dre(df, cena).merge(_balanco_fluxo(df, cena), on="ano_num", how="outer").sort_values("ano_num").fillna(0.0)
    dados["CAPEX"] = _conta(dados, "FLU - Investimentos").abs()
    dados["CAPEX Acumulado"] = dados["CAPEX"].cumsum()
    dados["CAPEX / Receita Líquida"] = dados["CAPEX"] / dados["Receita Líquida"].replace(0, pd.NA)
    fig = go.Figure()
    fig.add_bar(x=dados["ano_num"], y=dados["CAPEX"], name="CAPEX anual", marker_color=COR_SUAVE)
    fig.add_scatter(x=dados["ano_num"], y=dados["CAPEX Acumulado"], name="CAPEX acumulado", mode="lines+markers", line={"color": COR})
    fig.update_layout(title="Plano de CAPEX", xaxis_title="Ano", yaxis_title="R$")
    st.plotly_chart(fig, width="stretch", theme="streamlit")


def render_concedente_solvencia(df: pd.DataFrame, cena: str, ano_sel: str | int) -> None:
    dados = _dre(df, cena).merge(_balanco_fluxo(df, cena), on="ano_num", how="outer").sort_values("ano_num").fillna(0.0)
    lg = (_conta(dados, "BAL - Ativo Circulante").abs() + _conta(dados, "BAL - Realizável a Longo Prazo").abs()) / (
        _conta(dados, "BAL - Passivo Circulante").abs() + _conta(dados, "BAL - Exigível a Longo Prazo").abs()
    ).replace(0, pd.NA)
    dados["Liquidez Geral"] = lg
    dados["Endividamento"] = _conta(dados, "BAL - Total do Passivo").abs() / _conta(dados, "BAL - Total do Ativo").abs().replace(0, pd.NA)
    dados["Cobertura de Juros"] = dados["EBIT"] / _conta(dados, "DRE - Despesas Financeiras").abs().replace(0, pd.NA)
    fig = px.line(dados, x="ano_num", y="Liquidez Geral", markers=True, title="Liquidez Geral com limite de risco")
    fig.add_hline(y=1.0, line_dash="dash", line_color=COR_VERMELHO, annotation_text="Mínimo 1,0x")
    st.plotly_chart(fig, width="stretch", theme="streamlit")
    st.dataframe(dados[["ano_num", "Liquidez Geral", "Endividamento", "Cobertura de Juros"]], width="stretch", hide_index=True)


def render_concedente_ativos(df: pd.DataFrame, cena: str, ano_sel: str | int) -> None:
    dados = _balanco_fluxo(df, cena)
    bruto = _conta(dados, "BAL - Investimentos - Imobilizado").abs() + _conta(dados, "BAL - Investimentos - Intangível").abs()
    dep = _conta(dados, "BAL - Depreciação Acumulada").abs() + _conta(dados, "BAL - Amortização Acumulada").abs()
    dados["Base Líquida"] = bruto - dep
    dados["Depreciação/Amortização Acumulada"] = dep
    comp = dados[["ano_num", "Base Líquida", "Depreciação/Amortização Acumulada"]].melt("ano_num", var_name="Componente", value_name="Valor")
    fig = px.area(comp, x="ano_num", y="Valor", color="Componente", title="Ativos reversíveis líquidos vs depreciação acumulada")
    st.plotly_chart(fig, width="stretch", theme="streamlit")


def _selecionar_cenarios(cenas: list[str], persona: str) -> list[tuple[str, str]]:
    col_a, col_b, col_c = st.columns(3)
    default_b = 1 if len(cenas) > 1 else 0
    opcoes_c = [None, *cenas]
    default_c = 3 if len(cenas) > 2 else 0
    with col_a:
        cena_a = st.selectbox(
            "Cenário A (Base):",
            options=cenas,
            index=0,
            format_func=cena_rotulo,
            key=f"cmp_abc_a_{persona}",
        )
    with col_b:
        cena_b = st.selectbox(
            "Cenário B (Comparativo 1):",
            options=cenas,
            index=default_b,
            format_func=cena_rotulo,
            key=f"cmp_abc_b_{persona}",
        )
    with col_c:
        cena_c = st.selectbox(
            "Cenário C (Comparativo 2 / Opcional):",
            options=opcoes_c,
            index=default_c,
            format_func=lambda cena: "Nenhum" if cena is None else cena_rotulo(cena),
            key=f"cmp_abc_c_{persona}",
        )
    selecionados = [("A", cena_a), ("B", cena_b)]
    if cena_c is not None:
        selecionados.append(("C", cena_c))
    return selecionados


def _delta(valor_a: float, valor_b: float, fmt, *, maior_melhor: bool = True) -> tuple[str, str]:
    if pd.isna(valor_a) or pd.isna(valor_b):
        return "—", "off"
    dif = valor_b - valor_a
    pct = _safe_div(dif, abs(valor_a))
    pct_txt = f" ({pct * 100:+.1f}%)" if pd.notna(pct) else ""
    favoravel = dif >= 0 if maior_melhor else dif <= 0
    cor = "normal" if (dif >= 0) == favoravel else "inverse"
    return f"{fmt(dif)}{pct_txt}", cor


def _cor_delta(valor_a: float, valor_b: float, *, maior_melhor: bool = True) -> str:
    if pd.isna(valor_a) or pd.isna(valor_b):
        return "#8A8F98"
    dif = valor_b - valor_a
    favoravel = dif >= 0 if maior_melhor else dif <= 0
    return COR_OK if favoravel else COR_VERMELHO


def _metric_base(
    label: str,
    valor_a: float,
    comparativos: list[tuple[str, float]],
    fmt,
    *,
    maior_melhor: bool = True,
    help_text: str | None = None,
    extra: str | None = None,
) -> None:
    st.metric(label, fmt(valor_a), help=help_text)
    if extra:
        st.caption(extra)
    for rotulo, valor in comparativos:
        delta, _ = _delta(valor_a, valor, fmt, maior_melhor=maior_melhor)
        cor = _cor_delta(valor_a, valor, maior_melhor=maior_melhor)
        st.markdown(
            f"<div style='font-size:0.82rem;font-weight:700;color:{cor};'>Δ {rotulo}: {delta}</div>",
            unsafe_allow_html=True,
        )


def _fmt_x(valor: float) -> str:
    return "—" if pd.isna(valor) else f"{valor:.2f}x"


def _fmt_num(valor: float) -> str:
    return "—" if pd.isna(valor) else f"{valor:,.2f}"


def _ceo_cmp(df: pd.DataFrame, cena: str) -> pd.DataFrame:
    dre = _dre(df, cena)
    be = _break_even_df(df, cena)
    return dre.merge(be[["ano_num", "Break-Even"]], on="ano_num", how="left")


def _render_cmp_ceo(df: pd.DataFrame, cenarios: list[tuple[str, str]]) -> None:
    dados = {rotulo: _ceo_cmp(df, cena) for rotulo, cena in cenarios}
    metricas = {
        rotulo: {
            "receita": base["Receita Líquida"].sum(),
            "ebitda": base["EBITDA"].sum(),
            "margem": _safe_div(base["EBITDA"].sum(), base["Receita Líquida"].sum()),
            "break_even": base["Break-Even"].mean(),
        }
        for rotulo, base in dados.items()
    }
    comp = [rotulo for rotulo, _ in cenarios if rotulo != "A"]

    c1, c2, c3 = st.columns(3)
    with c1:
        _metric_base("Receita Líquida Acumulada", metricas["A"]["receita"], [(r, metricas[r]["receita"]) for r in comp], fmt_rs)
    with c2:
        margem_a = metricas["A"]["margem"]
        extra = f"Margem média A: {margem_a * 100:.1f}%" if pd.notna(margem_a) else "Margem média A: —"
        _metric_base("EBITDA Acumulado", metricas["A"]["ebitda"], [(r, metricas[r]["ebitda"]) for r in comp], fmt_rs, extra=extra)
    with c3:
        _metric_base("Break-Even Médio", metricas["A"]["break_even"], [(r, metricas[r]["break_even"]) for r in comp], fmt_rs, maior_melhor=False)

    fig = go.Figure()
    for rotulo, cena in cenarios:
        estilo = SERIES_STYLES[rotulo]
        base = dados[rotulo]
        nome = f"Série {rotulo} · {cena_rotulo(cena)}"
        fig.add_scatter(x=base["ano_num"], y=base["Receita Líquida"], mode="lines+markers", name=f"{nome} · Receita", line={"color": estilo["color"], "dash": estilo["dash"]})
        fig.add_scatter(x=base["ano_num"], y=base["EBITDA"], mode="lines+markers", name=f"{nome} · EBITDA", line={"color": estilo["color"], "dash": estilo["dash"], "width": 2})
    fig.update_layout(title="Receita Líquida e EBITDA: comparação de cenários", xaxis_title="Ano", yaxis_title="R$", hovermode="x unified")
    st.plotly_chart(fig, width="stretch", theme="streamlit")


def _render_cmp_cfo(ind: pd.DataFrame, cenarios: list[tuple[str, str]]) -> None:
    dados = {rotulo: ind[ind["CENA"] == cena].sort_values("ano_num") for rotulo, cena in cenarios}
    metricas = {
        rotulo: {
            "ncg": base["NCG"].mean(),
            "tesouraria": base["Saldo_Tesouraria"].min(),
            "ciclo": base["Ciclo_Financeiro"].mean(),
        }
        for rotulo, base in dados.items()
    }
    comp = [rotulo for rotulo, _ in cenarios if rotulo != "A"]

    c1, c2, c3 = st.columns(3)
    with c1:
        _metric_base("NCG Média", metricas["A"]["ncg"], [(r, metricas[r]["ncg"]) for r in comp], fmt_rs, maior_melhor=False)
    with c2:
        _metric_base("Menor Saldo de Tesouraria", metricas["A"]["tesouraria"], [(r, metricas[r]["tesouraria"]) for r in comp], fmt_rs)
    with c3:
        _metric_base("Ciclo Financeiro Médio", metricas["A"]["ciclo"], [(r, metricas[r]["ciclo"]) for r in comp], fmt_dias, maior_melhor=False)

    fig = go.Figure()
    for rotulo, cena in cenarios:
        estilo = SERIES_STYLES[rotulo]
        base = dados[rotulo]
        fig.add_scatter(
            x=base["ano_num"],
            y=base["Saldo_Tesouraria"],
            mode="lines",
            fill="tozeroy",
            fillcolor=estilo["fill"],
            name=f"Série {rotulo} · {cena_rotulo(cena)}",
            line={"color": estilo["color"], "dash": estilo["dash"]},
        )
    fig.add_hline(y=0, line_dash="dash", line_color=COR_VERMELHO, annotation_text="Zero")
    fig.update_layout(title="Teste de estresse de tesouraria", xaxis_title="Ano", yaxis_title="R$", hovermode="x unified")
    st.plotly_chart(fig, width="stretch", theme="streamlit")


def _render_cmp_acionistas(df: pd.DataFrame, cenarios: list[tuple[str, str]]) -> None:
    dados = {rotulo: _financeiro(df, cena) for rotulo, cena in cenarios}
    metricas = {
        rotulo: {
            "roic": base["ROIC"].mean(),
            "eva": base["EVA"].sum(),
            "dividendos": base["Dividendos"].sum(),
            "risco": base["Lucro Líquido"].std(),
        }
        for rotulo, base in dados.items()
    }
    comp = [rotulo for rotulo, _ in cenarios if rotulo != "A"]

    c1, c2, c3 = st.columns(3)
    with c1:
        _metric_base("ROIC Médio", metricas["A"]["roic"], [(r, metricas[r]["roic"]) for r in comp], fmt_pct)
    with c2:
        _metric_base("EVA Acumulado", metricas["A"]["eva"], [(r, metricas[r]["eva"]) for r in comp], fmt_rs)
    with c3:
        _metric_base("Dividendos Distribuídos", metricas["A"]["dividendos"], [(r, metricas[r]["dividendos"]) for r in comp], fmt_rs)

    eva = pd.concat(
        [
            pd.DataFrame({"ano_num": base["ano_num"], "Cenário": f"Série {rotulo}", "EVA": base["EVA"]})
            for rotulo, base in dados.items()
        ]
    )
    fig = px.bar(eva, x="ano_num", y="EVA", color="Cenário", barmode="group", title="EVA ano a ano: cenários selecionados")
    st.plotly_chart(fig, width="stretch", theme="streamlit")

    risco = pd.DataFrame(
        [
            {"Cenário": f"Série {rotulo}", "Risco": metricas[rotulo]["risco"], "ROIC Médio": metricas[rotulo]["roic"]}
            for rotulo, _ in cenarios
        ]
    )
    fig2 = px.scatter(risco, x="Risco", y="ROIC Médio", text="Cenário", title="Risco x Retorno")
    fig2.update_traces(textposition="top center", marker={"size": 16})
    fig2.update_layout(yaxis_tickformat=".1%")
    st.plotly_chart(fig2, width="stretch", theme="streamlit")


def _concedente_cmp(df: pd.DataFrame, cena: str) -> pd.DataFrame:
    dados = _dre(df, cena).merge(_balanco_fluxo(df, cena), on="ano_num", how="outer").sort_values("ano_num").fillna(0.0)
    dados["CAPEX"] = _conta(dados, "FLU - Investimentos").abs()
    dados["CAPEX Acumulado"] = dados["CAPEX"].cumsum()
    dados["Liquidez Geral"] = (_conta(dados, "BAL - Ativo Circulante").abs() + _conta(dados, "BAL - Realizável a Longo Prazo").abs()) / (
        _conta(dados, "BAL - Passivo Circulante").abs() + _conta(dados, "BAL - Exigível a Longo Prazo").abs()
    ).replace(0, pd.NA)
    dados["Base Final"] = _conta(dados, "BAL - Investimentos - Imobilizado").abs() + _conta(dados, "BAL - Investimentos - Intangível").abs()
    return dados


def _lg_referencia(dados: pd.DataFrame, ano_sel: str | int) -> float:
    if dados.empty:
        return float("nan")
    if ano_sel != "Todos":
        recorte = dados.loc[dados["ano_num"] == int(ano_sel)]
        return float(recorte["Liquidez Geral"].mean()) if not recorte.empty else float("nan")
    ultimo_ano = dados["ano_num"].max()
    return float(dados.loc[dados["ano_num"] == ultimo_ano, "Liquidez Geral"].mean())


def _base_final_ativos(dados: pd.DataFrame) -> float:
    if dados.empty:
        return float("nan")
    ultimo_ano = dados["ano_num"].max()
    final = dados.loc[dados["ano_num"] == ultimo_ano]
    base_bruta = float(final["Base Final"].sum())
    if abs(base_bruta) >= 1:
        return base_bruta
    ativo_total = float(_conta(final, "BAL - Total do Ativo").abs().sum())
    if abs(ativo_total) >= 1:
        return ativo_total
    return float(dados["Base Final"].abs().max())


def _render_cmp_concedente(df: pd.DataFrame, cenarios: list[tuple[str, str]], ano_sel: str | int) -> None:
    dados = {rotulo: _concedente_cmp(df, cena) for rotulo, cena in cenarios}
    metricas = {
        rotulo: {
            "capex": base["CAPEX"].sum(),
            "lg": base["Liquidez Geral"].mean(),
            "base_final": _base_final_ativos(base),
            "lg_ref": _lg_referencia(base, ano_sel),
        }
        for rotulo, base in dados.items()
    }
    comp = [rotulo for rotulo, _ in cenarios if rotulo != "A"]

    c1, c2, c3 = st.columns(3)
    with c1:
        _metric_base("CAPEX Acumulado Executado", metricas["A"]["capex"], [(r, metricas[r]["capex"]) for r in comp], fmt_rs)
    with c2:
        _metric_base("Liquidez Geral Média", metricas["A"]["lg"], [(r, metricas[r]["lg"]) for r in comp], _fmt_x)
    with c3:
        _metric_base("Base Final de Ativos Reversíveis", metricas["A"]["base_final"], [(r, metricas[r]["base_final"]) for r in comp], fmt_rs)

    fig = go.Figure()
    for rotulo, cena in cenarios:
        estilo = SERIES_STYLES[rotulo]
        base = dados[rotulo]
        fig.add_scatter(
            x=base["ano_num"],
            y=base["Liquidez Geral"],
            mode="lines+markers",
            name=f"Série {rotulo} · {cena_rotulo(cena)}",
            line={"color": estilo["color"], "dash": estilo["dash"]},
        )
    fig.add_hline(y=1.0, line_dash="dash", line_color=COR_VERMELHO, annotation_text="Mínimo contratual 1,0x")
    fig.update_layout(title="Liquidez Geral: base vs estresse", xaxis_title="Ano", yaxis_title="Liquidez Geral (x)", hovermode="x unified")
    st.plotly_chart(fig, width="stretch", theme="streamlit")
    abaixo_limite = [
        f"Série {rotulo} ({_fmt_x(metricas[rotulo]['lg_ref'])})"
        for rotulo, _ in cenarios
        if pd.notna(metricas[rotulo]["lg_ref"]) and metricas[rotulo]["lg_ref"] < 1.0
    ]
    if abaixo_limite:
        st.error("Risco de Descumprimento Contratual / Caducidade: " + ", ".join(abaixo_limite))
    else:
        st.success("Concessão em Conformidade Financeira (Liquidez ≥ 1,0x)")


def render_comparar_cenarios(df: pd.DataFrame, ind: pd.DataFrame, cenas: list[str], persona: str, ano_sel: str | int = "Todos") -> None:
    st.markdown("#### Comparação de Cenários (Análise A/B e Teste de Estresse)")
    cenarios = _selecionar_cenarios(cenas, persona)
    ids = [cena for _, cena in cenarios]
    if len(set(ids)) != len(ids):
        st.info("Selecione cenários diferentes para comparar.")
        return
    if persona == "ceo":
        _render_cmp_ceo(df, cenarios)
    elif persona == "cfo":
        _render_cmp_cfo(ind, cenarios)
    elif persona == "acionistas":
        _render_cmp_acionistas(df, cenarios)
    else:
        _render_cmp_concedente(df, cenarios, ano_sel)
