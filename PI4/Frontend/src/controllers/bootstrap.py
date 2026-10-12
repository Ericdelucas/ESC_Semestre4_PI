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

from Backend.diag import diag  # noqa: E402
from Backend.services import build_context_metrics, prepare_dashboard_data  # noqa: E402
from Backend.services.dashboard_pipeline import CACHE_DIR, cache_disponivel, cache_paths  # noqa: E402
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


def fonte_sql_ativa() -> bool:
    if "cti_fonte_sql" in st.session_state:
        return bool(st.session_state["cti_fonte_sql"])
    try:
        from Backend.data_loader.db import sql_conectado

        return sql_conectado()
    except Exception:  # noqa: BLE001
        return False


@st.cache_data(show_spinner=False)
def carregar_pipeline() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Cacheia o resultado. PostgreSQL primeiro; parquet/CSV so sem DATABASE_URL."""
    df, ind, ranking = prepare_dashboard_data(CSV_PATH)
    ranking = ranking.copy()
    if "CENA" in ranking.columns:
        ranking["rotulo"] = ranking["CENA"].map(cena_rotulo)
    return df, ind, ranking


@st.cache_data(show_spinner=False, ttl=180)
def carregar_recorte(cena_sel: str, ano_sel: str | int) -> pd.DataFrame:
    """Fatia filtrada no PostgreSQL — nao carrega o milhao de linhas."""
    from Backend.data_loader.sql_reader import fetch_recorte

    return fetch_recorte(cena_sel, ano_sel)


def carregar_estado() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame] | None:
    """PostgreSQL via DATABASE_URL; se o DNS falhar, usa cache sem derrubar a UI."""
    from Backend.data_loader.db import postgres_disponivel, sql_aviso, sql_conectado

    usa_sql = postgres_disponivel()
    diag("boot", f"cwd={Path.cwd()} postgres={usa_sql}")
    raw_path, ind_path, rank_path = cache_paths()
    diag("boot", f"CACHE_DIR={CACHE_DIR.resolve()} disponivel={cache_disponivel()}")
    for path in (raw_path, ind_path, rank_path, CSV_PATH):
        existe = path.exists()
        tamanho = path.stat().st_size if existe else 0
        diag("boot", f"{path.resolve()} existe={existe} bytes={tamanho}")
    spinner = (
        "A consultar cti_dados no PostgreSQL..."
        if usa_sql
        else "A carregar base (cache ou CSV)..."
    )
    try:
        with st.spinner(spinner):
            diag("boot", f"spinner={spinner!r} a chamar carregar_pipeline")
            dados = carregar_pipeline()
            diag(
                "boot",
                f"pipeline OK df={len(dados[0]):,} ind={len(dados[1]):,} ranking={len(dados[2]):,} sql={sql_conectado()}",
            )
        if sql_conectado():
            from Backend.data_loader.sql_reader import contar_linhas, fonte_label

            st.session_state["cti_fonte_sql"] = True
            st.session_state.setdefault("cti_active_dataset_name", fonte_label())
            try:
                st.session_state.setdefault("cti_row_count", contar_linhas())
            except Exception as exc:  # noqa: BLE001
                diag("boot", f"aviso COUNT(*) {type(exc).__name__}: {exc}")
        else:
            st.session_state["cti_fonte_sql"] = False
            if usa_sql:
                diag("boot", f"aviso: fallback cache ({sql_aviso()})")
                st.warning(t("boot.sql_fallback"))
            if dados and not dados[0].empty:
                st.session_state.setdefault("cti_row_count", len(dados[0]))
        diag(
            "boot",
            f"estado final df={len(dados[0]):,} ind={len(dados[1]):,} ranking={len(dados[2]):,} "
            f"sql={sql_conectado()} df_cols={list(dados[0].columns)[:8]}",
        )
        return dados
    except MemoryError:
        diag("boot", "MemoryError no carregamento")
        st.error(t("boot.memory"))
        return None
    except Exception as exc:  # noqa: BLE001
        diag("boot", f"aviso {type(exc).__name__}: {exc} — a tentar cache")
        try:
            if cache_disponivel():
                from Backend.services.dashboard_pipeline import load_cached_dashboard

                dados = load_cached_dashboard()
                st.session_state["cti_fonte_sql"] = False
                st.warning(t("boot.sql_fallback"))
                return dados
        except Exception as cache_exc:  # noqa: BLE001
            diag("boot", f"cache tambem falhou {type(cache_exc).__name__}: {cache_exc}")
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
