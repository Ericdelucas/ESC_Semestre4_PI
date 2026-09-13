"""Aba Mapeamento de Risco × Retorno."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.components.kpis import card_selo_html
from src.components.resilience import safe_render
from src.config import COR_ANCORA, CORES_SELO, SELOS_NEGOCIO
from src.data.analytics import cena_rotulo, cenas_por_percentil, melhor_entre
from src.data.formatting import fmt_dias, fmt_pct, fmt_rs


def _scatter(
    rank_view: pd.DataFrame,
    ranking: pd.DataFrame,
    cena_destaque: str | None,
) -> None:
    fig = px.scatter(
        rank_view,
        x="risco",
        y="rentabilidade",
        size="liquidez_plot",
        color="selo",
        hover_name="rotulo",
        hover_data={
            "liquidez": ":.2f",
            "liquidez_plot": False,
            "Ciclo_Financeiro": ":.1f",
            "selo": True,
            "risco": ":.3f",
            "rentabilidade": ":.3f",
        },
        color_discrete_map=CORES_SELO,
        size_max=26,
        category_orders={"selo": SELOS_NEGOCIO},
        labels={
            "risco": "Risco (Passivo / Ativo)",
            "rentabilidade": "Rentabilidade (Resultado / Receita)",
            "liquidez_plot": "Liquidez (≥0)",
            "selo": "Selo",
        },
        title=f"Matriz Risco × Retorno · {len(rank_view):,} cenários visíveis",
    )
    if cena_destaque is not None:
        ponto = ranking.loc[ranking["CENA"] == cena_destaque]
        if not ponto.empty:
            fig.add_trace(
                go.Scatter(
                    x=ponto["risco"],
                    y=ponto["rentabilidade"],
                    mode="markers",
                    marker={
                        "size": 18,
                        "color": COR_ANCORA,
                        "symbol": "diamond",
                        "line": {"width": 2, "color": "#111"},
                    },
                    name=f"Destaque · {cena_rotulo(cena_destaque)}",
                    hovertemplate="%{text}<extra></extra>",
                    text=ponto["rotulo"],
                )
            )
    fig.update_layout(legend_title_text="Selo de negócio", hovermode="closest")
    st.plotly_chart(fig, width="stretch", theme="streamlit")


def render(
    ranking: pd.DataFrame,
    persona: str,
    cenas: list[str],
    mapa_rotulo: dict[str, str],
    n_cenarios: int,
) -> None:
    st.markdown("### Matriz Risco × Retorno")
    st.caption(
        f"Distribuição consolidada dos {n_cenarios:,} cenários simulados para avaliação "
        "de rentabilidade, liquidez e endividamento."
    )

    if "selo_filtro" not in st.session_state:
        st.session_state["selo_filtro"] = None

    contagem_selo = ranking["selo"].value_counts().reindex(SELOS_NEGOCIO, fill_value=0)
    cols_selo = st.columns(3)
    for i, nome_selo in enumerate(SELOS_NEGOCIO):
        with cols_selo[i % 3]:
            ativo = st.session_state["selo_filtro"] == nome_selo
            st.markdown(
                card_selo_html(nome_selo, int(contagem_selo.get(nome_selo, 0)), ativo),
                unsafe_allow_html=True,
            )
            if st.button(
                "Filtrar" if not ativo else "Remover filtro",
                key=f"btn_selo_{i}",
                width="stretch",
            ):
                st.session_state["selo_filtro"] = None if ativo else nome_selo
                st.rerun()

    if st.session_state["selo_filtro"] is not None:
        st.caption(f"Filtro ativo: **{st.session_state['selo_filtro']}**")

    destaque_persona = {
        "CFO & Credores": "Ênfase em risco e liquidez (solvência).",
        "Acionistas": "Ênfase em rentabilidade (eixo Y).",
        "Poder Concedente": "Ênfase em selos de pressão de investimento e caixa de encerramento.",
        "Visão Geral": "Visão equilibrada risco × retorno.",
    }
    st.caption(destaque_persona.get(persona, ""))

    rank_view = ranking.copy()
    if st.session_state["selo_filtro"] is not None:
        rank_view = rank_view.loc[rank_view["selo"] == st.session_state["selo_filtro"]]

    opcoes_busca = ["(nenhum)"] + sorted(ranking["rotulo"].tolist())
    busca = st.selectbox("Buscar e destacar cenário", options=opcoes_busca, index=0, key="busca_cena_matriz")
    cena_destaque = mapa_rotulo.get(busca) if busca != "(nenhum)" else None

    rank_view = rank_view.copy()
    rank_view["liquidez_plot"] = rank_view["liquidez"].clip(lower=0).fillna(0)
    safe_render("gráfico de dispersão risco × retorno", _scatter, rank_view, ranking, cena_destaque)

    with st.expander("Comparador side-by-side (Cenário A vs Cenário B)", expanded=False):
        try:
            perc = cenas_por_percentil(ranking, "caixa_ano12", [0.05, 0.50])
            padrao_a = perc.get(0.05, cenas[0] if cenas else None)
            padrao_b = perc.get(0.50, cenas[1] if len(cenas) > 1 else padrao_a)
            rotulos_ord = sorted(ranking["rotulo"].tolist())
            rotulo_a_default = cena_rotulo(padrao_a) if padrao_a else rotulos_ord[0]
            rotulo_b_default = cena_rotulo(padrao_b) if padrao_b else rotulos_ord[min(1, len(rotulos_ord) - 1)]
            c_a, c_b = st.columns(2)
            with c_a:
                sel_a = st.selectbox(
                    "Cenário A (ex.: pior caso P5 de caixa)",
                    options=rotulos_ord,
                    index=rotulos_ord.index(rotulo_a_default) if rotulo_a_default in rotulos_ord else 0,
                    key="comp_a",
                )
            with c_b:
                sel_b = st.selectbox(
                    "Cenário B (ex.: base P50 de caixa)",
                    options=rotulos_ord,
                    index=rotulos_ord.index(rotulo_b_default) if rotulo_b_default in rotulos_ord else 0,
                    key="comp_b",
                )
            ra = ranking.loc[ranking["CENA"] == mapa_rotulo[sel_a]].iloc[0]
            rb = ranking.loc[ranking["CENA"] == mapa_rotulo[sel_b]].iloc[0]
            metricas_cmp = [
                ("Rentabilidade (%)", "rentabilidade", True, fmt_pct),
                ("Risco (Passivo/Ativo)", "risco", False, fmt_pct),
                ("Liquidez acumulada", "liquidez_acumulada", True, fmt_rs),
                ("Ciclo Financeiro (dias)", "Ciclo_Financeiro", False, fmt_dias),
            ]
            linhas = []
            for nome, col, maior_melhor, fmt in metricas_cmp:
                va, vb = float(ra[col]), float(rb[col])
                vencedor = melhor_entre(va, vb, maior_melhor=maior_melhor)
                linhas.append(
                    {
                        "Métrica": nome,
                        "Cenário A": fmt(va) + (" ✓" if vencedor == "A" else ""),
                        "Cenário B": fmt(vb) + (" ✓" if vencedor == "B" else ""),
                    }
                )
            st.caption(f"**A:** {sel_a} · **B:** {sel_b} · ✓ = mais seguro/rentável na métrica")
            st.dataframe(pd.DataFrame(linhas), width="stretch", hide_index=True)
        except Exception as exc:  # noqa: BLE001
            st.error("Não foi possível carregar o comparador side-by-side no momento.")
            st.caption(f"{type(exc).__name__}: {exc}")
