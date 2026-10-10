"""Estado global e cabecalho do app Streamlit."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

import pandas as pd
import streamlit as st


PI4_ROOT = Path(__file__).resolve().parents[3]
if str(PI4_ROOT) not in sys.path:
    sys.path.insert(0, str(PI4_ROOT))

from Backend.services import build_context_metrics, prepare_dashboard_data  # noqa: E402
from src.config import CSV_PATH  # noqa: E402
from src.config.i18n import t  # noqa: E402
from src.controllers.modals import open_relatorio  # noqa: E402
from src.controllers.headers import banner_auditoria_filtro  # noqa: E402
from src.controllers.ops_menu import garantir_varredura_silenciosa, render_ops_menu  # noqa: E402
from src.controllers.kpis import kpis_por_persona, render_kpi_row  # noqa: E402
from src.controllers.resilience import safe_render  # noqa: E402
from src.models.formatting import cena_rotulo, is_all_scenarios, texto_ciclo, texto_ncg, texto_tesouraria  # noqa: E402


@dataclass
class AppContext:
    """Estado derivado usado pelas views do Streamlit."""

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
    """Carrega base e indicadores processados pelo backend."""
    _ = mtime
    df, ind, ranking = prepare_dashboard_data(csv_path)
    ranking = ranking.copy()
    ranking["rotulo"] = ranking["CENA"].map(cena_rotulo)
    return df, ind, ranking


def carregar_estado() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame] | None:
    """Carrega o estado base do dashboard ou exibe erro amigavel."""
    if not CSV_PATH.exists():
        st.error(t("boot.missing_file", path=CSV_PATH))
        return None
    try:
        return carregar_pipeline(str(CSV_PATH), CSV_PATH.stat().st_mtime)
    except MemoryError:
        st.error(t("boot.memory"))
        return None
    except Exception as exc:  # noqa: BLE001 - evita queda abrupta do processo no deploy
        st.error(t("boot.prep_error", err=f"{type(exc).__name__}: {exc}"))
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
    """Monta contexto visual usando metricas calculadas pelo backend."""
    ranking = ranking.copy() if isinstance(ranking, pd.DataFrame) else pd.DataFrame()
    if "CENA" not in ranking.columns:
        ranking["CENA"] = pd.Series(dtype="object")
    ranking["rotulo"] = ranking["CENA"].map(cena_rotulo)
    mapa_rotulo = dict(zip(ranking["rotulo"], ranking["CENA"], strict=False))
    n_cenarios = int(ranking["CENA"].nunique()) if not ranking.empty else 0
    ano_enc, p_ruina, foco, foco_ano, k = build_context_metrics(
        ind,
        ranking,
        cena_sel=cena_sel,
        ano_sel=ano_sel,
    )
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
    """Renderiza titulo, banner e KPIs ja processados."""
    with st.container(key="cti_header_bar"):
        title_col, report_col, menu_col = st.columns([0.74, 0.18, 0.08], vertical_alignment="center")
        with title_col:
            st.subheader(t("header.focus", cena=cena_rotulo(ctx.cena_sel)))
        with report_col:
            if ctx.persona != "teste" and st.button(t("header.report"), key="header_create_report", use_container_width=True):
                open_relatorio()
                st.rerun()
        with menu_col:
            if ctx.persona != "teste":
                render_ops_menu()
    if ctx.persona == "teste":
        return
    garantir_varredura_silenciosa()
    safe_render("banner de auditoria", banner_auditoria_filtro, ctx.cena_sel, ctx.ano_sel)
    if is_all_scenarios(ctx.cena_sel):
        st.write(t("header.avg_scenes"))
    st.write(t("header.avg_all") if ctx.ano_sel == "Todos" else t("header.avg_year", ano=ctx.ano_sel))
    render_kpi_row(kpis_por_persona(ctx.persona, ctx.k, ctx.ranking, ctx.df, ctx.cena_sel, ctx.ano_sel))
    st.info(t(f"persona.blurb.{ctx.persona}"))
    if ctx.persona == "cfo":
        st.caption(texto_ncg(ctx.k["NCG"]) if "NCG" in ctx.k.index else "")
        col_tes, col_ciclo = st.columns(2)
        col_tes.success(texto_tesouraria(ctx.k["Saldo_Tesouraria"]) if "Saldo_Tesouraria" in ctx.k.index else "-")
        col_ciclo.warning(texto_ciclo(ctx.k["Ciclo_Financeiro"]) if "Ciclo_Financeiro" in ctx.k.index else "-")
