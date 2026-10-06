"""Modal do construtor modular de relatorios executivos."""

from __future__ import annotations

import base64
from datetime import datetime

import pandas as pd
import streamlit as st

from src.models.formatting import cena_rotulo


DEFAULT_BLOCKS_BY_PROFILE: dict[str, list[str]] = {
    "CEO": ["cover", "financial_dre", "break_even", "commercial", "scenario_comparison"],
    "CFO": ["cover", "financial_dre", "break_even", "commercial"],
    "CTO": ["cover", "operational_tech", "break_even", "scenario_comparison"],
}


def _available_scenarios(df: pd.DataFrame, current: str) -> list[str]:
    if "CENA" not in df.columns:
        return [current]
    scenarios = sorted(str(item) for item in df["CENA"].dropna().unique())
    return scenarios or [current]


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


def display_pdf_preview(pdf_bytes: bytes) -> None:
    """Exibe o PDF em iframe embutido no modal."""
    base64_pdf = base64.b64encode(pdf_bytes).decode("utf-8")
    pdf_display = (
        f'<iframe src="data:application/pdf;base64,{base64_pdf}" '
        'width="100%" height="500" type="application/pdf"></iframe>'
    )
    st.markdown(pdf_display, unsafe_allow_html=True)


@st.dialog("Criar Relatorio", width="large")
def render_dialog(df: pd.DataFrame, cena_sel: str, ano_sel: str | int) -> None:
    """Renderiza o report builder em modal estavel com formulario."""
    _ = ano_sel
    st.caption("Monte o PDF executivo. Os campos abaixo so atualizam quando voce confirma o formulario.")

    try:
        block_options, default_block_notes, generate_custom_report_pdf = _load_report_backend()
        blocks = block_options()
        suggested_notes = default_block_notes(df, cena_sel)
    except Exception as exc:  # noqa: BLE001
        st.error(f"Nao foi possivel inicializar o gerador de relatorios: {type(exc).__name__}: {exc}")
        return

    st.session_state.setdefault("report_c_level", "CEO")
    _ensure_report_defaults(st.session_state["report_c_level"], blocks, suggested_notes)

    with st.form("form_report_builder", clear_on_submit=False):
        profile_col, author_col, company_col = st.columns([0.22, 0.38, 0.4])
        with profile_col:
            profile = st.selectbox("Perfil C-Level", ["CEO", "CFO", "CTO"], key="report_c_level")
        with author_col:
            author = st.text_input("Autor", value="Equipe ESC", key="report_author")
        with company_col:
            company_name = st.text_input("Empresa", value="Grupo ESC", key="report_company_name")

        selected_blocks = st.multiselect(
            "Blocos do relatorio",
            options=list(blocks),
            format_func=lambda block_id: blocks[block_id],
            key="report_selected_blocks",
            help="Selecione apenas as secoes que devem entrar no PDF final.",
        )

        comparison_scenarios: list[str] = []
        if "scenario_comparison" in selected_blocks:
            scenarios = _available_scenarios(df, cena_sel)
            comparison_options = [item for item in scenarios if item != cena_sel]
            st.session_state["report_scenarios"] = [
                item for item in st.session_state.get("report_scenarios", []) if item in comparison_options
            ]
            comparison_scenarios = st.multiselect(
                "Cenarios para comparacao",
                options=comparison_options,
                key="report_scenarios",
            )

        st.markdown("#### Pareceres executivos")
        if not selected_blocks:
            st.warning("Selecione ao menos um bloco para gerar o relatorio.")
        for block_id in selected_blocks:
            label = blocks[block_id]
            with st.expander(f"✏️ Editar Parecer Executivo - {label}", expanded=False):
                st.text_area(
                    label,
                    height=150,
                    key=f"text_parecer_{block_id}",
                    label_visibility="collapsed",
                )

        confirm_col, generate_col, close_col = st.columns([0.36, 0.36, 0.28])
        with confirm_col:
            confirmed = st.form_submit_button("Atualizar Previa / Confirmar Dados", use_container_width=True)
        with generate_col:
            generate_pdf = st.form_submit_button("Gerar PDF Executivo", type="primary", use_container_width=True)
        with close_col:
            close_dialog = st.form_submit_button("Fechar", use_container_width=True)

    if close_dialog:
        st.session_state["show_report_modal"] = False
        st.rerun()

    notes = _build_notes(selected_blocks)
    filename_scenario = str(cena_sel).lower().replace(" ", "_").replace("/", "_")
    filename = f"relatorio_personalizado_esc_{profile.lower()}_{filename_scenario}_{datetime.now():%Y%m%d}.pdf"
    signature = repr((cena_sel, selected_blocks, notes, author, profile, company_name, comparison_scenarios))

    if confirmed or generate_pdf:
        if not selected_blocks:
            st.error("Selecione ao menos um bloco antes de gerar o PDF.")
            return
        try:
            with st.spinner("Montando pre-visualizacao em PDF..."):
                pdf_bytes = generate_custom_report_pdf(
                    df,
                    scenario=cena_sel,
                    selected_blocks=selected_blocks,
                    notes=notes,
                    author=author,
                    profile=profile,
                    company_name=company_name,
                    comparison_scenarios=comparison_scenarios,
                )
        except Exception as exc:  # noqa: BLE001
            st.error(f"Nao foi possivel gerar o PDF personalizado: {type(exc).__name__}: {exc}")
            return
        st.session_state["custom_report_pdf"] = pdf_bytes
        st.session_state["custom_report_filename"] = filename
        st.session_state["custom_report_signature"] = signature
        if confirmed and not generate_pdf:
            st.success("Pre-visualizacao atualizada. Revise o PDF abaixo antes do download.")

    # Exibicao fora do formulario: permanece visivel apos o submit do form.
    preview_pdf = st.session_state.get("custom_report_pdf")
    if isinstance(preview_pdf, dict):
        preview_pdf = preview_pdf.get("bytes")
    if preview_pdf:
        st.subheader("👁️ Pré-visualização do Relatório")
        display_pdf_preview(preview_pdf)
        st.download_button(
            "Download do Relatorio Personalizado (.pdf)",
            data=preview_pdf,
            file_name=st.session_state.get("custom_report_filename", filename),
            mime="application/pdf",
            help=f"Relatorio personalizado do cenario {cena_rotulo(cena_sel)}.",
            use_container_width=True,
        )
