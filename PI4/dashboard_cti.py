"""
Dashboard CTI — Capital de Giro, Ciclo Operacional e Ranking
Execute:  streamlit run dashboard_cti.py
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

BASE = Path(__file__).resolve().parent
CSV_PATH = BASE / "Cti.csv"

st.set_page_config(
    page_title="CTI · Painel Financeiro",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Paleta sóbria (infra / concessão)
COR = "#1F4E45"
COR_SUAVE = "#5B8A7A"
COR_ALERTA = "#A65D3F"
COR_OK = "#2F6B4F"


def parse_valor_br(serie: pd.Series) -> pd.Series:
    s = serie.astype("string").str.replace(".", "", regex=False).str.replace(",", ".", regex=False)
    return pd.to_numeric(s, errors="coerce")


def normalizar_conta(serie: pd.Series) -> pd.Series:
    return serie.astype("string").str.replace(r"\s+", " ", regex=True).str.strip()


@st.cache_data(show_spinner="Carregando base CTI…")
def carregar_base() -> pd.DataFrame:
    df = pd.read_csv(CSV_PATH, header=None, names=["ANO", "CENA", "CONTA", "VALOR"])
    df["CONTA"] = normalizar_conta(df["CONTA"])
    df["VALOR"] = parse_valor_br(df["VALOR"])
    df["ano_num"] = df["ANO"].astype(str).str.extract(r"(\d+)")[0].astype("Int64")
    return df


def soma_contas(df: pd.DataFrame, nomes: list[str]) -> pd.DataFrame:
    m = df["CONTA"].isin(nomes)
    return (
        df.loc[m]
        .groupby(["ANO", "ano_num", "CENA"], as_index=False)["VALOR"]
        .sum()
        .rename(columns={"VALOR": "valor"})
    )


@st.cache_data(show_spinner="Calculando indicadores…")
def montar_indicadores(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    contas_receber = soma_contas(
        df,
        [
            "BAL - Contas a Receber - Clientes",
            "BAL - Contas a Receber - Partes Relacionadas",
            "BAL - Contas a Receber - SWAP",
        ],
    ).rename(columns={"valor": "contas_receber"})

    pecas = {
        "estoques": ["BAL - Estoques Diversos"],
        "creditos_tributarios": ["BAL - Créditos Tributários"],
        "fornecedores": ["BAL - Fornecedores"],
        "encargos_sociais": ["BAL - Encargos Sociais e Trabalhistas"],
        "tributos_a_pagar": ["BAL - Tributos a pagar"],
        "disponivel": ["BAL - Disponível"],
        "emprestimos_cp": ["BAL - Empréstimos"],
        "ativo_circ": ["BAL - Ativo Circulante"],
        "passivo_circ": ["BAL - Passivo Circulante"],
        "total_ativo": ["BAL - Total do Ativo"],
        "total_passivo": ["BAL - Total do Passivo"],
        "dre_receita": ["DRE - Receita"],
        "dre_custos": ["DRE - Custos"],
        "resultado": ["DRE - Resultado Líquido"],
        "ebitda": ["DRE - EBITDA"],
        "geracao_caixa": ["FLU - Geração de Caixa"],
    }

    base = contas_receber.copy()
    for nome, contas in pecas.items():
        tmp = soma_contas(df, contas).rename(columns={"valor": nome})
        base = base.merge(tmp, on=["ANO", "ano_num", "CENA"], how="outer")

    base = base.fillna(0)

    base["ACO"] = base["contas_receber"] + base["estoques"] + base["creditos_tributarios"]
    base["PCO"] = base["fornecedores"] + base["encargos_sociais"] + base["tributos_a_pagar"]
    base["NCG"] = base["ACO"] - base["PCO"]
    base["Saldo_Tesouraria"] = base["disponivel"] - base["emprestimos_cp"]

    custos_abs = base["dre_custos"].abs().replace(0, np.nan)
    receita = base["dre_receita"].replace(0, np.nan)
    base["PMR"] = (base["contas_receber"] / receita) * 365
    base["PME"] = (base["estoques"] / custos_abs) * 365
    base["PMP"] = (base["fornecedores"] / custos_abs) * 365
    base["Ciclo_Financeiro"] = base["PMR"] + base["PME"] - base["PMP"]

    base["rentabilidade"] = base["resultado"] / receita
    base["liquidez"] = base["ativo_circ"] / base["passivo_circ"].replace(0, np.nan)
    base["risco"] = base["total_passivo"] / base["total_ativo"].replace(0, np.nan)

    ranking = (
        base.groupby("CENA", as_index=False)
        .agg(
            rentabilidade=("rentabilidade", "mean"),
            liquidez=("liquidez", "mean"),
            risco=("risco", "mean"),
            NCG=("NCG", "mean"),
            Saldo_Tesouraria=("Saldo_Tesouraria", "mean"),
            Ciclo_Financeiro=("Ciclo_Financeiro", "mean"),
            receita=("dre_receita", "mean"),
            resultado=("resultado", "mean"),
        )
    )

    q_rent = ranking["rentabilidade"].quantile([0.25, 0.75])
    q_liq = ranking["liquidez"].quantile([0.25, 0.75])
    q_risco = ranking["risco"].quantile([0.25, 0.75])

    ranking["Alta rentabilidade"] = ranking["rentabilidade"] >= q_rent[0.75]
    ranking["Retorno moderado"] = ranking["rentabilidade"].between(
        q_rent[0.25], q_rent[0.75], inclusive="left"
    )
    ranking["Alta liquidez"] = ranking["liquidez"] >= q_liq[0.75]
    ranking["Baixa liquidez"] = ranking["liquidez"] <= q_liq[0.25]
    ranking["Baixo risco"] = ranking["risco"] <= q_risco[0.25]
    ranking["Alto risco"] = ranking["risco"] >= q_risco[0.75]

    return base, ranking


def fmt_rs(x: float) -> str:
    if pd.isna(x):
        return "—"
    sinal = "-" if x < 0 else ""
    v = abs(x)
    if v >= 1e9:
        return f"{sinal}R$ {v/1e9:,.2f} bi".replace(",", "X").replace(".", ",").replace("X", ".")
    if v >= 1e6:
        return f"{sinal}R$ {v/1e6:,.2f} mi".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{sinal}R$ {v:,.0f}".replace(",", "X").replace(".", ",").replace("X", ".")


def fmt_dias(x: float) -> str:
    if pd.isna(x):
        return "—"
    return f"{x:,.1f} dias".replace(",", "X").replace(".", ",").replace("X", ".")


def fmt_pct(x: float) -> str:
    if pd.isna(x):
        return "—"
    return f"{x*100:,.2f}%".replace(",", "X").replace(".", ",").replace("X", ".")


def texto_ncg(ncg: float) -> str:
    if pd.isna(ncg):
        return "Sem dado"
    if ncg > 0:
        return "A operação consome caixa: clientes/estoques prendem mais recurso do que fornecedores financiam."
    if ncg < 0:
        return "A operação gera caixa: fornecedores e obrigações financiam parte do giro."
    return "NCG equilibrada."


def texto_tesouraria(saldo: float) -> str:
    if pd.isna(saldo):
        return "Sem dado"
    if saldo >= 0:
        return "Caixa disponível cobre (ou supera) os empréstimos de curto prazo — menor dependência de banco no dia a dia."
    return "Empréstimos de curto prazo superam o disponível — a empresa depende de bancos para financiar a rotina."


def texto_ciclo(dias: float) -> str:
    if pd.isna(dias):
        return "Sem dado"
    if dias > 30:
        return f"Ciclo longo ({fmt_dias(dias)}): a empresa precisa financiar a operação com recurso próprio por mais tempo."
    if dias > 0:
        return f"Ciclo positivo moderado ({fmt_dias(dias)}): ainda há intervalo a financiar entre pagar e receber."
    return f"Ciclo negativo ({fmt_dias(dias)}): a empresa recebe antes de pagar — situação favorável de caixa."


# -----------------------------------------------------------------------------
# UI
# -----------------------------------------------------------------------------
st.title("Painel financeiro CTI")
st.caption(
    "Leitura humana dos cenários de planejamento · capital de giro, prazos médios e ranking de risco/retorno"
)

if not CSV_PATH.exists():
    st.error(f"Arquivo não encontrado: {CSV_PATH}")
    st.stop()

df = carregar_base()
ind, ranking = montar_indicadores(df)

with st.sidebar:
    st.header("Filtros")
    anos = sorted(ind["ano_num"].dropna().unique().tolist())
    ano_sel = st.selectbox("Ano do horizonte", options=["Todos"] + anos, index=0)

    cenas = sorted(ind["CENA"].dropna().unique().tolist())
    cena_padrao = cenas[0] if cenas else None
    cena_sel = st.selectbox("Cenário em foco", options=cenas, index=0 if cena_padrao else 0)

    st.markdown("---")
    st.markdown(
        f"**Base:** `{CSV_PATH.name}`  \n"
        f"**Linhas brutas:** {len(df):,}  \n"
        f"**Cenários:** {ind['CENA'].nunique():,}  \n"
        f"**Anos:** {ind['ano_num'].nunique()}"
    )

ind_ano = ind if ano_sel == "Todos" else ind[ind["ano_num"] == ano_sel]
foco = ind[ind["CENA"] == cena_sel].sort_values("ano_num")
if ano_sel != "Todos":
    foco_ano = foco[foco["ano_num"] == ano_sel]
else:
    foco_ano = foco

# KPIs do cenário em foco (média no filtro de ano)
k = foco_ano[
    ["NCG", "Saldo_Tesouraria", "Ciclo_Financeiro", "PMR", "PME", "PMP", "liquidez", "rentabilidade", "risco"]
].mean(numeric_only=True)

st.subheader(f"Cenário em foco: `{cena_sel}`")
if ano_sel == "Todos":
    st.write("Valores médios ao longo dos 12 anos do horizonte.")
else:
    st.write(f"Valores do **Ano {ano_sel}**.")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Necessidade de Capital de Giro (NCG)", fmt_rs(k["NCG"]))
c2.metric("Saldo de Tesouraria", fmt_rs(k["Saldo_Tesouraria"]))
c3.metric("Ciclo Financeiro", fmt_dias(k["Ciclo_Financeiro"]))
c4.metric("Liquidez corrente", f"{k['liquidez']:.2f}x" if pd.notna(k["liquidez"]) else "—")

st.info(texto_ncg(k["NCG"]))
col_a, col_b = st.columns(2)
col_a.success(texto_tesouraria(k["Saldo_Tesouraria"]))
col_b.warning(texto_ciclo(k["Ciclo_Financeiro"]))

aba1, aba2, aba3, aba4 = st.tabs(
    ["Capital de giro", "Prazos e ciclo", "Ranking dos cenários", "Como ler estes números"]
)

with aba1:
    st.markdown("#### Evolução no tempo (cenário selecionado)")
    fig_ncg = px.line(
        foco,
        x="ano_num",
        y=["NCG", "Saldo_Tesouraria"],
        markers=True,
        labels={"ano_num": "Ano", "value": "R$", "variable": "Indicador"},
        color_discrete_map={"NCG": COR, "Saldo_Tesouraria": COR_SUAVE},
        title="NCG × Saldo de Tesouraria ao longo do horizonte",
    )
    fig_ncg.update_layout(legend_title_text="", hovermode="x unified")
    st.plotly_chart(fig_ncg, use_container_width=True)

    st.markdown("#### De onde vem a NCG")
    decomp = foco_ano[["ACO", "PCO", "NCG"]].mean()
    decomp_df = pd.DataFrame(
        {
            "Componente": [
                "Ativo circulante operacional (receber + estoques + créditos)",
                "Passivo circulante operacional (fornecedores + encargos + tributos)",
                "NCG (= ACO − PCO)",
            ],
            "Valor": [decomp["ACO"], decomp["PCO"], decomp["NCG"]],
        }
    )
    fig_bar = px.bar(
        decomp_df,
        x="Componente",
        y="Valor",
        text=[fmt_rs(v) for v in decomp_df["Valor"]],
        color="Componente",
        color_discrete_sequence=[COR_SUAVE, COR_ALERTA, COR],
        title="Composição da Necessidade de Capital de Giro",
    )
    fig_bar.update_layout(showlegend=False, xaxis_title="", yaxis_title="R$")
    fig_bar.update_traces(textposition="outside")
    st.plotly_chart(fig_bar, use_container_width=True)

with aba2:
    st.markdown("#### Prazos médios (dias)")
    p1, p2, p3, p4 = st.columns(4)
    p1.metric("PMR — receber de clientes", fmt_dias(k["PMR"]))
    p2.metric("PME — giro de estoque", fmt_dias(k["PME"]))
    p3.metric("PMP — pagar fornecedores", fmt_dias(k["PMP"]))
    p4.metric("Ciclo financeiro", fmt_dias(k["Ciclo_Financeiro"]))

    fig_prazos = px.line(
        foco,
        x="ano_num",
        y=["PMR", "PME", "PMP", "Ciclo_Financeiro"],
        markers=True,
        labels={"ano_num": "Ano", "value": "Dias", "variable": "Prazo"},
        title="Trajetória dos prazos médios no horizonte",
    )
    fig_prazos.update_layout(legend_title_text="", hovermode="x unified")
    st.plotly_chart(fig_prazos, use_container_width=True)

    st.markdown(
        """
**Em linguagem simples**

- **PMR alto** → clientes demoram a pagar → mais caixa preso.
- **PMP alto** → fornecedores dão mais prazo → ajuda o caixa.
- **Ciclo financeiro** = quantos dias a empresa precisa “adiantar” do próprio bolso.
"""
    )

with aba3:
    st.markdown("#### Perfil dos cenários (média no horizonte)")
    cats = st.multiselect(
        "Filtrar por selo",
        options=[
            "Alta rentabilidade",
            "Retorno moderado",
            "Alta liquidez",
            "Baixa liquidez",
            "Baixo risco",
            "Alto risco",
        ],
        default=[],
    )
    rank_view = ranking.copy()
    if cats:
        mask = np.zeros(len(rank_view), dtype=bool)
        for c in cats:
            mask |= rank_view[c].to_numpy()
        rank_view = rank_view.loc[mask]

    # Plotly exige size >= 0; liquidez pode ser negativa em alguns cenários
    rank_view = rank_view.copy()
    rank_view["liquidez_plot"] = rank_view["liquidez"].clip(lower=0).fillna(0)

    fig_scatter = px.scatter(
        rank_view,
        x="risco",
        y="rentabilidade",
        size="liquidez_plot",
        hover_name="CENA",
        hover_data={"liquidez": ":.2f", "liquidez_plot": False},
        color="Ciclo_Financeiro",
        color_continuous_scale="Tealgrn",
        size_max=28,
        labels={
            "risco": "Risco (Passivo / Ativo)",
            "rentabilidade": "Rentabilidade (Resultado / Receita)",
            "liquidez_plot": "Liquidez (≥0)",
            "Ciclo_Financeiro": "Ciclo (dias)",
        },
        title="Mapa risco × retorno (tamanho = liquidez; negativas viram 0)",
    )
    st.plotly_chart(fig_scatter, use_container_width=True)

    contagem = {
        "Alta rentabilidade": int(ranking["Alta rentabilidade"].sum()),
        "Retorno moderado": int(ranking["Retorno moderado"].sum()),
        "Alta liquidez": int(ranking["Alta liquidez"].sum()),
        "Baixa liquidez": int(ranking["Baixa liquidez"].sum()),
        "Baixo risco": int(ranking["Baixo risco"].sum()),
        "Alto risco": int(ranking["Alto risco"].sum()),
    }
    cont_df = pd.DataFrame({"Categoria": list(contagem.keys()), "Cenários": list(contagem.values())})
    fig_cat = px.bar(
        cont_df,
        x="Categoria",
        y="Cenários",
        text="Cenários",
        color="Categoria",
        color_discrete_sequence=[COR, COR_SUAVE, COR_OK, COR_ALERTA, "#3D6B5A", "#8B4513"],
        title="Quantos cenários caem em cada selo (quartis)",
    )
    fig_cat.update_layout(showlegend=False, xaxis_title="", yaxis_title="Nº de cenários")
    st.plotly_chart(fig_cat, use_container_width=True)

    show = rank_view.sort_values("rentabilidade", ascending=False).head(20).copy()
    show["rentabilidade"] = show["rentabilidade"].map(fmt_pct)
    show["liquidez"] = show["liquidez"].map(lambda x: f"{x:.2f}x" if pd.notna(x) else "—")
    show["risco"] = show["risco"].map(lambda x: f"{x:.2%}" if pd.notna(x) else "—")
    show["NCG"] = show["NCG"].map(fmt_rs)
    show["Ciclo_Financeiro"] = show["Ciclo_Financeiro"].map(fmt_dias)
    st.dataframe(
        show[
            [
                "CENA",
                "rentabilidade",
                "liquidez",
                "risco",
                "NCG",
                "Ciclo_Financeiro",
                "Alta rentabilidade",
                "Alta liquidez",
                "Baixa liquidez",
                "Baixo risco",
                "Alto risco",
            ]
        ],
        use_container_width=True,
        hide_index=True,
    )

with aba4:
    st.markdown(
        f"""
### O que este painel responde

1. **A operação come ou gera caixa?** → olhe a **NCG**.  
2. **Dependemos de banco no curto prazo?** → olhe o **Saldo de Tesouraria**.  
3. **Por quantos dias financiamos a operação?** → olhe o **Ciclo Financeiro**.  
4. **Entre os {ranking.shape[0]:,} cenários, quais são mais rentáveis / líquidos / arriscados?** → aba Ranking.

### Fórmulas (iguais às do notebook)

| Indicador | Fórmula |
|---|---|
| NCG | (Contas a Receber + Estoques + Créditos Tributários) − (Fornecedores + Encargos + Tributos a Pagar) |
| Saldo de Tesouraria | Disponível − Empréstimos CP |
| PMR | (Contas a Receber / Receita) × 365 |
| PME | (Estoques / abs(Custos)) × 365 |
| PMP | (Fornecedores / abs(Custos)) × 365 |
| Ciclo Financeiro | PMR + PME − PMP |

Cenário atual em destaque: **{cena_sel}** · Rentabilidade {fmt_pct(k["rentabilidade"])} · Risco {fmt_pct(k["risco"]) if pd.notna(k["risco"]) else "—"}.
"""
    )

st.markdown("---")
st.caption("CTI · Dashboard de planejamento financeiro · dados: Cti.csv")
