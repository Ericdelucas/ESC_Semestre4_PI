"""Aba Assistente de IA CTI (RAG)."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from src.components.resilience import resilient_view
from src.config.i18n import get_lang, t
from src.data.formatting import cena_rotulo, fmt_pct
from src.data.rag_engine import RagEngine, resolve_api_key


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
    colada = str(st.session_state.get("google_api_key", "")).strip()
    if colada:
        return colada
    try:
        for nome in ("GOOGLE_API_KEY", "GEMINI_API_KEY"):
            val = str(st.secrets.get(nome, "")).strip()
            if val:
                return val
    except Exception:
        pass
    return resolve_api_key()


def _garantir_historico() -> list[dict[str, str]]:
    if "chat_history" not in st.session_state or not isinstance(st.session_state.chat_history, list):
        st.session_state.chat_history = []
    return st.session_state.chat_history


@resilient_view("aba Assistente de IA CTI")
def render(
    ranking: pd.DataFrame,
    n_cenarios: int,
    p_ruina: float,
    cena_sel: str,
    k: pd.Series,
    ano_enc: int,
) -> None:
    st.subheader(t("ai.title"))
    st.caption(t("ai.caption"))

    c1, c2 = st.columns([3, 1])
    with c1:
        chave_ui = st.text_input(
            t("ai.api_key"),
            type="password",
            key="gemini_key_input",
            help=t("ai.api_key_help"),
        )
        if chave_ui:
            st.session_state["google_api_key"] = chave_ui
    with c2:
        if st.button(t("ai.clear"), width="stretch"):
            st.session_state.chat_history = []
            st.rerun()

    if not _chave_api():
        st.info(t("ai.no_key"))

    engine = _carregar_engine(ranking, _fingerprint(ranking))
    st.caption(t("ai.indexed", n_docs=f"{len(engine.documents):,}", n_cen=f"{n_cenarios:,}", backend=engine.backend))

    historico = _garantir_historico()
    if not historico:
        st.chat_message("assistant").markdown(t("ai.welcome"))

    for msg in historico:
        papel = msg.get("role", "assistant")
        if papel not in {"user", "assistant"}:
            papel = "assistant"
        st.chat_message(papel).markdown(msg.get("content", ""))

    pergunta = st.chat_input(t("ai.placeholder"))
    if not pergunta:
        return

    historico.append({"role": "user", "content": pergunta})
    st.chat_message("user").markdown(pergunta)

    extra = t(
        "ai.extra_focus",
        cena=cena_rotulo(cena_sel),
        n=f"{n_cenarios:,}",
        p_ruina=f"{p_ruina:.1f}",
        ano=ano_enc,
        rent=fmt_pct(k["rentabilidade"]) if "rentabilidade" in k.index else "—",
    )
    with st.chat_message("assistant"):
        with st.spinner(t("ai.thinking")):
            resposta, fontes = engine.ask(
                pergunta,
                lang=get_lang(),
                history=historico[:-1],
                api_key=_chave_api(),
                extra_context=extra,
            )
        st.markdown(resposta)
        if fontes:
            st.caption(t("ai.sources") + ": " + " · ".join(fontes[:8]))
    historico.append({"role": "assistant", "content": resposta})
    st.session_state.chat_history = historico
