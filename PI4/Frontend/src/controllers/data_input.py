"""Entrada temporaria de novos dados para o dashboard."""

from __future__ import annotations

import traceback
from io import BytesIO

import pandas as pd
import streamlit as st

from src.config.i18n import get_lang, t
from src.models.formatting.tables import render_table
from src.models.loaders import REQUIRED_LONG_COLUMNS, importar_planilha, normalizar_upload, otimizar_base_cti

DF_OVERRIDE_KEY = "cti_df_override"
DATASETS_KEY = "cti_datasets"
ACTIVE_DATASET_KEY = "cti_active_dataset_name"
PENDING_ACTIVE_DATASET_KEY = "cti_pending_active_dataset_name"
UPLOAD_COUNTER_KEY = "cti_upload_counter"
ORIGINAL_DATASET_KEY = "cti_original_dataset"
DEFAULT_MODIFIED_KEY = "cti_default_dataset_modified"
DEFAULT_DATASET_NAME = "Base Padrão (Original)"


def has_custom_data() -> bool:
    return (
        st.session_state.get(ACTIVE_DATASET_KEY) != DEFAULT_DATASET_NAME
        or bool(st.session_state.get(DEFAULT_MODIFIED_KEY))
        or isinstance(st.session_state.get(DF_OVERRIDE_KEY), pd.DataFrame)
    )


def normalizar_novos_dados(df: pd.DataFrame, *, nome_arquivo: str = "editor_manual") -> tuple[pd.DataFrame, list[str]]:
    return normalizar_upload(df, nome_arquivo=nome_arquivo)


def _exemplo_largo() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "ID_Cenario": ["Cen_00001", "Cen_00001", "Cen_00002"],
            "Nome_Cenario": ["Base", "Base", "Estresse"],
            "Ano": [1, 2, 1],
            "Receita Bruta (R$)": [1_000_000, 1_100_000, 800_000],
            "EBITDA": [250_000, 270_000, 120_000],
            "Custos": [400_000, 420_000, 380_000],
        }
    )


def _exemplo_longo() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "ANO": ["Ano 1", "Ano 1", "Ano 2"],
            "CENA": ["Cen_00001", "Cen_00001", "Cen_00001"],
            "CONTA": ["DRE - Receita", "DRE - EBITDA", "DRE - Receita"],
            "VALOR": [1_000_000, 250_000, 1_100_000],
        }
    )


def _bytes_template_xlsx() -> bytes:
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        _exemplo_largo().to_excel(writer, index=False, sheet_name="formato_largo")
        _exemplo_longo().to_excel(writer, index=False, sheet_name="formato_longo")
    return buffer.getvalue()


def _bytes_template_csv() -> bytes:
    return _exemplo_largo().to_csv(index=False).encode("utf-8-sig")


def _erro_amigavel(erro: object, *, nome_arquivo: str = "") -> str:
    texto = str(erro or "").strip()
    baixo = texto.lower()
    if "traceback" in baixo:
        texto = texto.split("Traceback", 1)[0].strip()
    if "cena" in baixo and ("nao encontrada" in baixo or "não encontrada" in baixo or "ausente" in baixo or "obrigator" in baixo):
        return t("data.err.missing_cena")
    if "coluna obrigatoria" in baixo or "coluna obrigatória" in baixo or "required column" in baixo:
        return texto or t("data.err.generic")
    if "unique requires" in baixo:
        return t("data.err.generic")
    if isinstance(erro, KeyError):
        coluna = str(erro).strip("'\"")
        if coluna in {"None", "nan", "", "CENA"}:
            return t("data.err.missing_cena")
        return t("data.err.missing_col", col=coluna)
    if not texto:
        return t("data.err.generic")
    if nome_arquivo and nome_arquivo not in texto:
        return f"{texto} ({nome_arquivo})"
    return texto


def _mostrar_erros(erros: list[str]) -> None:
    for erro in erros:
        st.error(_erro_amigavel(erro))


def _render_guia_formato() -> None:
    st.info(f"**{t('data.guide.title')}**\n\n{t('data.guide.body')}")
    with st.expander(t("data.example.expander"), expanded=False):
        st.caption(t("data.example.wide"))
        render_table(_exemplo_largo())
        st.caption(t("data.example.long"))
        render_table(_exemplo_longo())
        st.download_button(
            t("data.template.xlsx"),
            data=_bytes_template_xlsx(),
            file_name="template_exemplo.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key="download_template_xlsx",
            use_container_width=True,
        )
        st.download_button(
            t("data.template.csv"),
            data=_bytes_template_csv(),
            file_name="template_exemplo.csv",
            mime="text/csv",
            key="download_template_csv",
            use_container_width=True,
        )


def _manual_template() -> pd.DataFrame:
    return pd.DataFrame(columns=["ANO", "ano_num", "CENA", "CONTA", "VALOR"])


def _unique_dataset_name(name: str) -> str:
    datasets = st.session_state.get(DATASETS_KEY, {})
    base = name.strip() or "Base Personalizada"
    if base not in datasets:
        return base
    counter = 2
    while f"{base} ({counter})" in datasets:
        counter += 1
    return f"{base} ({counter})"


def _default_upload_name(uploaded_file) -> str:
    counter = int(st.session_state.get(UPLOAD_COUNTER_KEY, 0)) + 1
    if uploaded_file is not None:
        return f"Base Upload {counter} ({uploaded_file.name})"
    return f"Base Manual {counter}"


def _init_datasets(current_df: pd.DataFrame) -> None:
    if DATASETS_KEY not in st.session_state or not isinstance(st.session_state.get(DATASETS_KEY), dict):
        st.session_state[ORIGINAL_DATASET_KEY] = current_df
        st.session_state[DATASETS_KEY] = {DEFAULT_DATASET_NAME: current_df}
        st.session_state[ACTIVE_DATASET_KEY] = DEFAULT_DATASET_NAME
        st.session_state[DEFAULT_MODIFIED_KEY] = False

        legado = st.session_state.get(DF_OVERRIDE_KEY)
        if isinstance(legado, pd.DataFrame):
            legacy_name = _unique_dataset_name("Base Customizada (Legado)")
            st.session_state[DATASETS_KEY][legacy_name] = otimizar_base_cti(legado)
            st.session_state[ACTIVE_DATASET_KEY] = legacy_name
    else:
        st.session_state.setdefault(ORIGINAL_DATASET_KEY, current_df)
        st.session_state.setdefault(DEFAULT_MODIFIED_KEY, False)
        st.session_state[DATASETS_KEY].setdefault(DEFAULT_DATASET_NAME, st.session_state[ORIGINAL_DATASET_KEY])
        if st.session_state.get(ACTIVE_DATASET_KEY) not in st.session_state[DATASETS_KEY]:
            st.session_state[ACTIVE_DATASET_KEY] = DEFAULT_DATASET_NAME

    st.session_state.setdefault(UPLOAD_COUNTER_KEY, 0)


def _sync_legacy_override(active_name: str, active_df: pd.DataFrame) -> None:
    if active_name == DEFAULT_DATASET_NAME and not st.session_state.get(DEFAULT_MODIFIED_KEY):
        st.session_state.pop(DF_OVERRIDE_KEY, None)
    else:
        st.session_state[DF_OVERRIDE_KEY] = active_df


def render_data_input(current_df: pd.DataFrame) -> pd.DataFrame:
    """Renderiza insercao de dados na sidebar e retorna o DataFrame ativo."""
    _init_datasets(current_df)

    with st.sidebar.expander(t("data.expander"), expanded=False):
        st.subheader(t("data.manager"))

        dataset_names = list(st.session_state[DATASETS_KEY].keys())
        pending_name = st.session_state.pop(PENDING_ACTIVE_DATASET_KEY, None)
        if pending_name in dataset_names:
            st.session_state[ACTIVE_DATASET_KEY] = pending_name
            st.session_state["active_dataset_selector"] = pending_name

        active_name = st.session_state.get(ACTIVE_DATASET_KEY, DEFAULT_DATASET_NAME)
        if active_name not in dataset_names:
            active_name = DEFAULT_DATASET_NAME
            st.session_state[ACTIVE_DATASET_KEY] = active_name
        if st.session_state.get("active_dataset_selector") not in dataset_names:
            st.session_state["active_dataset_selector"] = active_name

        selected_name = st.selectbox(
            t("data.active_select"),
            options=dataset_names,
            index=dataset_names.index(st.session_state["active_dataset_selector"]),
            format_func=lambda name: t("data.default_name") if name == DEFAULT_DATASET_NAME else name,
            key="active_dataset_selector",
        )
        st.session_state[ACTIVE_DATASET_KEY] = selected_name
        active_df = st.session_state[DATASETS_KEY][selected_name]
        _sync_legacy_override(selected_name, active_df)

        st.caption(t("data.active_caption", n=f"{len(active_df):,}"))
        with st.expander(t("data.preview"), expanded=False):
            preview = active_df.head(40).copy()
            render_table(preview)
        st.markdown("---")
        st.caption(t("data.help"))
        _render_guia_formato()
        uploaded = st.file_uploader(t("data.upload"), type=["csv", "xlsx"], key="new_data_upload")
        default_name = _default_upload_name(uploaded)
        custom_name = st.text_input(
            t("data.new_name"),
            value="",
            placeholder=default_name,
            key="new_dataset_name",
            help=t("data.new_name_help"),
        )
        mode_new = t("data.mode.new")
        mode_concat = t("data.mode.concat")
        mode = st.radio(
            t("data.mode"),
            [mode_new, mode_concat],
            horizontal=False,
            key=f"new_data_mode_{get_lang()}",
        )

        manual = st.data_editor(
            st.session_state.get("manual_data_rows", _manual_template()),
            num_rows="dynamic",
            width="stretch",
            key="manual_data_editor",
            column_config={
                "ANO": st.column_config.TextColumn("ANO"),
                "ano_num": st.column_config.NumberColumn("ano_num", format="%d", min_value=1, step=1),
                "CENA": st.column_config.TextColumn("CENA"),
                "CONTA": st.column_config.TextColumn("CONTA"),
                "VALOR": st.column_config.NumberColumn("VALOR", format="R$ %.2f", step=0.01),
            },
        )
        st.session_state["manual_data_rows"] = pd.DataFrame(manual)

        if st.button(t("data.apply"), type="primary", key="apply_new_data"):
            try:
                frames: list[pd.DataFrame] = []
                erros: list[str] = []
                if uploaded is not None:
                    upload_df, upload_errors = importar_planilha(uploaded.name, uploaded.getvalue())
                    if not upload_df.empty:
                        frames.append(upload_df)
                    erros.extend(_erro_amigavel(item, nome_arquivo=uploaded.name) for item in upload_errors)

                manual_df, manual_errors = normalizar_novos_dados(pd.DataFrame(manual), nome_arquivo="editor_manual")
                if not manual_df.empty:
                    frames.append(manual_df)
                elif uploaded is None:
                    erros.extend(manual_errors)

                novos = pd.concat(frames, ignore_index=True, copy=False) if frames else pd.DataFrame(columns=list(REQUIRED_LONG_COLUMNS))
                if not novos.empty:
                    novos["VALOR"] = pd.to_numeric(novos["VALOR"], errors="coerce").fillna(0)
                    novos = otimizar_base_cti(novos)
                if novos.empty:
                    _mostrar_erros(erros or [t("data.err.generic")])
                else:
                    for aviso in erros:
                        st.warning(aviso)
                    if mode == mode_new:
                        dataset_name = _unique_dataset_name(custom_name or default_name)
                        st.session_state[DATASETS_KEY][dataset_name] = novos
                        st.session_state[ACTIVE_DATASET_KEY] = dataset_name
                        st.session_state[PENDING_ACTIVE_DATASET_KEY] = dataset_name
                        st.session_state[UPLOAD_COUNTER_KEY] = int(st.session_state.get(UPLOAD_COUNTER_KEY, 0)) + 1
                        st.success(t("data.saved", n=f"{len(novos):,}", name=dataset_name))
                    else:
                        updated_df = pd.concat([active_df, novos], ignore_index=True, copy=False)
                        updated_df["VALOR"] = pd.to_numeric(updated_df["VALOR"], errors="coerce").fillna(0)
                        updated_df = otimizar_base_cti(updated_df)
                        st.session_state[DATASETS_KEY][selected_name] = updated_df
                        st.session_state[ACTIVE_DATASET_KEY] = selected_name
                        st.session_state[PENDING_ACTIVE_DATASET_KEY] = selected_name
                        if selected_name == DEFAULT_DATASET_NAME:
                            st.session_state[DEFAULT_MODIFIED_KEY] = True
                        st.success(t("data.concatenated", n=f"{len(novos):,}", name=selected_name))
                    st.rerun()
            except Exception as exc:  # noqa: BLE001
                print(f"[CTI upload] Falha no aplicar dados: {type(exc).__name__}: {exc}", flush=True)
                traceback.print_exc()
                st.error(_erro_amigavel(exc, nome_arquivo=getattr(uploaded, "name", "")))

        if st.button(t("data.restore"), key="restore_original_data"):
            original_df = st.session_state.get(ORIGINAL_DATASET_KEY, current_df)
            st.session_state[DATASETS_KEY][DEFAULT_DATASET_NAME] = original_df
            st.session_state[ACTIVE_DATASET_KEY] = DEFAULT_DATASET_NAME
            st.session_state[PENDING_ACTIVE_DATASET_KEY] = DEFAULT_DATASET_NAME
            st.session_state[DEFAULT_MODIFIED_KEY] = False
            st.session_state.pop(DF_OVERRIDE_KEY, None)
            st.success(t("data.restored"))
            st.rerun()

        removable = [name for name in st.session_state[DATASETS_KEY] if name != DEFAULT_DATASET_NAME]
        if removable:
            st.markdown("---")
            if st.session_state.get("delete_dataset_name") not in removable:
                st.session_state["delete_dataset_name"] = removable[0]
            delete_name = st.selectbox(t("data.delete"), options=removable, key="delete_dataset_name")
            if st.button(t("data.delete_btn"), key="delete_dataset"):
                st.session_state[DATASETS_KEY].pop(delete_name, None)
                if st.session_state.get(ACTIVE_DATASET_KEY) == delete_name:
                    st.session_state[ACTIVE_DATASET_KEY] = DEFAULT_DATASET_NAME
                    st.session_state[PENDING_ACTIVE_DATASET_KEY] = DEFAULT_DATASET_NAME
                    st.session_state.pop(DF_OVERRIDE_KEY, None)
                st.success(t("data.deleted_ok", name=delete_name))
                st.rerun()

    return active_df
