"""Entrada temporaria de novos dados para o dashboard."""

from __future__ import annotations

from io import BytesIO, StringIO
from pathlib import Path

import pandas as pd
import streamlit as st

from src.models.loaders import normalizar_conta, otimizar_base_cti, parse_valor_br

DF_OVERRIDE_KEY = "cti_df_override"
DATASETS_KEY = "cti_datasets"
ACTIVE_DATASET_KEY = "cti_active_dataset_name"
PENDING_ACTIVE_DATASET_KEY = "cti_pending_active_dataset_name"
UPLOAD_COUNTER_KEY = "cti_upload_counter"
ORIGINAL_DATASET_KEY = "cti_original_dataset"
DEFAULT_MODIFIED_KEY = "cti_default_dataset_modified"
DEFAULT_DATASET_NAME = "Base Padrão (Original)"
REQUIRED_LONG_COLUMNS = {"ANO", "CENA", "CONTA", "VALOR", "ano_num"}
SCENARIO_ALIASES = {
    "cenario": "CENA",
    "cenário": "CENA",
    "scenario": "CENA",
    "cena": "CENA",
}
COLUMN_ALIASES = {
    "ano": "ANO",
    "ano_num": "ano_num",
    "conta": "CONTA",
    "indicador": "CONTA",
    "métrica": "CONTA",
    "metrica": "CONTA",
    "valor": "VALOR",
    **SCENARIO_ALIASES,
}


def has_custom_data() -> bool:
    return (
        st.session_state.get(ACTIVE_DATASET_KEY) != DEFAULT_DATASET_NAME
        or bool(st.session_state.get(DEFAULT_MODIFIED_KEY))
        or isinstance(st.session_state.get(DF_OVERRIDE_KEY), pd.DataFrame)
    )


def _clean_col_name(col: object) -> str:
    return str(col).strip()


def _rename_aliases(df: pd.DataFrame) -> pd.DataFrame:
    rename: dict[str, str] = {}
    for col in df.columns:
        clean = _clean_col_name(col)
        canonical = COLUMN_ALIASES.get(clean.lower(), clean)
        rename[col] = canonical
    return df.rename(columns=rename)


def _to_number(series: pd.Series) -> pd.Series:
    if pd.api.types.is_numeric_dtype(series):
        return pd.to_numeric(series, errors="coerce")
    return parse_valor_br(series)


def _read_upload(uploaded_file) -> pd.DataFrame:
    suffix = Path(uploaded_file.name).suffix.lower()
    payload = uploaded_file.getvalue()
    if suffix == ".xlsx":
        return pd.read_excel(BytesIO(payload))
    texto = payload.decode("utf-8-sig", errors="ignore")
    try:
        dados = pd.read_csv(StringIO(texto), sep=None, engine="python")
        known = {str(col).strip().lower() for col in dados.columns} & set(COLUMN_ALIASES)
        if known:
            return dados
        return pd.read_csv(StringIO(texto), header=None, names=["ANO", "CENA", "CONTA", "VALOR"])
    except Exception:
        return pd.read_csv(StringIO(texto), header=None, names=["ANO", "CENA", "CONTA", "VALOR"])


def _long_from_wide(df: pd.DataFrame) -> pd.DataFrame:
    id_cols = [col for col in ["ANO", "ano_num", "CENA"] if col in df.columns]
    metric_cols = [col for col in df.columns if col not in {*id_cols, "CONTA", "VALOR"}]
    if not {"CENA", "ano_num"}.issubset(df.columns) or not metric_cols:
        return pd.DataFrame(columns=list(REQUIRED_LONG_COLUMNS))
    base = df.copy()
    if "ANO" not in base.columns:
        base["ANO"] = "Ano " + pd.to_numeric(base["ano_num"], errors="coerce").fillna(0).astype(int).astype(str)
    return base.melt(
        id_vars=["ANO", "ano_num", "CENA"],
        value_vars=metric_cols,
        var_name="CONTA",
        value_name="VALOR",
    )


def normalizar_novos_dados(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    erros: list[str] = []
    if df.empty:
        return pd.DataFrame(columns=list(REQUIRED_LONG_COLUMNS)), ["A tabela enviada esta vazia."]

    dados = _rename_aliases(df).copy()
    if not {"CENA", "CONTA", "VALOR"}.issubset(dados.columns):
        dados = _long_from_wide(dados)

    missing = {"CENA", "CONTA", "VALOR"} - set(dados.columns)
    if missing:
        erros.append("Colunas obrigatorias ausentes: " + ", ".join(sorted(missing)))
        return pd.DataFrame(columns=list(REQUIRED_LONG_COLUMNS)), erros

    if "ano_num" not in dados.columns:
        if "ANO" in dados.columns:
            dados["ano_num"] = dados["ANO"].astype(str).str.extract(r"(\d+)", expand=False)
        else:
            erros.append("Coluna obrigatoria ausente: ano_num ou ANO.")
            return pd.DataFrame(columns=list(REQUIRED_LONG_COLUMNS)), erros

    dados["ano_num"] = pd.to_numeric(dados["ano_num"], errors="coerce").astype("Int64")
    if "ANO" not in dados.columns:
        dados["ANO"] = "Ano " + dados["ano_num"].fillna(0).astype(int).astype(str)

    dados = dados.dropna(subset=["ano_num"]).copy()
    dados["CENA"] = dados["CENA"].astype(str).str.strip()
    dados["CONTA"] = normalizar_conta(dados["CONTA"])
    dados["VALOR"] = _to_number(dados["VALOR"]).fillna(0)
    dados = dados.loc[(dados["CENA"] != "") & (dados["CONTA"] != "")]
    if dados.empty:
        erros.append("Nenhuma linha valida foi encontrada apos a normalizacao.")
    return dados[["ANO", "CENA", "CONTA", "VALOR", "ano_num"]].reset_index(drop=True), erros


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

    with st.sidebar.expander("Inserção de Dados", expanded=False):
        st.subheader("Gerenciador de Bases de Dados")

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
            "Selecione a Base Ativa",
            options=dataset_names,
            index=dataset_names.index(st.session_state["active_dataset_selector"]),
            key="active_dataset_selector",
        )
        st.session_state[ACTIVE_DATASET_KEY] = selected_name
        active_df = st.session_state[DATASETS_KEY][selected_name]
        _sync_legacy_override(selected_name, active_df)

        st.caption(f"Base ativa: {len(active_df):,} linhas.")
        st.markdown("---")
        st.caption("Carregue CSV/XLSX ou edite linhas manualmente no formato da base.")
        uploaded = st.file_uploader("Arquivo de novos dados", type=["csv", "xlsx"], key="new_data_upload")
        default_name = _default_upload_name(uploaded)
        custom_name = st.text_input(
            "Nome da nova base",
            value="",
            placeholder=default_name,
            key="new_dataset_name",
            help="Usado ao salvar como nova base.",
        )
        mode = st.radio(
            "Modo de aplicação",
            ["Salvar como Nova Base", "Concatenar à Base Selecionada"],
            horizontal=False,
            key="new_data_mode",
        )

        manual = st.data_editor(
            st.session_state.get("manual_data_rows", _manual_template()),
            num_rows="dynamic",
            width="stretch",
            key="manual_data_editor",
        )

        if st.button("Aplicar/Salvar Novos Dados", type="primary", key="apply_new_data"):
            frames: list[pd.DataFrame] = []
            erros: list[str] = []
            if uploaded is not None:
                try:
                    raw_upload = _read_upload(uploaded)
                    upload_df, upload_errors = normalizar_novos_dados(raw_upload)
                    frames.append(upload_df)
                    erros.extend(upload_errors)
                except Exception as exc:
                    erros.append(f"Falha ao ler arquivo: {exc}")

            manual_df, manual_errors = normalizar_novos_dados(pd.DataFrame(manual))
            if not manual_df.empty:
                frames.append(manual_df)
            elif uploaded is None:
                erros.extend(manual_errors)

            novos = pd.concat(frames, ignore_index=True, copy=False) if frames else pd.DataFrame(columns=current_df.columns)
            if not novos.empty:
                novos["VALOR"] = pd.to_numeric(novos["VALOR"], errors="coerce").fillna(0)
                novos = otimizar_base_cti(novos)
            if erros and novos.empty:
                st.error(" ".join(erros))
            else:
                if mode == "Salvar como Nova Base":
                    dataset_name = _unique_dataset_name(custom_name or default_name)
                    st.session_state[DATASETS_KEY][dataset_name] = novos
                    st.session_state[ACTIVE_DATASET_KEY] = dataset_name
                    st.session_state[PENDING_ACTIVE_DATASET_KEY] = dataset_name
                    st.session_state[UPLOAD_COUNTER_KEY] = int(st.session_state.get(UPLOAD_COUNTER_KEY, 0)) + 1
                    st.success(f"{len(novos):,} linhas salvas em '{dataset_name}'.")
                else:
                    updated_df = pd.concat([active_df, novos], ignore_index=True, copy=False)
                    updated_df["VALOR"] = pd.to_numeric(updated_df["VALOR"], errors="coerce").fillna(0)
                    updated_df = otimizar_base_cti(updated_df)
                    st.session_state[DATASETS_KEY][selected_name] = updated_df
                    st.session_state[ACTIVE_DATASET_KEY] = selected_name
                    st.session_state[PENDING_ACTIVE_DATASET_KEY] = selected_name
                    if selected_name == DEFAULT_DATASET_NAME:
                        st.session_state[DEFAULT_MODIFIED_KEY] = True
                    st.success(f"{len(novos):,} linhas concatenadas em '{selected_name}'.")
                st.rerun()

        if st.button("Restaurar Dados Originais", key="restore_original_data"):
            original_df = st.session_state.get(ORIGINAL_DATASET_KEY, current_df)
            st.session_state[DATASETS_KEY][DEFAULT_DATASET_NAME] = original_df
            st.session_state[ACTIVE_DATASET_KEY] = DEFAULT_DATASET_NAME
            st.session_state[PENDING_ACTIVE_DATASET_KEY] = DEFAULT_DATASET_NAME
            st.session_state[DEFAULT_MODIFIED_KEY] = False
            st.session_state.pop(DF_OVERRIDE_KEY, None)
            st.success("Base original restaurada.")
            st.rerun()

        removable = [name for name in st.session_state[DATASETS_KEY] if name != DEFAULT_DATASET_NAME]
        if removable:
            st.markdown("---")
            if st.session_state.get("delete_dataset_name") not in removable:
                st.session_state["delete_dataset_name"] = removable[0]
            delete_name = st.selectbox("Excluir base adicionada", options=removable, key="delete_dataset_name")
            if st.button("Excluir Base Selecionada", key="delete_dataset"):
                st.session_state[DATASETS_KEY].pop(delete_name, None)
                if st.session_state.get(ACTIVE_DATASET_KEY) == delete_name:
                    st.session_state[ACTIVE_DATASET_KEY] = DEFAULT_DATASET_NAME
                    st.session_state[PENDING_ACTIVE_DATASET_KEY] = DEFAULT_DATASET_NAME
                    st.session_state.pop(DF_OVERRIDE_KEY, None)
                st.success(f"Base '{delete_name}' excluida.")
                st.rerun()

    return active_df
