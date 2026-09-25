"""Aba Mapeamento de Risco × Retorno."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.controllers.headers import heading_with_help
from src.controllers.kpis import card_selo_html
from src.controllers.resilience import resilient_view, safe_render
from src.config import COR_ANCORA, CORES_SELO, SELOS_NEGOCIO
from src.config.glossary import help_text
from src.config.i18n import get_lang, t, translate_selo
from src.models.analytics import cenas_por_percentil
from src.models.formatting import cena_rotulo, cena_sort_key, fmt_dias, fmt_pct, fmt_rs, melhor_entre


def _scatter(
    rank_view: pd.DataFrame,
    ranking: pd.DataFrame,
    cena_destaque: str | None,
) -> None:
    view = rank_view.copy()
    view["selo_i18n"] = view["selo"].map(translate_selo)
    cores_i18n = {translate_selo(k): v for k, v in CORES_SELO.items()}
    ordem = [translate_selo(s) for s in SELOS_NEGOCIO]
    fig = px.scatter(
        view,
        x="risco",
        y="rentabilidade",
        size="liquidez_plot",
        color="selo_i18n",
        hover_name="rotulo",
        hover_data={
            "liquidez": ":.2f",
            "liquidez_plot": False,
            "Ciclo_Financeiro": ":.1f",
            "selo_i18n": True,
            "risco": ":.3f",
            "rentabilidade": ":.3f",
        },
        color_discrete_map=cores_i18n,
        size_max=26,
        category_orders={"selo_i18n": ordem},
        labels={
            "risco": t("map.x"),
            "rentabilidade": t("map.y"),
            "liquidez_plot": t("map.size"),
            "liquidez": t("kpi.liquidity"),
            "Ciclo_Financeiro": t("kpi.cycle"),
            "selo_i18n": t("map.selo"),
        },
        title=t("map.chart_title", n=f"{len(rank_view):,}"),
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
                        "symbol": "star",
                        "line": {"width": 1.5, "color": "#111"},
                    },
                    name=f"★ {cena_rotulo(cena_destaque)}",
                    hovertemplate="%{x:.3f}, %{y:.3f}<extra></extra>",
                )
            )
    st.plotly_chart(fig, width="stretch", theme="streamlit")


@resilient_view("aba Mapeamento de Risco × Retorno")
def render(
    ranking: pd.DataFrame,
    persona: str,
    cenas: list[str],
    mapa_rotulo: dict[str, str],
    n_cenarios: int,
) -> None:
    heading_with_help(t("map.title"), "risk_return")
    st.caption(t("map.caption", n=f"{n_cenarios:,}"))

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
                t("map.clear") if ativo else t("map.filter"),
                key=f"btn_selo_{i}",
                width="stretch",
            ):
                st.session_state["selo_filtro"] = None if ativo else nome_selo
                st.rerun()

    if st.session_state["selo_filtro"] is not None:
        st.caption(t("map.active", selo=translate_selo(st.session_state["selo_filtro"])))

    st.caption(t(f"map.focus.{persona}"))

    rank_view = ranking.copy()
    if st.session_state["selo_filtro"] is not None:
        rank_view = rank_view.loc[rank_view["selo"] == st.session_state["selo_filtro"]]

    nenhum = t("map.none")
    opcoes_busca = [nenhum] + [
        cena_rotulo(c) for c in sorted(ranking["CENA"].tolist(), key=cena_sort_key)
    ]
    busca = st.selectbox(
        t("map.search"),
        options=opcoes_busca,
        index=0,
        key=f"busca_cena_matriz_{get_lang()}",
        help=help_text("map_search"),
    )
    cena_destaque = mapa_rotulo.get(busca) if busca != nenhum else None

    rank_view = rank_view.copy()
    rank_view["liquidez_plot"] = rank_view["liquidez"].clip(lower=0).fillna(0)
    safe_render("gráfico de dispersão risco × retorno", _scatter, rank_view, ranking, cena_destaque)

    with st.expander(t("map.comp_exp"), expanded=False):
        try:
            perc = cenas_por_percentil(ranking, "caixa_ano12", [0.05, 0.50])
            padrao_a = perc.get(0.05, cenas[0] if cenas else None)
            padrao_b = perc.get(0.50, cenas[1] if len(cenas) > 1 else padrao_a)
            rotulos_ord = [cena_rotulo(c) for c in sorted(ranking["CENA"].tolist(), key=cena_sort_key)]
            rotulo_a_default = cena_rotulo(padrao_a) if padrao_a else rotulos_ord[0]
            rotulo_b_default = cena_rotulo(padrao_b) if padrao_b else rotulos_ord[min(1, len(rotulos_ord) - 1)]
            c_a, c_b = st.columns(2)
            with c_a:
                sel_a = st.selectbox(
                    t("map.comp_a"),
                    options=rotulos_ord,
                    index=rotulos_ord.index(rotulo_a_default) if rotulo_a_default in rotulos_ord else 0,
                    key=f"comp_a_{get_lang()}",
                    help=help_text("map_comp"),
                )
            with c_b:
                sel_b = st.selectbox(
                    t("map.comp_b"),
                    options=rotulos_ord,
                    index=rotulos_ord.index(rotulo_b_default) if rotulo_b_default in rotulos_ord else 0,
                    key=f"comp_b_{get_lang()}",
                    help=help_text("map_comp"),
                )
            ra = ranking.loc[ranking["CENA"] == mapa_rotulo[sel_a]].iloc[0]
            rb = ranking.loc[ranking["CENA"] == mapa_rotulo[sel_b]].iloc[0]
            metricas_cmp = [
                (t("map.m.profit"), "rentabilidade", True, fmt_pct),
                (t("map.m.risk"), "risco", False, fmt_pct),
                (t("map.m.liq"), "liquidez_acumulada", True, fmt_rs),
                (t("map.m.cycle"), "Ciclo_Financeiro", False, fmt_dias),
            ]
            linhas = []
            for nome, col, maior_melhor, fmt in metricas_cmp:
                va, vb = float(ra[col]), float(rb[col])
                vencedor = melhor_entre(va, vb, maior_melhor=maior_melhor)
                linhas.append(
                    {
                        t("map.metric"): nome,
                        t("map.scene_a"): fmt(va) + (" ✓" if vencedor == "A" else ""),
                        t("map.scene_b"): fmt(vb) + (" ✓" if vencedor == "B" else ""),
                    }
                )
            st.caption(t("map.comp_cap", a=sel_a, b=sel_b))
            st.dataframe(pd.DataFrame(linhas), width="stretch", hide_index=True)
        except Exception as exc:  # noqa: BLE001
            st.error(str(exc))
