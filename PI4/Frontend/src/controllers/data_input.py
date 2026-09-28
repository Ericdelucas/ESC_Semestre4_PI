"""Entrada temporaria de novos dados para o dashboard."""

from __future__ import annotations

from io import BytesIO, StringIO
from pathlib import Path

import pandas as pd
import streamlit as st

from src.models.loaders import normalizar_conta, parse_valor_br

DF_OVERRIDE_KEY = "cti_df_override"
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
    return isinstance(st.session_state.get(DF_OVERRIDE_KEY), pd.DataFrame)


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


def render_data_input(current_df: pd.DataFrame) -> pd.DataFrame:
    """Renderiza insercao de dados na sidebar e retorna o DataFrame ativo."""
    active_df = st.session_state.get(DF_OVERRIDE_KEY)
    if not isinstance(active_df, pd.DataFrame):
        active_df = current_df

    with st.sidebar.expander("Inserção de Dados", expanded=False):
        st.caption("Carregue CSV/XLSX ou edite linhas manualmente no formato da base.")
        uploaded = st.file_uploader("Arquivo de novos dados", type=["csv", "xlsx"], key="new_data_upload")
        mode = st.radio("Modo de aplicação", ["Concatenar à base atual", "Substituir base atual"], horizontal=False, key="new_data_mode")

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

            novos = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame(columns=current_df.columns)
            if erros and novos.empty:
                st.error(" ".join(erros))
            else:
                base = pd.DataFrame(columns=current_df.columns) if mode == "Substituir base atual" else active_df
                st.session_state[DF_OVERRIDE_KEY] = pd.concat([base, novos], ignore_index=True).fillna(0)
                st.success(f"{len(novos):,} linhas aplicadas.")
                st.rerun()

        if st.button("Restaurar Dados Originais", key="restore_original_data"):
            st.session_state.pop(DF_OVERRIDE_KEY, None)
            st.success("Base original restaurada.")
            st.rerun()

        if isinstance(st.session_state.get(DF_OVERRIDE_KEY), pd.DataFrame):
            st.info(f"Base customizada ativa: {len(active_df):,} linhas.")

    return active_df
