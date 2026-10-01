"""Estado global e cabeçalho do app (fora do orquestrador)."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

import pandas as pd
import streamlit as st

from src.controllers.headers import banner_auditoria_filtro
from src.controllers.kpis import kpis_por_persona, render_kpi_row
from src.config import CACHE_DIR, CSV_PATH
from src.config.i18n import t
from src.models.analytics import montar_indicadores, probabilidade_caixa_negativo
from src.models.analytics.indicators import _compactar_indicadores
from src.models.formatting import cena_rotulo, texto_ciclo, texto_ncg, texto_tesouraria
from src.models.loaders import load_cti_csv, otimizar_base_cti


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


@st.cache_resource(show_spinner="Preparando base e indicadores...", max_entries=1)
def carregar_pipeline(csv_path: str, mtime: float) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Cache em memoria por caminho+mtime, sem hashear DataFrame."""
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
        and raw_path.stat().st_mtime >= csv.stat().st_mtime
    ):
        df = otimizar_base_cti(pd.read_parquet(raw_path))
        ind = _compactar_indicadores(pd.read_parquet(ind_path))
        ranking = _compactar_indicadores(pd.read_parquet(rank_path)).copy()
        if "selo" in ranking.columns:
            ranking["selo"] = ranking["selo"].astype("category")
        ranking["rotulo"] = ranking["CENA"].map(cena_rotulo)
        return df, ind, ranking

    if os.environ.get("RENDER"):
        raise RuntimeError(
            "Cache parquet nao encontrado no runtime. "
            "Confirme se o Build Command executa `python scripts/precompute_cache.py` antes do start."
        )

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
    try:
        return carregar_pipeline(str(CSV_PATH), mtime)
    except MemoryError:
        st.error(
            "A base excedeu a memoria disponivel durante a preparacao. "
            "Tente reduzir o arquivo de entrada ou usar os caches parquet ja gerados."
        )
        return None
    except Exception as exc:  # noqa: BLE001 - evita queda abrupta do processo no deploy
        st.error(f"Nao foi possivel preparar a base de dados: {type(exc).__name__}: {exc}")
        return None


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
        "ebitda",
        "dre_receita",
        "dre_custos",
        "investimentos",
        "total_ativo",
        "total_passivo",
    ]
    base_kpi = foco_ano if not foco_ano.empty else foco
    presentes = [c for c in kpi_cols if c in base_kpi.columns]
    k = base_kpi[presentes].mean(numeric_only=True) if presentes else pd.Series(dtype=float)
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
    st.subheader(t("header.focus", cena=cena_rotulo(ctx.cena_sel)))
    if ctx.persona == "teste":
        return
    safe_render("banner de auditoria", banner_auditoria_filtro, ctx.cena_sel, ctx.ano_sel)
    st.write(
        t("header.avg_all")
        if ctx.ano_sel == "Todos"
        else t("header.avg_year", ano=ctx.ano_sel)
    )
    render_kpi_row(kpis_por_persona(ctx.persona, ctx.k, ctx.ranking, ctx.df, ctx.cena_sel, ctx.ano_sel))
    st.info(t(f"persona.blurb.{ctx.persona}"))
    if ctx.persona == "cfo":
        st.caption(texto_ncg(ctx.k["NCG"]) if "NCG" in ctx.k.index else "")
        a, b = st.columns(2)
        a.success(texto_tesouraria(ctx.k["Saldo_Tesouraria"]) if "Saldo_Tesouraria" in ctx.k.index else "—")
        b.warning(texto_ciclo(ctx.k["Ciclo_Financeiro"]) if "Ciclo_Financeiro" in ctx.k.index else "—")

