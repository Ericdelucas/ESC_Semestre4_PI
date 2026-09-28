"""Contexto e cache do Assistente CTI."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from src.config.i18n import get_lang
from src.models.formatting import cena_rotulo, fmt_pct
from src.models.rag_engine import RagEngine, build_focus_context, resolve_api_key


def _fingerprint(ranking: pd.DataFrame) -> str:
    n = int(ranking.shape[0])
    caixa = ranking["caixa_ano12"] if "caixa_ano12" in ranking.columns else pd.Series(dtype=float)
    media = float(caixa.mean()) if not caixa.empty else 0.0
    return f"{n}:{media:.4f}"


@st.cache_resource(show_spinner="Indexando cenários e manuais da CTI…")
def _carregar_engine(_ranking: pd.DataFrame, fingerprint: str) -> RagEngine:
    _ = fingerprint
    return RagEngine.from_ranking(_ranking)


def _chave_api() -> str | None:
    colada = str(st.session_state.get("gemini_api_key_input", "")).strip()
    if colada:
        st.session_state["google_api_key"] = colada
        return colada
    antiga = str(st.session_state.get("google_api_key", "")).strip()
    if antiga:
        return antiga
    try:
        for nome in ("GOOGLE_API_KEY", "GEMINI_API_KEY"):
            val = str(st.secrets.get(nome, "")).strip()
            if val:
                return val
    except Exception:
        pass
    return resolve_api_key()


def _contexto_foco(
    ranking: pd.DataFrame,
    n_cenarios: int,
    p_ruina: float,
    cena_sel: str,
    k: pd.Series,
    ano_enc: int,
    ano_sel: str | int,
) -> str:
    rent = fmt_pct(k["rentabilidade"]) if "rentabilidade" in k.index else "—"
    intro = (
        f"Contexto da tela: cenário em foco {cena_rotulo(cena_sel)}; "
        f"{n_cenarios:,} cenários na base; prob. caixa negativo Ano {ano_enc}: {p_ruina:.1f}%; "
        f"rentabilidade do recorte {rent}."
    )
    detalhe = build_focus_context(
        ranking,
        cena_sel=cena_sel,
        n_cenarios=n_cenarios,
        p_ruina=p_ruina,
        ano_enc=ano_enc,
        k=k,
        ano_sel=ano_sel,
        lang=get_lang(),
    )
    return f"{intro}\n{detalhe}"
