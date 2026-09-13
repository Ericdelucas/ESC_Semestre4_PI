"""
Painel financeiro CTI — entrada principal (< 100 linhas).

Execute:
  py -m streamlit run app.py
  py -m streamlit run dashboard_cti.py
"""

from __future__ import annotations

import streamlit as st

from src.components.headers import banner_auditoria_filtro, expander_auditoria_base, render_titulo
from src.components.kpis import kpis_por_persona, render_kpi_row
from src.components.resilience import safe_render
from src.components.sidebar import render_persona, render_sidebar
from src.config import CSV_PATH
from src.data.analytics import cena_rotulo, montar_indicadores, probabilidade_caixa_negativo
from src.data.formatting import texto_ciclo, texto_ncg, texto_tesouraria
from src.data.loaders import load_cti_csv
from src.views import capital_giro, comparar, como_ler, distribuicao, faixa_risco, mapeamento_risco, prazos_ciclo

st.set_page_config(page_title="CTI · Painel Financeiro", page_icon="📊", layout="wide", initial_sidebar_state="expanded")


@st.cache_data(show_spinner="Carregando base CTI…")
def _carregar_base():
    return load_cti_csv(CSV_PATH)


@st.cache_data(show_spinner="Calculando indicadores…")
def _montar_indicadores(df):
    return montar_indicadores(df)


def main() -> None:
    render_titulo()
    if not CSV_PATH.exists():
        st.error(f"Arquivo não encontrado: {CSV_PATH}")
        st.stop()

    df = safe_render("base de dados", _carregar_base)
    if df is None:
        st.stop()
    resultado = safe_render("indicadores financeiros", _montar_indicadores, df)
    if resultado is None:
        st.stop()
    ind, ranking = resultado
    ranking = ranking.copy()
    ranking["rotulo"] = ranking["CENA"].map(cena_rotulo)
    mapa_rotulo = dict(zip(ranking["rotulo"], ranking["CENA"], strict=False))
    n_cenarios = int(ranking["CENA"].nunique())
    ano_enc = int(ranking["ano_encerramento"].iloc[0]) if len(ranking) else 12
    p_ruina = probabilidade_caixa_negativo(ranking)

    ano_sel, cena_sel, anos, cenas = render_sidebar(df, ind, n_cenarios)
    persona = render_persona()
    foco = ind[ind["CENA"] == cena_sel].sort_values("ano_num")
    foco_ano = foco if ano_sel == "Todos" else foco[foco["ano_num"] == ano_sel]
    k = foco_ano[["NCG", "Saldo_Tesouraria", "Ciclo_Financeiro", "PMR", "PME", "PMP", "liquidez", "rentabilidade", "risco", "resultado"]].mean(numeric_only=True)

    st.subheader(f"Cenário em foco: `{cena_sel}`")
    safe_render("banner de auditoria", banner_auditoria_filtro, cena_sel, ano_sel)
    st.write("Valores médios ao longo dos 12 anos." if ano_sel == "Todos" else f"Valores do **Ano {ano_sel}**.")
    render_kpi_row(kpis_por_persona(persona, k, ranking))
    if persona == "Visão Geral":
        st.info(texto_ncg(k["NCG"]))
        a, b = st.columns(2)
        a.success(texto_tesouraria(k["Saldo_Tesouraria"]))
        b.warning(texto_ciclo(k["Ciclo_Financeiro"]))
    elif persona == "CFO & Credores":
        st.info("Foco em solvência, giro e capacidade de honrar dívida no curto prazo.")
    elif persona == "Acionistas":
        st.info("Foco em retorno, resultado e liquidez que sustenta distribuição.")
    else:
        st.info("Foco em continuidade operacional, caixa de encerramento e sustentabilidade do horizonte.")
    safe_render("auditoria da base", expander_auditoria_base, df, cena_sel, ano_sel)

    abas = st.tabs(["Capital de giro", "Prazos e ciclo", "Mapeamento de Risco × Retorno", "Distribuição & Probabilidades", "Faixa de risco", "Comparar cenários", "Como ler estes números"])
    with abas[0]:
        safe_render("aba Capital de giro", capital_giro.render, foco, foco_ano, cena_sel, ano_sel)
    with abas[1]:
        safe_render("aba Prazos e ciclo", prazos_ciclo.render, foco, k, cena_sel, ano_sel)
    with abas[2]:
        safe_render("aba Mapeamento de Risco × Retorno", mapeamento_risco.render, ranking, persona, cenas, mapa_rotulo, n_cenarios)
    with abas[3]:
        safe_render("aba Distribuição & Probabilidades", distribuicao.render, ranking, ano_enc, n_cenarios, p_ruina)
    with abas[4]:
        safe_render("aba Faixa de risco", faixa_risco.render, ind, cena_sel, ano_sel, anos)
    with abas[5]:
        safe_render("aba Comparar cenários", comparar.render, ind, cenas, cena_sel, ano_sel)
    with abas[6]:
        safe_render("aba Como ler", como_ler.render, n_cenarios, cena_sel, k, ano_enc, p_ruina)
    st.markdown("---")
    st.caption("CTI · Dashboard modular · dados: Cti.csv")


main()
