"""Estado global e cabeçalho do app (fora do orquestrador)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd
import streamlit as st

from src.components.headers import banner_auditoria_filtro, render_titulo
from src.components.kpis import kpis_por_persona, render_kpi_row
from src.components.resilience import safe_render
from src.config import CACHE_DIR, CSV_PATH
from src.config.i18n import t
from src.data.analytics import montar_indicadores, probabilidade_caixa_negativo
from src.data.formatting import cena_rotulo, texto_ciclo, texto_ncg, texto_tesouraria
from src.data.loaders import load_cti_csv


@dataclass
class AppContext:
    df: pd.DataFrame
    ind: pd.DataFrame
    ranking: pd.DataFrame
    mapa_rotulo: dict[str, str]
    n_cenarios: int
    ano_enc: int
    p_ruina: float
    ano_sel: str | int
    cena_sel: str
    anos: list[int]
    cenas: list[str]
    persona: str
    foco: pd.DataFrame
    foco_ano: pd.DataFrame
    k: pd.Series


@st.cache_resource(show_spinner="Preparando base e indicadores…")
def carregar_pipeline(csv_path: str, mtime: float) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Cache em memória por caminho+mtime — sem hashear DataFrame."""
    _ = mtime  # entra na chave do cache
    CACHE_DIR.mkdir(exist_ok=True)
    ind_path = CACHE_DIR / "indicadores.parquet"
    rank_path = CACHE_DIR / "ranking.parquet"
    raw_path = CACHE_DIR / "cti_limpo.parquet"

    # Atalho: se indicadores já existem e estão frescos em relação ao CSV
    csv = Path(csv_path)
    if (
        ind_path.exists()
        and rank_path.exists()
        and raw_path.exists()
        and ind_path.stat().st_mtime >= csv.stat().st_mtime
        and rank_path.stat().st_mtime >= csv.stat().st_mtime
    ):
        df = pd.read_parquet(raw_path)
        ind = pd.read_parquet(ind_path)
        ranking = pd.read_parquet(rank_path).copy()
        ranking["rotulo"] = ranking["CENA"].map(cena_rotulo)
        return df, ind, ranking

    df = load_cti_csv(csv)
    ind, ranking = montar_indicadores(df)
    ranking = ranking.copy()
    ranking["rotulo"] = ranking["CENA"].map(cena_rotulo)
    ind.to_parquet(ind_path, index=False)
    ranking.to_parquet(rank_path, index=False)
    return df, ind, ranking


def carregar_estado() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame] | None:
    if not CSV_PATH.exists():
        st.error(f"Arquivo não encontrado: {CSV_PATH}")
        return None
    mtime = CSV_PATH.stat().st_mtime
    return safe_render("pipeline de dados", carregar_pipeline, str(CSV_PATH), mtime)


def montar_contexto(
    df: pd.DataFrame,
    ind: pd.DataFrame,
    ranking: pd.DataFrame,
    *,
    ano_sel: str | int,
    cena_sel: str,
    anos: list[int],
    cenas: list[str],
    persona: str,
) -> AppContext:
    ranking = ranking.copy()
    ranking["rotulo"] = ranking["CENA"].map(cena_rotulo)
    mapa_rotulo = dict(zip(ranking["rotulo"], ranking["CENA"], strict=False))
    n_cenarios = int(ranking["CENA"].nunique())
    ano_enc = int(ranking["ano_encerramento"].iloc[0]) if len(ranking) else 12
    p_ruina = probabilidade_caixa_negativo(ranking)
    foco = ind.loc[ind["CENA"] == cena_sel].sort_values("ano_num")
    if ano_sel == "Todos":
        foco_ano = foco
    else:
        ano_num = int(ano_sel)
        foco_ano = foco.loc[pd.to_numeric(foco["ano_num"], errors="coerce") == ano_num]
    kpi_cols = [
        "NCG",
        "Saldo_Tesouraria",
        "Ciclo_Financeiro",
        "PMR",
        "PME",
        "PMP",
        "liquidez",
        "rentabilidade",
        "risco",
        "resultado",
    ]
    base_kpi = foco_ano if not foco_ano.empty else foco
    k = base_kpi[kpi_cols].mean(numeric_only=True)
    return AppContext(
        df=df,
        ind=ind,
        ranking=ranking,
        mapa_rotulo=mapa_rotulo,
        n_cenarios=n_cenarios,
        ano_enc=ano_enc,
        p_ruina=p_ruina,
        ano_sel=ano_sel,
        cena_sel=cena_sel,
        anos=anos,
        cenas=cenas,
        persona=persona,
        foco=foco,
        foco_ano=foco_ano,
        k=k,
    )


def render_cabecalho(ctx: AppContext) -> None:
    """Título, banner, KPIs e textos por persona (auditoria fica no orquestrador)."""
    render_titulo()
    st.subheader(t("header.focus", cena=cena_rotulo(ctx.cena_sel)))
    safe_render("banner de auditoria", banner_auditoria_filtro, ctx.cena_sel, ctx.ano_sel)
    st.write(
        t("header.avg_all")
        if ctx.ano_sel == "Todos"
        else t("header.avg_year", ano=ctx.ano_sel)
    )
    render_kpi_row(kpis_por_persona(ctx.persona, ctx.k, ctx.ranking))
    if ctx.persona == "geral":
        st.info(texto_ncg(ctx.k["NCG"]))
        a, b = st.columns(2)
        a.success(texto_tesouraria(ctx.k["Saldo_Tesouraria"]))
        b.warning(texto_ciclo(ctx.k["Ciclo_Financeiro"]))
    elif ctx.persona == "cfo":
        st.info(t("persona.blurb.cfo"))
    elif ctx.persona == "acionistas":
        st.info(t("persona.blurb.acionistas"))
    else:
        st.info(t("persona.blurb.concedente"))
