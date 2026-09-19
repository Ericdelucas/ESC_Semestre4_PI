"""Visões orientadas às decisões de cada stakeholder."""
from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from src.components.kpis import render_kpi_row
from src.config.i18n import get_lang
from src.data.formatting import fmt_rs, fmt_pct


def tr(pt, en):
    return en if get_lang() == "en" else pt


PROFILE_NAV = {
    "geral": ["overview", "comparar", "mapeamento", "faixa", "assistente", "como_ler"],
    "cfo": ["overview", "capital_giro", "prazos", "faixa", "comparar", "distribuicao", "assistente", "como_ler"],
    "acionistas": ["overview", "mapeamento", "comparar", "distribuicao", "faixa", "assistente", "como_ler"],
    "concedente": ["overview", "faixa", "comparar", "distribuicao", "capital_giro", "assistente", "como_ler"],
}


def overview_label(persona):
    return {
        "geral": tr("Visão estratégica", "Strategic overview"),
        "cfo": tr("Gestão financeira", "Financial management"),
        "acionistas": tr("Retorno e risco", "Return and risk"),
        "concedente": tr("Sustentabilidade da concessão", "Concession sustainability"),
    }[persona]


def labels():
    return {
        "dre_receita": tr("Receita", "Revenue"),
        "resultado": tr("Resultado líquido", "Net income"),
        "ebitda": "EBITDA",
        "dre_custos": tr("Custos (magnitude)", "Costs (magnitude)"),
        "geracao_caixa": tr("Geração de caixa", "Cash generation"),
        "caixa_final_sinal": tr("Saldo final de caixa", "Closing cash balance"),
        "NCG": tr("Necessidade de capital de giro", "Working capital requirement"),
        "Saldo_Tesouraria": tr("Saldo de tesouraria", "Treasury balance"),
        "emprestimos_cp": tr("Empréstimos (magnitude)", "Loans (magnitude)"),
        "pressao_invest": tr("Investimentos (magnitude)", "Investments (magnitude)"),
        "dist_abs": tr("Distribuição aos acionistas (magnitude)", "Shareholder distributions (magnitude)"),
        "rentabilidade": tr("Margem líquida", "Net margin"),
        "liquidez": tr("Liquidez corrente", "Current ratio"),
    }


def critical_flags(frame):
    return pd.DataFrame({
        tr("Caixa final negativo", "Negative closing cash"): frame["caixa_final_sinal"] < 0,
        tr("Liquidez abaixo de 1", "Current ratio below 1"): frame["liquidez"] < 1,
        tr("Geração de caixa negativa", "Negative cash generation"): frame["geracao_caixa"] < 0,
    }, index=frame.index)


def render_summary(ctx):
    st.subheader(overview_label(ctx.persona))
    purposes = {
        "geral": tr("Como está a empresa e onde precisamos agir?", "How is the company doing and where should we act?"),
        "cfo": tr("Temos recursos suficientes e como devemos administrá-los?", "Do we have sufficient resources and how should we manage them?"),
        "acionistas": tr("Os resultados e a geração de caixa compensam os riscos?", "Do earnings and cash generation justify the risks?"),
        "concedente": tr("Há condições financeiras para sustentar a operação e os investimentos?", "Can financial resources sustain operations and investments?"),
    }

    st.write(purposes[ctx.persona])
    data = ctx.foco_ano
    if data.empty:
        st.warning(tr("Sem dados para este recorte.", "No data for this selection."))
        return
    names = labels()
    cols = {
        "geral": ["dre_receita", "resultado", "ebitda", "geracao_caixa"],
        "cfo": ["NCG", "Saldo_Tesouraria", "emprestimos_cp", "caixa_final_sinal"],
        "acionistas": ["resultado", "rentabilidade", "dist_abs", "geracao_caixa"],
        "concedente": ["caixa_final_sinal", "liquidez", "geracao_caixa", "pressao_invest"],
    }[ctx.persona]
    cards = []
    for col in cols:
        series = data[col].abs() if col == "emprestimos_cp" else data[col]
        value = series.mean()
        formatted = "\u2014" if pd.isna(value) else (fmt_pct(value) if col == "rentabilidade" else f"{value:.2f}x" if col == "liquidez" else fmt_rs(value))
        cards.append((names[col], formatted, tr("Média dos anos selecionados; não é valor acumulado.", "Average of selected years; not a cumulative amount.")))
    render_kpi_row(cards)
    st.caption(tr(f"Cenário {ctx.cena_sel} \u00b7 " + ("médias anuais do horizonte completo" if ctx.ano_sel == "Todos" else f"valores do ano {ctx.ano_sel}"), f"Scenario {ctx.cena_sel} \u00b7 " + ("annual averages over the full horizon" if ctx.ano_sel == "Todos" else f"values for year {ctx.ano_sel}")))


def chart(data, cols, title, unit="R$"):
    names = labels()
    plot = data[["ano_num", *cols]].copy()
    for col in ("emprestimos_cp", "dre_custos"):
        if col in plot:
            plot[col] = plot[col].abs()
    plot = plot.rename(columns=names)
    fig = px.line(plot, x="ano_num", y=[names[c] for c in cols], markers=True,
                  title=title, labels={"ano_num": tr("Ano", "Year"), "value": unit, "variable": ""})
    fig.update_layout(hovermode="x unified", legend_title_text="")
    fig.add_hline(y=0, line_dash="dot", opacity=0.4)
    if unit == "%":
        fig.update_yaxes(tickformat=".1%")
    st.plotly_chart(fig, width="stretch")


def render(ctx):
    data = ctx.foco_ano.sort_values("ano_num")
    if data.empty:
        return
    st.subheader(tr("Pontos de atenção e decisões", "Issues and decisions"))
    flags = critical_flags(data)
    critical = flags.any(axis=1)
    years = ", ".join(str(int(y)) for y in data.loc[critical, "ano_num"])
    if years:
        st.warning(tr(f"Anos com sinais de atenção financeira: {years}. Verifique as causas antes de decidir.", f"Years with financial warning signs: {years}. Check the causes before deciding."))
    else:
        st.info(tr("Nenhum dos três sinais de atenção foi encontrado no recorte: caixa final negativo, liquidez abaixo de 1 ou geração de caixa negativa.", "None of the three warning signs were found: negative closing cash, current ratio below 1 or negative cash generation."))
    guidance = {
        "geral": tr("Prioridade: investigar perda de resultado, pressão de custos e capacidade de financiar investimentos.", "Priority: investigate declining earnings, cost pressure and investment funding capacity."),
        "cfo": tr("Prioridade: cruzar necessidade de giro, empréstimos e tesouraria para planejar recursos nos anos de maior pressão.", "Priority: compare working capital, loans and treasury balances to plan funding in stressed years."),
        "acionistas": tr("Prioridade: verificar se o crescimento da receita se converte em lucro e caixa antes de avaliar distribuições.", "Priority: check whether revenue growth translates into earnings and cash before assessing distributions."),
        "concedente": tr("Prioridade: acompanhar os anos críticos e a capacidade financeira de manter operação e investimentos previstos.", "Priority: monitor critical years and financial capacity to maintain operations and planned investments."),
    }
    st.write(guidance[ctx.persona])

    if ctx.persona == "geral":
        chart(data, ["dre_receita", "dre_custos", "resultado", "ebitda"], tr("Desempenho geral e pressão dos custos", "Overall performance and cost pressure"))
        chart(data, ["geracao_caixa", "pressao_invest", "caixa_final_sinal"], tr("Capacidade financeira para investir", "Financial capacity to invest"))
    elif ctx.persona == "cfo":
        chart(data, ["NCG", "Saldo_Tesouraria", "emprestimos_cp"], tr("Capital de giro e dependência de empréstimos", "Working capital and reliance on loans"))
        chart(data, ["geracao_caixa", "pressao_invest", "dist_abs", "caixa_final_sinal"], tr("Caixa, investimentos e distribuições", "Cash, investments and distributions"))
        st.caption(tr("Saldo de tesouraria negativo sinaliza empréstimos superiores ao disponível; não equivale, sozinho, a inadimplência. Geração de caixa segue a conta FLU da base.", "Negative treasury means loans exceed available cash; it does not alone establish default. Cash generation follows the source FLU account."))
    elif ctx.persona == "acionistas":
        chart(data, ["dre_receita", "resultado", "dist_abs"], tr("Crescimento, lucro e distribuição de resultados", "Growth, earnings and distributions"))
        chart(data, ["rentabilidade"], tr("Quanto da receita se transforma em lucro?", "How much revenue becomes profit?"), "%")
        chart(data, ["geracao_caixa", "caixa_final_sinal", "emprestimos_cp"], tr("Sustentação financeira dos resultados", "Financial sustainability of earnings"))
        st.caption(tr("Margem líquida = resultado / receita. Ela não mede retorno sobre o capital investido. Distribuições projetadas não demonstram, isoladamente, capacidade de pagar dividendos ou criação de valor.", "Net margin = earnings / revenue, not return on invested capital. Projected distributions alone do not establish dividend capacity or value creation."))
    else:
        chart(data, ["geracao_caixa", "pressao_invest", "caixa_final_sinal"], tr("Recursos para continuidade e investimentos", "Resources for continuity and investments"))
        chart(data, ["liquidez"], tr("Cobertura das obrigações de curto prazo", "Coverage of short-term obligations"), "x")
        st.caption(tr("Estes sinais financeiros apoiam o acompanhamento; a base não comprova cumprimento de obrigações contratuais nem qualidade do serviço.", "These financial signals support monitoring; the dataset does not establish contractual compliance or service quality."))

    st.subheader(tr("Evolução em relação ao ano anterior", "Change from the previous year"))
    history = ctx.foco.sort_values("ano_num").copy()
    names = labels()
    history[tr("Variação da receita (%)", "Revenue change (%)")] = history["dre_receita"].pct_change(fill_method=None).where(history["dre_receita"].shift() > 0) * 100
    history[tr("Variação do resultado (R$)", "Earnings change (R$)")] = history["resultado"].diff()
    extra = list(history.columns[-2:])
    history = history.loc[history["ano_num"].isin(data["ano_num"]), ["ano_num", "dre_receita", "resultado", *extra]]
    st.dataframe(history.rename(columns={"ano_num": tr("Ano", "Year"), **names}), hide_index=True, width="stretch")

    st.subheader(tr("Anos críticos e exposição entre cenários", "Critical years and exposure across scenarios"))
    population = ctx.ind.loc[ctx.ind["ano_num"].isin(data["ano_num"])].copy()
    population["critical"] = critical_flags(population).any(axis=1)
    n = population["CENA"].nunique()
    affected = population.groupby("CENA")["critical"].any().sum()
    st.write(tr(f"{affected} de {n} cenários apresentam pelo menos um sinal no período selecionado.", f"{affected} of {n} scenarios show at least one warning sign in the selected period."))
    st.caption(tr("Frequência empírica, com cenários de mesmo peso; não é probabilidade de falência. Critérios: caixa final < 0, liquidez < 1 ou geração de caixa < 0. Valores ausentes não são classificados.", "Empirical frequency with equal scenario weights, not a bankruptcy probability. Criteria: closing cash < 0, current ratio < 1 or cash generation < 0. Missing values are not classified."))
    table = data[["ano_num", "caixa_final_sinal", "liquidez", "geracao_caixa", "pressao_invest"]].copy()
    table[tr("Sinais de atenção", "Warning signs")] = flags.apply(lambda row: "; ".join(row.index[row]) or "\u2014", axis=1)
    frequencies = population.groupby("ano_num")["critical"].mean() * 100
    table[tr("Cenários com sinais (%)", "Scenarios with warnings (%)")] = table["ano_num"].map(frequencies)
    st.dataframe(table.rename(columns={"ano_num": tr("Ano", "Year"), **names}), hide_index=True, width="stretch")
