"""Modal do construtor modular de relatorios executivos."""

from __future__ import annotations

import os
import time
import traceback
from datetime import datetime

import pandas as pd
import streamlit as st

from src.config.i18n import t
from src.controllers.modals import close_relatorio, dialog_kwargs
from src.models.formatting import cena_rotulo


DEFAULT_BLOCKS_BY_PROFILE: dict[str, list[str]] = {
    "CEO": ["cover", "financial_dre", "break_even", "commercial", "scenario_comparison"],
    "CFO": ["cover", "financial_dre", "break_even", "commercial"],
    "CTO": ["cover", "operational_tech", "break_even", "scenario_comparison"],
}

PENDING_KEY = "_cti_report_pending"


def _available_scenarios(cenas: list[str] | None, current: str) -> list[str]:
    items = [str(item) for item in (cenas or []) if str(item).strip()]
    if current and str(current) not in items:
        items = [str(current), *items]
    return items or [str(current)]


def _load_report_backend():
    from Backend.services.custom_report_service import (  # noqa: PLC0415
        block_options,
        default_block_notes,
        generate_custom_report_pdf,
    )

    return block_options, default_block_notes, generate_custom_report_pdf


def _ensure_report_defaults(profile: str, blocks: dict[str, str], suggested_notes: dict[str, str]) -> None:
    """Inicializa chaves estaveis sem apagar edicoes ja feitas pelo usuario."""
    valid_blocks = set(blocks)
    current_blocks = st.session_state.get("report_selected_blocks")
    if not current_blocks or any(block not in valid_blocks for block in current_blocks):
        st.session_state["report_selected_blocks"] = [
            block for block in DEFAULT_BLOCKS_BY_PROFILE.get(profile, DEFAULT_BLOCKS_BY_PROFILE["CEO"]) if block in valid_blocks
        ]

    st.session_state.setdefault("report_scenarios", [])
    for block_id, note in suggested_notes.items():
        st.session_state.setdefault(f"text_parecer_{block_id}", note)


def _build_notes(selected_blocks: list[str]) -> dict[str, str]:
    return {block_id: st.session_state.get(f"text_parecer_{block_id}", "") for block_id in selected_blocks}


def _log(msg: str) -> None:
    from Backend.diag import log_relatorio

    log_relatorio(msg)


def _df_relatorio() -> pd.DataFrame:
    from src.controllers.bootstrap import carregar_pipeline
    from src.controllers.data_input import DF_OVERRIDE_KEY, has_custom_data

    if has_custom_data():
        override = st.session_state.get(DF_OVERRIDE_KEY)
        if isinstance(override, pd.DataFrame) and not override.empty:
            return override
    df, _, _ = carregar_pipeline()
    return df


def _frames_relatorio(df: pd.DataFrame, scenario: str) -> dict[str, pd.DataFrame]:
    from src.views.persona_tabs.common import _break_even_df, _dre, _ltv_df

    t0 = time.time()
    frames = {
        "dre": _dre(df, scenario),
        "be": _break_even_df(df, scenario),
        "ltv": _ltv_df(df, scenario),
    }
    _log(
        f"frames cacheados cenario={scenario} dre={len(frames['dre'])} be={len(frames['be'])} "
        f"ltv={len(frames['ltv'])} em {time.time() - t0:.2f}s"
    )
    return frames


def _gerar_pdf(payload: dict) -> bytes:
    from Backend.services.custom_report_service import generate_custom_report_pdf
    from src.models.formatting import is_all_scenarios

    scenario = payload["scenario"]
    t0 = time.time()
    _log(f"inicio geracao PDF cenario={scenario} blocos={payload['selected_blocks']} RENDER={bool(os.environ.get('RENDER'))}")
    df = _df_relatorio()
    _log(f"df fonte linhas={len(df)} cols={list(df.columns)[:8]}")
    comparacoes = list(payload.get("comparison_scenarios") or [])
    extra_frames: dict[str, dict[str, pd.DataFrame]] = {}
    if comparacoes:
        from src.views.persona_tabs.common import _break_even_df, _dre

        for extra in comparacoes[:3]:
            extra_frames[str(extra)] = {"dre": _dre(df, extra), "be": _break_even_df(df, extra)}
            _log(f"frame extra cenario={extra} dre={len(extra_frames[str(extra)]['dre'])}")
    elif not is_all_scenarios(scenario) and "CENA" in df.columns:
        recorte = df.loc[df["CENA"].astype(str) == str(scenario)]
        _log(f"filtro CENA={scenario} {len(df)} -> {len(recorte)}")
        df = recorte
    frames = _frames_relatorio(df, scenario)
    pdf_bytes = generate_custom_report_pdf(
        df,
        scenario=scenario,
        selected_blocks=payload["selected_blocks"],
        notes=payload["notes"],
        author=payload["author"],
        profile=payload["profile"],
        company_name=payload["company_name"],
        comparison_scenarios=comparacoes,
        dre=frames["dre"],
        be=frames["be"],
        ltv=frames["ltv"],
        extra_frames=extra_frames,
        skip_charts=True,
        use_llm=False,
    )
    _log(f"PDF OK bytes={len(pdf_bytes)} em {time.time() - t0:.2f}s")
    return pdf_bytes


def flush_pending_pdf() -> None:
    """Gera o PDF fora do st.dialog para o websocket nao cair no meio do modal."""
    pending = st.session_state.get(PENDING_KEY)
    if not pending:
        return
    _log("flush_pending_pdf — geracao fora do dialog")
    try:
        with st.spinner(t("report.spinner")):
            pdf_bytes = _gerar_pdf(pending)
    except Exception as exc:  # noqa: BLE001
        st.session_state.pop(PENDING_KEY, None)
        _log(f"geracao FALHOU {type(exc).__name__}: {exc}\n{traceback.format_exc()}")
        st.session_state["_cti_report_error"] = f"{type(exc).__name__}: {exc}"
        return
    st.session_state.pop(PENDING_KEY, None)
    st.session_state.pop("_cti_report_error", None)
    st.session_state["custom_report_pdf"] = pdf_bytes
    st.session_state["custom_report_filename"] = pending["filename"]
    _log(f"flush_pending_pdf OK bytes={len(pdf_bytes)}")


def render_dialog(cena_sel: str, ano_sel: str | int, cenas: list[str] | None = None, df: pd.DataFrame | None = None) -> None:
    """Renderiza o report builder em modal estavel com formulario."""
    _ = df
    titulo = t("report.title")
    try:
        decorator = st.dialog(titulo, **dialog_kwargs(width="large", on_dismiss=close_relatorio))
    except TypeError:
        decorator = st.dialog(titulo, width="large")

    @decorator
    def _dialog() -> None:
        _render_report_body(cena_sel, ano_sel, cenas)

    _log(f"dialog a abrir cena={cena_sel} ano={ano_sel} opcoes_cena={len(cenas or [])}")
    _dialog()


def _render_report_body(cena_sel: str, ano_sel: str | int, cenas: list[str] | None) -> None:
    _ = ano_sel
    st.caption(t("report.caption"))

    try:
        block_options, default_block_notes, _generate = _load_report_backend()
        blocks = block_options()
        suggested_notes = default_block_notes(None, cena_sel)
    except Exception as exc:  # noqa: BLE001
        _log(f"init FALHOU {type(exc).__name__}: {exc}\n{traceback.format_exc()}")
        st.error(t("report.init_error", err=f"{type(exc).__name__}: {exc}"))
        if st.button(t("report.close"), key="report_init_close"):
            close_relatorio()
            st.rerun()
        return

    st.session_state.setdefault("report_c_level", "CEO")
    _ensure_report_defaults(st.session_state["report_c_level"], blocks, suggested_notes)

    erro = st.session_state.pop("_cti_report_error", None)
    if erro:
        st.error(t("report.pdf_error", err=erro))
    elif st.session_state.get("custom_report_pdf"):
        st.success(t("report.preview_ok"))

    with st.form("form_report_builder", clear_on_submit=False):
        profile_col, author_col, company_col = st.columns([0.22, 0.38, 0.4])
        with profile_col:
            profile = st.selectbox(t("report.profile"), ["CEO", "CFO", "CTO"], key="report_c_level")
        with author_col:
            if "report_author" not in st.session_state:
                st.session_state["report_author"] = t("report.author_default")
            author = st.text_input(t("report.author"), key="report_author")
        with company_col:
            company_name = st.text_input(t("report.company"), value="Grupo ESC", key="report_company_name")

        selected_blocks = st.multiselect(
            t("report.blocks"),
            options=list(blocks),
            format_func=lambda block_id: t(f"report.block.{block_id}"),
            key="report_selected_blocks",
            help=t("report.blocks_help"),
        )

        comparison_scenarios: list[str] = []
        if "scenario_comparison" in selected_blocks:
            scenarios = _available_scenarios(cenas, cena_sel)
            comparison_options = [item for item in scenarios if item != cena_sel]
            st.session_state["report_scenarios"] = [
                item for item in st.session_state.get("report_scenarios", []) if item in comparison_options
            ]
            comparison_scenarios = st.multiselect(
                t("report.scenarios"),
                options=comparison_options,
                key="report_scenarios",
            )

        st.markdown(f"#### {t('report.notes')}")
        if not selected_blocks:
            st.warning(t("report.need_block"))
        for block_id in selected_blocks:
            label = t(f"report.block.{block_id}")
            with st.expander(t("report.edit_note", label=label), expanded=False):
                st.text_area(
                    label,
                    height=150,
                    key=f"text_parecer_{block_id}",
                    label_visibility="collapsed",
                )

        confirm_col, generate_col, close_col = st.columns([0.36, 0.36, 0.28])
        with confirm_col:
            confirmed = st.form_submit_button(t("report.confirm"), use_container_width=True)
        with generate_col:
            generate_pdf = st.form_submit_button(t("report.generate"), type="primary", use_container_width=True)
        with close_col:
            close_dialog = st.form_submit_button(t("report.close"), use_container_width=True)

    if close_dialog:
        close_relatorio()
        st.rerun()

    notes = _build_notes(selected_blocks)
    filename_scenario = str(cena_sel).lower().replace(" ", "_").replace("/", "_")
    filename = f"relatorio_personalizado_esc_{profile.lower()}_{filename_scenario}_{datetime.now():%Y%m%d}.pdf"

    if confirmed or generate_pdf:
        if not selected_blocks:
            st.error(t("report.need_block_pdf"))
            return
        _log(
            f"pedido PDF na fila confirm={confirmed} generate={generate_pdf} "
            f"blocos={selected_blocks} cenario={cena_sel}"
        )
        st.session_state[PENDING_KEY] = {
            "scenario": cena_sel,
            "selected_blocks": list(selected_blocks),
            "notes": notes,
            "author": author,
            "profile": profile,
            "company_name": company_name,
            "comparison_scenarios": list(comparison_scenarios),
            "filename": filename,
        }
        st.rerun()

    preview_pdf = st.session_state.get("custom_report_pdf")
    if isinstance(preview_pdf, dict):
        preview_pdf = preview_pdf.get("bytes")
    if preview_pdf:
        st.subheader(t("report.preview"))
        st.caption(t("report.download"))
        st.download_button(
            t("report.download"),
            data=preview_pdf,
            file_name=st.session_state.get("custom_report_filename", filename),
            mime="application/pdf",
            help=f"Relatorio personalizado do cenario {cena_rotulo(cena_sel)}.",
            use_container_width=True,
        )
