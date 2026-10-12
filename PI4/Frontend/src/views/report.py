"""Modal do construtor modular de relatorios executivos."""

from __future__ import annotations

import html
import os
import time
import traceback
from datetime import datetime
from io import BytesIO

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
    st.session_state["custom_report_preview_meta"] = _meta_preview(frames, payload)
    return pdf_bytes


def _meta_preview(frames: dict[str, pd.DataFrame], payload: dict) -> dict:
    from Backend.services.report_generator import format_exec_money, format_exec_pct

    dre = frames.get("dre") if isinstance(frames.get("dre"), pd.DataFrame) else pd.DataFrame()
    be = frames.get("be") if isinstance(frames.get("be"), pd.DataFrame) else pd.DataFrame()
    ltv = frames.get("ltv") if isinstance(frames.get("ltv"), pd.DataFrame) else pd.DataFrame()

    def _mean(tabela: pd.DataFrame, *nomes: str) -> float:
        for nome in nomes:
            if tabela is None or tabela.empty or nome not in tabela.columns:
                continue
            value = float(pd.to_numeric(tabela[nome], errors="coerce").mean())
            if not pd.isna(value):
                return value
        return 0.0

    receita = _mean(dre, "Receita Líquida", "Receita Liquida")
    ebitda = _mean(dre, "EBITDA")
    return {
        "company": payload.get("company_name") or "Grupo ESC",
        "profile": payload.get("profile") or "CEO",
        "scenario": payload.get("scenario") or "",
        "author": payload.get("author") or "",
        "blocks": list(payload.get("selected_blocks") or []),
        "notes": payload.get("notes") or {},
        "kpis": {
            "ebitda": format_exec_money(ebitda),
            "margem": format_exec_pct(ebitda / receita if receita else 0.0),
            "break_even": format_exec_money(_mean(be, "Break-Even")),
            "ltv_cac": f"{_mean(ltv, 'LTV/CAC'):.1f}x",
        },
        "dre": dre.head(12).to_dict("records") if not dre.empty else [],
        "be": be.head(12).to_dict("records") if not be.empty else [],
    }


def _pdf_para_imagens(pdf_bytes: bytes, max_paginas: int = 8) -> list[bytes]:
    """Rasteriza paginas do PDF em JPEG compacto para o modal."""
    t0 = time.time()
    try:
        import pypdfium2 as pdfium
    except Exception as exc:  # noqa: BLE001
        _log(f"pypdfium2 ausente ({type(exc).__name__}: {exc})")
        pdfium = None
    if pdfium is not None:
        try:
            doc = pdfium.PdfDocument(pdf_bytes)
            imagens: list[bytes] = []
            total = min(len(doc), max_paginas)
            for indice in range(total):
                pagina = doc[indice]
                pil = pagina.render(scale=1.35).to_pil().convert("RGB")
                if pil.width > 920:
                    ratio = 920 / pil.width
                    pil = pil.resize((920, max(1, int(pil.height * ratio))))
                buf = BytesIO()
                pil.save(buf, format="JPEG", quality=72, optimize=True)
                imagens.append(buf.getvalue())
            _log(f"preview pypdfium2 paginas={len(imagens)} em {time.time() - t0:.2f}s")
            return imagens
        except Exception as exc:  # noqa: BLE001
            _log(f"pypdfium2 FALHOU {type(exc).__name__}: {exc}")
    try:
        import fitz

        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        imagens = []
        total = min(doc.page_count, max_paginas)
        for indice in range(total):
            pix = doc.load_page(indice).get_pixmap(matrix=fitz.Matrix(1.3, 1.3), alpha=False)
            pil_bytes = pix.tobytes("jpeg")
            imagens.append(pil_bytes)
        _log(f"preview pymupdf paginas={len(imagens)} em {time.time() - t0:.2f}s")
        return imagens
    except Exception as exc:  # noqa: BLE001
        _log(f"raster PDF indisponivel ({type(exc).__name__}: {exc})")
    return []


def _html_folhas(meta: dict) -> str:
    kpis = meta.get("kpis") or {}
    notas = meta.get("notes") or {}
    kpis_html = "".join(
        f"<div class='kpi'><span>{html.escape(str(rotulo))}</span><strong>{html.escape(str(valor))}</strong></div>"
        for rotulo, valor in (
            ("EBITDA", kpis.get("ebitda", "—")),
            ("Margem", kpis.get("margem", "—")),
            ("Break-Even", kpis.get("break_even", "—")),
            ("LTV/CAC", kpis.get("ltv_cac", "—")),
        )
    )
    linhas_dre = "".join(
        "<tr>"
        + "".join(f"<td>{html.escape(str(row.get(col, '')))}</td>" for col in ("ano_num", "Receita Líquida", "EBITDA", "EBIT", "Lucro Líquido"))
        + "</tr>"
        for row in (meta.get("dre") or [])[:8]
    )
    pareceres = "".join(
        f"<p><strong>{html.escape(str(chave))}:</strong> {html.escape(str(texto)[:400])}</p>"
        for chave, texto in notas.items()
        if str(texto).strip()
    )
    return f"""
    <div class="folha">
      <h1>{html.escape(str(meta.get('company') or 'Grupo ESC'))}</h1>
      <p class="meta">{html.escape(str(meta.get('profile') or ''))} · {html.escape(str(meta.get('scenario') or ''))} · {html.escape(str(meta.get('author') or ''))}</p>
      <div class="kpis">{kpis_html}</div>
      <h2>DRE</h2>
      <table><thead><tr><th>Ano</th><th>Receita</th><th>EBITDA</th><th>EBIT</th><th>Lucro</th></tr></thead>
      <tbody>{linhas_dre or "<tr><td colspan='5'>—</td></tr>"}</tbody></table>
      {pareceres}
    </div>
    <style>
      .folha {{ background:#fff; color:#0f172a; padding:28px 32px; border-radius:10px;
                 font-family:Georgia, 'Times New Roman', serif; border:1px solid #cbd5e1; }}
      .folha h1 {{ margin:0 0 6px; font-size:22px; color:#0b1f33; }}
      .folha h2 {{ font-size:16px; color:#0b1f33; margin:18px 0 8px; }}
      .meta {{ color:#64748b; margin:0 0 16px; font-size:13px; }}
      .kpis {{ display:grid; grid-template-columns:repeat(4,1fr); gap:8px; margin:12px 0 18px; }}
      .kpi {{ background:#0b1f33; color:#fff; padding:10px 8px; text-align:center; border-radius:6px; }}
      .kpi span {{ display:block; font-size:10px; letter-spacing:.04em; color:#93c5fd; }}
      .kpi strong {{ font-size:14px; }}
      table {{ width:100%; border-collapse:collapse; font-size:12px; }}
      th, td {{ border-bottom:1px solid #e2e8f0; padding:6px 4px; text-align:left; }}
      p {{ font-size:13px; line-height:1.45; }}
    </style>
    """


def _botao_download(pdf_bytes: bytes, filename: str, cena_sel: str, key: str) -> None:
    st.download_button(
        t("report.download"),
        data=pdf_bytes,
        file_name=filename,
        mime="application/pdf",
        help=f"Relatorio personalizado do cenario {cena_rotulo(cena_sel)}.",
        use_container_width=True,
        key=key,
    )


def _mostrar_previsualizacao(pdf_bytes: bytes, filename: str, cena_sel: str) -> None:
    st.subheader(t("report.preview"))
    st.caption(t("report.preview_hint"))
    paginas = st.session_state.get("custom_report_preview_pages") or []
    mostrou = False
    if paginas:
        rotulos = [t("report.page", n=indice + 1, total=len(paginas)) for indice in range(len(paginas))]
        abas = st.tabs(rotulos)
        for aba, imagem in zip(abas, paginas):
            with aba:
                st.image(imagem, use_container_width=True)
        mostrou = True
    elif hasattr(st, "pdf"):
        try:
            st.pdf(pdf_bytes, height=620)
            mostrou = True
        except TypeError:
            try:
                st.pdf(pdf_bytes)
                mostrou = True
            except Exception as exc:  # noqa: BLE001
                _log(f"st.pdf FALHOU {type(exc).__name__}: {exc}")
        except Exception as exc:  # noqa: BLE001
            _log(f"st.pdf FALHOU {type(exc).__name__}: {exc}")
    if not mostrou:
        meta = st.session_state.get("custom_report_preview_meta") or {}
        import streamlit.components.v1 as components

        components.html(_html_folhas(meta), height=520, scrolling=True)
    _botao_download(pdf_bytes, filename, cena_sel, key="report_download_top")


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
    st.session_state["custom_report_preview_pages"] = _pdf_para_imagens(pdf_bytes)
    _log(
        f"flush_pending_pdf OK bytes={len(pdf_bytes)} "
        f"paginas_preview={len(st.session_state['custom_report_preview_pages'])}"
    )


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

    preview_pdf = st.session_state.get("custom_report_pdf")
    if isinstance(preview_pdf, dict):
        preview_pdf = preview_pdf.get("bytes")
    filename_atual = st.session_state.get(
        "custom_report_filename",
        f"relatorio_personalizado_esc_{datetime.now():%Y%m%d}.pdf",
    )
    if preview_pdf:
        st.success(t("report.preview_ok"))
        _mostrar_previsualizacao(preview_pdf, filename_atual, cena_sel)
        st.divider()

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

    if preview_pdf:
        _botao_download(
            preview_pdf,
            st.session_state.get("custom_report_filename", filename),
            cena_sel,
            key="report_download_bottom",
        )
