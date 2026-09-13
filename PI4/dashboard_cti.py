"""
Dashboard CTI — Capital de Giro, Ciclo Operacional e Ranking
Execute:  python dashboard_cti.py
     ou:  .venv/bin/streamlit run dashboard_cti.py
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
CSV_PATH = BASE / "Cti.csv"
VENV_PY = BASE / ".venv" / "bin" / "python"


def _usar_venv_se_preciso() -> None:
    """Se o Python do sistema não tem as libs, relança no .venv.

    Os imports abaixo são intencionais: precisam ocorrer antes do import
    definitivo, senão o Python do sistema quebra com ModuleNotFoundError.
    Não comparar sys.executable com .venv/bin/python: no Debian esse
    arquivo é um symlink para o Python do sistema.
    """
    if not VENV_PY.exists():
        return
    if Path(sys.prefix).resolve() == (BASE / ".venv").resolve():
        return
    try:
        import numpy  # noqa: F401
        import streamlit  # noqa: F401
    except ModuleNotFoundError:
        os.execv(str(VENV_PY), [str(VENV_PY), str(Path(__file__).resolve()), *sys.argv[1:]])


_usar_venv_se_preciso()

try:
    import numpy as np
    import pandas as pd
    import plotly.express as px
    import plotly.graph_objects as go
    import streamlit as st
    from streamlit.runtime.scriptrunner import get_script_run_ctx
    from streamlit.web import cli as stcli
except ModuleNotFoundError as exc:
    print(
        "Dependências não encontradas. No diretório PI4, use o ambiente virtual:\n"
        f"  {VENV_PY} {Path(__file__).resolve().name}\n"
        f"Detalhe: {exc}",
        file=sys.stderr,
    )
    raise SystemExit(1)


def _assegurar_streamlit() -> None:
    """Permite `python dashboard_cti.py` além de `streamlit run`."""
    if get_script_run_ctx() is not None:
        return
    sys.argv = ["streamlit", "run", str(Path(__file__).resolve()), *sys.argv[1:]]
    raise SystemExit(stcli.main())


_assegurar_streamlit()

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
COR_ANCORA = "#E8C07A"


def parse_valor_br(serie: pd.Series) -> pd.Series:
    s = serie.astype("string").str.replace(".", "", regex=False).str.replace(",", ".", regex=False)
    return pd.to_numeric(s, errors="coerce")


def normalizar_conta(serie: pd.Series) -> pd.Series:
    return serie.astype("string").str.replace(r"\s+", " ", regex=True).str.strip()


def magnitude(serie: pd.Series) -> pd.Series:
    """O Cti.csv mistura débito (+) e crédito (−) nos saldos do BP.

    Indicadores de giro e liquidez usam o valor absoluto (quanto há / quanto se deve).
    """
    return serie.abs()


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

    # Ativos operacionais (débito, em geral positivos)
    base["ACO"] = (
        magnitude(base["contas_receber"])
        + magnitude(base["estoques"])
        + magnitude(base["creditos_tributarios"])
    )
    # Fornecedores / encargos / tributos vêm como crédito (−). PCO = valor devido.
    base["PCO"] = magnitude(
        base["fornecedores"] + base["encargos_sociais"] + base["tributos_a_pagar"]
    )
    base["NCG"] = base["ACO"] - base["PCO"]
    base["Saldo_Tesouraria"] = magnitude(base["disponivel"]) - magnitude(base["emprestimos_cp"])

    custos_abs = base["dre_custos"].abs().replace(0, np.nan)
    receita = base["dre_receita"].replace(0, np.nan)
    base["PMR"] = (magnitude(base["contas_receber"]) / receita) * 365
    base["PME"] = (magnitude(base["estoques"]) / custos_abs) * 365
    base["PMP"] = (magnitude(base["fornecedores"]) / custos_abs) * 365
    base["Ciclo_Financeiro"] = base["PMR"] + base["PME"] - base["PMP"]

    base["rentabilidade"] = base["resultado"] / receita
    # PC (e, em alguns anos, AC) vem com sinal de crédito. Sem abs: 1,80 bi / (−1,08 bi) = −1,66x.
    base["liquidez"] = magnitude(base["ativo_circ"]) / magnitude(base["passivo_circ"]).replace(0, np.nan)
    base["risco"] = magnitude(base["total_passivo"]) / magnitude(base["total_ativo"]).replace(0, np.nan)

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


METRICAS_NUVEM: dict[str, tuple[str, bool]] = {
    "Caixa disponível": ("disponivel", True),
    "Geração de caixa": ("geracao_caixa", True),
    "Saldo de tesouraria": ("Saldo_Tesouraria", True),
    "NCG": ("NCG", False),
}

CORES_COMPARA = [COR, COR_ALERTA, "#3D6B5A"]

# (x, y_paper, texto, cor) — y_paper defasado para as caixas não colidirem
MARCOS_HORIZONTE: tuple[tuple[float, float, str, str], ...] = (
    (9.5, 1.16, "Anos 8–11: ciclo pleno / alta de caixa", COR_SUAVE),
    (12.0, 1.04, "Ano 12: encerramento de contrato / liquidação de ativos", COR_ALERTA),
)


def nome_amigavel(cena: object) -> str:
    """Total Cen_00006 → Cenário 6 (rótulo executivo; o código interno segue no filtro)."""
    achado = re.search(r"(\d+)", str(cena))
    if achado is None:
        return str(cena)
    return f"Cenário {int(achado.group(1))}"


def anotar_marcos_negocio(fig: go.Figure) -> go.Figure:
    for x, y_paper, texto, cor in MARCOS_HORIZONTE:
        fig.add_annotation(
            x=x,
            y=y_paper,
            yref="paper",
            text=texto,
            showarrow=False,
            font={"size": 11, "color": cor},
            bgcolor="rgba(17, 17, 17, 0.55)",
            bordercolor=cor,
            borderpad=4,
            align="center",
            xanchor="center",
        )
    fig.update_layout(margin={"t": 132})
    return fig


@st.cache_data(show_spinner=False)
def resumo_envelope(ind: pd.DataFrame, coluna: str, maior_e_melhor: bool) -> pd.DataFrame:
    g = ind.groupby("ano_num")[coluna]
    out = pd.DataFrame(
        {
            "ano_num": g.mean().index.astype(int),
            "media": g.mean().to_numpy(),
            "mediana": g.median().to_numpy(),
            "p5": g.quantile(0.05).to_numpy(),
            "p95": g.quantile(0.95).to_numpy(),
            "minimo": g.min().to_numpy(),
            "maximo": g.max().to_numpy(),
        }
    )
    if maior_e_melhor:
        out["otimista"] = out["maximo"]
        out["pessimista"] = out["minimo"]
    else:
        out["otimista"] = out["minimo"]
        out["pessimista"] = out["maximo"]
    return out


def recorte_label(ano_sel: str | int) -> str:
    return "Todos" if ano_sel == "Todos" else f"Ano {ano_sel}"


def titulo_filtro(assunto: str, cena_sel: str, ano_sel: str | int) -> str:
    return f"{assunto} — Cenário Foco: {nome_amigavel(cena_sel)} | Recorte: {recorte_label(ano_sel)}"


def ancorar_ano_temporal(
    fig: go.Figure,
    dados: pd.DataFrame,
    y_cols: list[str],
    ano_sel: str | int,
) -> go.Figure:
    """Linha vertical + marcador no ano filtrado. Sem recorte anual, não altera o gráfico."""
    if ano_sel == "Todos":
        return fig
    ano = int(ano_sel)
    fig.add_vline(
        x=ano,
        line_dash="dash",
        line_color=COR_ANCORA,
        line_width=2,
        annotation_text=f"Filtro: Ano {ano}",
        annotation_position="top",
        annotation_font={"color": COR_ANCORA, "size": 12},
    )
    ponto = dados.loc[dados["ano_num"] == ano]
    if ponto.empty:
        return fig
    primeira = True
    for col in y_cols:
        fig.add_trace(
            go.Scatter(
                x=ponto["ano_num"],
                y=ponto[col],
                mode="markers",
                marker={
                    "size": 16,
                    "color": COR_ANCORA,
                    "symbol": "diamond",
                    "line": {"width": 2, "color": "#111111"},
                },
                name=f"Âncora do filtro (Ano {ano})",
                showlegend=primeira,
                hovertemplate=f"{col}<br>Ano {ano}: %{{y}}<extra></extra>",
            )
        )
        primeira = False
    return fig


def figura_envelope(
    ind: pd.DataFrame,
    coluna: str,
    rotulo: str,
    maior_e_melhor: bool,
    *,
    titulo: str | None = None,
    ano_destaque: int | None = None,
    cena_destaque: str | None = None,
    mostrar_pontos: bool = False,
    mostrar_media: bool = False,
) -> go.Figure:
    env = resumo_envelope(ind, coluna, maior_e_melhor)
    fig = go.Figure()
    # 1) faixa ao fundo
    fig.add_trace(
        go.Scatter(
            x=env["ano_num"],
            y=env["p95"],
            mode="lines",
            line={"width": 0},
            showlegend=False,
            hoverinfo="skip",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=env["ano_num"],
            y=env["p5"],
            mode="lines",
            line={"width": 0},
            fill="tonexty",
            fillcolor="rgba(31, 78, 69, 0.18)",
            name="Faixa 5–95%",
            showlegend=True,
            hoverinfo="skip",
        )
    )
    # 2) pontos na frente da faixa (só se o seletor estiver ligado)
    if mostrar_pontos:
        rng = np.random.default_rng(42)
        x_nuvem = ind["ano_num"].to_numpy(dtype=float) + rng.uniform(-0.22, 0.22, len(ind))
        fig.add_trace(
            go.Scatter(
                x=x_nuvem,
                y=ind[coluna],
                mode="markers",
                marker={"size": 8, "color": COR_SUAVE, "opacity": 0.38},
                name="Todos os cenários",
                showlegend=True,
                hoverinfo="skip",
            )
        )
    # 3) linhas centrais por cima
    fig.add_trace(
        go.Scatter(
            x=env["ano_num"],
            y=env["mediana"],
            mode="lines+markers",
            line={"color": COR, "width": 3},
            name="Mais provável (mediana)",
            showlegend=True,
        )
    )
    if mostrar_media:
        fig.add_trace(
            go.Scatter(
                x=env["ano_num"],
                y=env["media"],
                mode="lines",
                line={"color": COR, "width": 1.5, "dash": "dot"},
                name="Média",
                showlegend=True,
            )
        )
    fig.add_trace(
        go.Scatter(
            x=env["ano_num"],
            y=env["pessimista"],
            mode="lines+markers",
            line={"color": COR_ALERTA, "width": 2},
            name="Pessimista (pior caso)",
            showlegend=True,
        )
    )
    fig.add_trace(
        go.Scatter(
            x=env["ano_num"],
            y=env["otimista"],
            mode="lines+markers",
            line={"color": COR_OK, "width": 2},
            name="Otimista (melhor caso)",
            showlegend=True,
        )
    )
    fig.update_layout(
        title=titulo
        or f"Faixa de risco — {rotulo} nos 12 anos ({ind['CENA'].nunique():,} cenários)",
        xaxis_title="Ano",
        yaxis_title=rotulo,
        hovermode="x unified",
        legend_title_text="",
        legend={"traceorder": "normal"},
    )
    if ano_destaque is not None:
        fig.add_vline(
            x=ano_destaque,
            line_dash="dash",
            line_color=COR_ANCORA,
            line_width=2,
            annotation_text=f"Filtro: Ano {ano_destaque}",
            annotation_position="top",
            annotation_font={"color": COR_ANCORA, "size": 12},
        )
        if cena_destaque is not None:
            ancora = ind.loc[(ind["CENA"] == cena_destaque) & (ind["ano_num"] == ano_destaque)]
            if not ancora.empty:
                fig.add_trace(
                    go.Scatter(
                        x=ancora["ano_num"],
                        y=ancora[coluna],
                        mode="markers",
                        marker={
                            "size": 16,
                            "color": COR_ANCORA,
                            "symbol": "diamond",
                            "line": {"width": 2, "color": "#111111"},
                        },
                        name=f"Âncora · {nome_amigavel(cena_destaque)} · Ano {ano_destaque}",
                        hovertemplate=f"{nome_amigavel(cena_destaque)}<br>Ano {ano_destaque}: %{{y}}<extra></extra>",
                    )
                )
    return anotar_marcos_negocio(fig)


def figura_histograma_ano(
    fatia: pd.DataFrame,
    coluna: str,
    rotulo: str,
    ano: int,
    *,
    titulo: str | None = None,
) -> go.Figure:
    serie = fatia[coluna].dropna()
    fig = px.histogram(
        fatia,
        x=coluna,
        nbins=40,
        histnorm="probability",
        color_discrete_sequence=[COR_SUAVE],
        title=titulo or f"Distribuição de {rotulo} no Ano {ano} ({len(serie):,} cenários)",
        labels={coluna: rotulo, "probability": "Probabilidade"},
    )
    fig.update_layout(yaxis_title="Probabilidade (fração dos cenários)", bargap=0.05)
    if serie.empty:
        return fig
    marcas = [
        (float(serie.median()), COR, "Mediana"),
        (float(serie.mean()), COR, "Média"),
        (float(serie.min()), COR_ALERTA, "Pior caso"),
        (float(serie.max()), COR_OK, "Melhor caso"),
    ]
    dash = {"Mediana": "solid", "Média": "dot", "Pior caso": "dash", "Melhor caso": "dash"}
    for valor, cor, nome in marcas:
        fig.add_vline(
            x=valor,
            line_color=cor,
            line_dash=dash[nome],
            line_width=2,
            annotation_text=f"{nome}: {fmt_rs(valor)}",
            annotation_position="top",
        )
    return fig


def cenas_padrao_comparacao(cenas: list[str]) -> list[str]:
    escolhidas: list[str] = []
    for alvo in ("00001", "00500"):
        match = next((c for c in cenas if alvo in str(c)), None)
        if match is not None:
            escolhidas.append(match)
    if len(escolhidas) < 2:
        return cenas[:2]
    return escolhidas[:2]


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


def banner_auditoria_filtro(cena_sel: str, ano_sel: str | int) -> None:
    ano_txt = "Todos" if ano_sel == "Todos" else str(ano_sel)
    st.markdown(
        f"""
<div style="
    background: linear-gradient(90deg, rgba(232,192,122,0.16), rgba(91,138,122,0.10));
    border: 1px solid #C4A15A;
    border-left: 6px solid {COR_ANCORA};
    border-radius: 8px;
    padding: 0.8rem 1.1rem;
    margin: 0.15rem 0 0.85rem 0;
    font-size: 1.05rem;
    font-weight: 600;
    letter-spacing: 0.01em;
    line-height: 1.45;
">
📌 Exibindo dados de: {nome_amigavel(cena_sel)} | Ano {ano_txt}
</div>
""",
        unsafe_allow_html=True,
    )


def expander_auditoria_base(df: pd.DataFrame, cena_sel: str, ano_sel: str | int) -> None:
    bruto = df.loc[df["CENA"] == cena_sel]
    if ano_sel != "Todos":
        bruto = bruto.loc[bruto["ano_num"] == ano_sel]
    n = len(bruto)
    with st.expander("🔍 Conferir dados brutos (Auditoria)"):
        st.caption(
            f"{n:,} registros encontrados para **{nome_amigavel(cena_sel)}** "
            f"(código `{cena_sel}`) · recorte **{recorte_label(ano_sel)}**."
        )
        if n == 0:
            st.warning("Nenhuma linha da base corresponde a este recorte.")
            return
        visao = bruto[["ANO", "CENA", "CONTA", "VALOR"]].copy()
        st.dataframe(visao, width="stretch", hide_index=True)


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
    anos = sorted(int(a) for a in ind["ano_num"].dropna().unique().tolist())
    ano_sel = st.selectbox("Ano do horizonte", options=["Todos", *anos], index=0)

    cenas = sorted(ind["CENA"].dropna().unique().tolist())
    cena_padrao = cenas[0] if cenas else None
    cena_sel = st.selectbox(
        "Cenário em foco",
        options=cenas,
        index=0 if cena_padrao else 0,
        format_func=nome_amigavel,
    )

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

st.subheader(f"Cenário em foco: {nome_amigavel(cena_sel)}")
st.caption(f"Código interno da base: `{cena_sel}`")
banner_auditoria_filtro(cena_sel, ano_sel)
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

expander_auditoria_base(df, cena_sel, ano_sel)

aba1, aba2, aba3, aba_risco, aba_comp, aba4 = st.tabs(
    [
        "Capital de giro",
        "Prazos e ciclo",
        "Ranking dos cenários",
        "Faixa de risco",
        "Comparar cenários",
        "Como ler estes números",
    ]
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
        title=titulo_filtro("Evolução Temporal", cena_sel, ano_sel),
    )
    fig_ncg.update_layout(legend_title_text="", hovermode="x unified")
    fig_ncg = ancorar_ano_temporal(fig_ncg, foco, ["NCG", "Saldo_Tesouraria"], ano_sel)
    fig_ncg = anotar_marcos_negocio(fig_ncg)
    st.plotly_chart(fig_ncg, width="stretch", theme="streamlit")

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
        title=titulo_filtro("Composição da NCG", cena_sel, ano_sel),
    )
    fig_bar.update_layout(showlegend=False, xaxis_title="", yaxis_title="R$")
    fig_bar.update_traces(textposition="outside")
    st.plotly_chart(fig_bar, width="stretch", theme="streamlit")

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
        title=titulo_filtro("Trajetória dos prazos médios", cena_sel, ano_sel),
    )
    fig_prazos.update_layout(legend_title_text="", hovermode="x unified")
    fig_prazos = ancorar_ano_temporal(fig_prazos, foco, ["PMR", "PME", "PMP", "Ciclo_Financeiro"], ano_sel)
    fig_prazos = anotar_marcos_negocio(fig_prazos)
    st.plotly_chart(fig_prazos, width="stretch", theme="streamlit")

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

    rank_view = rank_view.copy()
    rank_view["liquidez_plot"] = rank_view["liquidez"].fillna(0)
    rank_view["Cenario"] = rank_view["CENA"].map(nome_amigavel)

    fig_scatter = px.scatter(
        rank_view,
        x="risco",
        y="rentabilidade",
        size="liquidez_plot",
        hover_name="Cenario",
        hover_data={"liquidez": ":.2f", "liquidez_plot": False},
        color="Ciclo_Financeiro",
        color_continuous_scale="Tealgrn",
        size_max=28,
        labels={
            "risco": "Risco (Passivo / Ativo)",
            "rentabilidade": "Rentabilidade (Resultado / Receita)",
            "liquidez_plot": "Liquidez",
            "Ciclo_Financeiro": "Ciclo (dias)",
        },
        title=titulo_filtro("Mapa risco × retorno (tamanho = liquidez)", cena_sel, ano_sel),
    )
    risco_plot = rank_view["risco"].dropna()
    if not risco_plot.empty:
        q_lo = float(risco_plot.quantile(0.02))
        q_hi = float(risco_plot.quantile(0.98))
        amplitude = q_hi - q_lo
        if amplitude < 1e-3:
            centro = float(risco_plot.median())
            xmin, xmax = centro - 0.012, centro + 0.012
        else:
            margem = max(amplitude * 0.18, 0.004)
            xmin, xmax = q_lo - margem, q_hi + margem
        fig_scatter.update_xaxes(range=[xmin, xmax], tickformat=".3f", nticks=7)
    else:
        fig_scatter.update_xaxes(tickformat=".3f")
    fig_scatter.update_yaxes(tickformat=".2%")
    st.plotly_chart(fig_scatter, width="stretch", theme="streamlit")

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
        title=titulo_filtro("Quantos cenários caem em cada selo (quartis)", cena_sel, ano_sel),
    )
    fig_cat.update_layout(showlegend=False, xaxis_title="", yaxis_title="Nº de cenários")
    st.plotly_chart(fig_cat, width="stretch", theme="streamlit")

    show = rank_view.sort_values("rentabilidade", ascending=False).head(20).copy()
    show["Cenario"] = show["CENA"].map(nome_amigavel)
    show["rentabilidade"] = show["rentabilidade"].map(fmt_pct)
    show["liquidez"] = show["liquidez"].map(lambda x: f"{x:.2f}x" if pd.notna(x) else "—")
    show["risco"] = show["risco"].map(lambda x: f"{x:.2%}" if pd.notna(x) else "—")
    show["NCG"] = show["NCG"].map(fmt_rs)
    show["Ciclo_Financeiro"] = show["Ciclo_Financeiro"].map(fmt_dias)
    st.dataframe(
        show[
            [
                "Cenario",
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
        width="stretch",
        hide_index=True,
    )

with aba_risco:
    st.markdown("#### Envelope de probabilidade (todos os cenários)")
    st.caption(
        "A faixa sombreada cobre 90% dos casos (percentis 5 e 95). "
        "A mediana é o caminho mais típico. Pontos individuais e a média ficam desligados por padrão."
    )
    rotulo_nuvem = st.selectbox(
        "Métrica da nuvem",
        options=list(METRICAS_NUVEM.keys()),
        index=0,
        key="metrica_nuvem",
    )
    col_nuvem, maior_melhor = METRICAS_NUVEM[rotulo_nuvem]
    ano_nuvem = None if ano_sel == "Todos" else int(ano_sel)
    col_graf, col_camadas = st.columns([4, 1])
    with col_camadas:
        st.markdown("**Camadas**")
        ver_pontos = st.checkbox("Pontos de todos os cenários", value=False, key="camada_pontos")
        ver_media = st.checkbox("Linha da média", value=False, key="camada_media")
    with col_graf:
        st.plotly_chart(
            figura_envelope(
                ind,
                col_nuvem,
                rotulo_nuvem,
                maior_melhor,
                titulo=titulo_filtro(f"Faixa de risco — {rotulo_nuvem}", cena_sel, ano_sel),
                ano_destaque=ano_nuvem,
                cena_destaque=cena_sel,
                mostrar_pontos=ver_pontos,
                mostrar_media=ver_media,
            ),
            width="stretch",
            theme="streamlit",
        )

    env = resumo_envelope(ind, col_nuvem, maior_melhor)
    e1, e2, e3, e4 = st.columns(4)
    e1.metric("Mediana no horizonte", fmt_rs(float(env["mediana"].mean())))
    e2.metric("Média no horizonte", fmt_rs(float(env["media"].mean())))
    e3.metric("Pior caso (extremo)", fmt_rs(float(env["pessimista"].min() if maior_melhor else env["pessimista"].max())))
    e4.metric("Melhor caso (extremo)", fmt_rs(float(env["otimista"].max() if maior_melhor else env["otimista"].min())))

    st.markdown("#### Histograma por ano")
    if ano_sel == "Todos":
        ano_hist = st.selectbox(
            "Ano da distribuição",
            options=anos,
            index=anos.index(9) if 9 in anos else 0,
            key="ano_histograma",
        )
        st.caption("O filtro da barra lateral está em **Todos** — escolha o ano do histograma acima.")
    else:
        ano_hist = int(ano_sel)
        st.caption(f"Usando o ano do filtro lateral: **Ano {ano_hist}**.")

    fatia_ano = ind[ind["ano_num"] == ano_hist]
    st.plotly_chart(
        figura_histograma_ano(
            fatia_ano,
            col_nuvem,
            rotulo_nuvem,
            ano_hist,
            titulo=titulo_filtro(f"Distribuição de {rotulo_nuvem}", cena_sel, ano_hist),
        ),
        width="stretch",
        theme="streamlit",
    )

with aba_comp:
    st.markdown("#### Comparador lado a lado")
    st.caption("Escolha **2 ou 3** cenários para ver a mesma métrica no horizonte e os KPIs na mesma tela.")
    padrao_comp = [c for c in cenas_padrao_comparacao(cenas) if c in cenas]
    escolhidos = st.multiselect(
        "Cenários para comparar",
        options=cenas,
        default=padrao_comp,
        max_selections=3,
        format_func=nome_amigavel,
        key="cenas_comparar",
    )
    if len(escolhidos) < 2:
        st.info("Selecione pelo menos dois cenários (máximo três).")
    else:
        rotulo_comp = st.selectbox(
            "Métrica do gráfico",
            options=list(METRICAS_NUVEM.keys()),
            index=0,
            key="metrica_comparar",
        )
        col_comp, _maior = METRICAS_NUVEM[rotulo_comp]
        trilhas = ind[ind["CENA"].isin(escolhidos)].sort_values(["CENA", "ano_num"]).copy()
        trilhas["Cenario"] = trilhas["CENA"].map(nome_amigavel)
        fig_comp = px.line(
            trilhas,
            x="ano_num",
            y=col_comp,
            color="Cenario",
            markers=True,
            color_discrete_sequence=CORES_COMPARA,
            labels={"ano_num": "Ano", col_comp: rotulo_comp, "Cenario": "Cenário"},
            title=titulo_filtro(f"{rotulo_comp}: comparação no horizonte", cena_sel, ano_sel),
        )
        fig_comp.update_layout(hovermode="x unified", legend_title_text="")
        fig_comp = ancorar_ano_temporal(fig_comp, trilhas, [col_comp], ano_sel)
        fig_comp = anotar_marcos_negocio(fig_comp)
        st.plotly_chart(fig_comp, width="stretch", theme="streamlit")

        cols_kpi = st.columns(len(escolhidos))
        for col_ui, cena in zip(cols_kpi, escolhidos, strict=True):
            recorte = trilhas[trilhas["CENA"] == cena]
            if ano_sel != "Todos":
                recorte = recorte[recorte["ano_num"] == ano_sel]
            m = recorte[
                ["NCG", "Saldo_Tesouraria", "liquidez", "Ciclo_Financeiro", "disponivel", "geracao_caixa"]
            ].mean(numeric_only=True)
            col_ui.markdown(f"**{nome_amigavel(cena)}**")
            col_ui.caption(f"`{cena}`")
            col_ui.metric("Caixa disponível", fmt_rs(m["disponivel"]))
            col_ui.metric("Geração de caixa", fmt_rs(m["geracao_caixa"]))
            col_ui.metric("NCG", fmt_rs(m["NCG"]))
            col_ui.metric("Saldo de tesouraria", fmt_rs(m["Saldo_Tesouraria"]))
            col_ui.metric("Liquidez corrente", f"{m['liquidez']:.2f}x" if pd.notna(m["liquidez"]) else "—")
            col_ui.metric("Ciclo financeiro", fmt_dias(m["Ciclo_Financeiro"]))

        resumo_comp = (
            trilhas.groupby("CENA", as_index=False)
            .agg(
                caixa=("disponivel", "mean"),
                geracao_caixa=("geracao_caixa", "mean"),
                NCG=("NCG", "mean"),
                tesouraria=("Saldo_Tesouraria", "mean"),
                liquidez=("liquidez", "mean"),
                ciclo=("Ciclo_Financeiro", "mean"),
                rentabilidade=("rentabilidade", "mean"),
            )
            .set_index("CENA")
            .reindex(escolhidos)
        )
        resumo_comp.index = [nome_amigavel(c) for c in resumo_comp.index]
        linhas_fmt = {
            "Caixa disponível": resumo_comp["caixa"].map(fmt_rs),
            "Geração de caixa": resumo_comp["geracao_caixa"].map(fmt_rs),
            "NCG": resumo_comp["NCG"].map(fmt_rs),
            "Saldo de tesouraria": resumo_comp["tesouraria"].map(fmt_rs),
            "Liquidez corrente": resumo_comp["liquidez"].map(
                lambda x: f"{x:.2f}x" if pd.notna(x) else "—"
            ),
            "Ciclo financeiro": resumo_comp["ciclo"].map(fmt_dias),
            "Rentabilidade": resumo_comp["rentabilidade"].map(fmt_pct),
        }
        st.dataframe(pd.DataFrame(linhas_fmt).T, width="stretch")

with aba4:
    st.markdown(
        f"""
### O que este painel responde

1. **A operação come ou gera caixa?** → olhe a **NCG**.  
2. **Dependemos de banco no curto prazo?** → olhe o **Saldo de Tesouraria**.  
3. **Por quantos dias financiamos a operação?** → olhe o **Ciclo Financeiro**.  
4. **Entre os {ranking.shape[0]:,} cenários, quais são mais rentáveis / líquidos / arriscados?** → aba Ranking.  
5. **Qual a faixa de caixa no horizonte?** → aba Faixa de risco (nuvem + mediana + pior/melhor caso).  
6. **Como o caixa se espalha num ano (ex.: Ano 9)?** → histograma da mesma aba, com o filtro de ano.  
7. **Como dois ou três cenários se comparam?** → aba Comparar cenários.

Os títulos usam **Cenário 6** (não `Total Cen_00006`). Na Faixa de risco, as caixas **Pontos de todos os cenários** e **Linha da média** ligam camadas extras. As faixas dos Anos 8–11 e do Ano 12 no gráfico marcam ciclo pleno e encerramento de contrato.

### Fórmulas (iguais às do notebook)

Saldos de passivo no `Cti.csv` vêm com sinal de crédito (−). Sem o valor absoluto, `NCG = ACO − PCO` vira `ACO + |PCO|` e a liquidez fica negativa.

| Indicador | Fórmula |
|---|---|
| NCG | ACO − abs(PCO) |
| Saldo de Tesouraria | Disponível − Empréstimos CP |
| PMR | (Contas a Receber / Receita) × 365 |
| PME | (Estoques / abs(Custos)) × 365 |
| PMP | (Fornecedores / abs(Custos)) × 365 |
| Ciclo Financeiro | PMR + PME − PMP |

Cenário atual em destaque: **{nome_amigavel(cena_sel)}** · Rentabilidade {fmt_pct(k["rentabilidade"])} · Risco {fmt_pct(k["risco"]) if pd.notna(k["risco"]) else "—"}.
"""
    )

st.markdown("---")
st.caption("CTI · Dashboard de planejamento financeiro · dados: Cti.csv")
