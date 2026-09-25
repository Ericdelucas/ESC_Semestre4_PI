"""Painel de chat do Assistente CTI (RAG), no formato nativo do Streamlit."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from src.controllers.resilience import resilient_view
from src.config.i18n import get_lang
from src.models.formatting import cena_rotulo, fmt_pct
from src.models.rag_engine import RagEngine, build_focus_context, resolve_api_key

_BOAS_VINDAS = (
    "Olá! Sou o consultor virtual da CTI. Como posso ajudar com os cenários hoje?"
)


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


def render_chat_panel(
    ranking: pd.DataFrame,
    n_cenarios: int,
    p_ruina: float,
    cena_sel: str,
    k: pd.Series,
    ano_enc: int,
    ano_sel: str | int = "Todos",
) -> None:
    # 1. Cabeçalho limpo
    col_title, col_close = st.columns([4, 1])
    with col_title:
        st.subheader("🤖 Assistente CTI")
    with col_close:
        if st.button("✖", key="close_chat_btn"):
            st.session_state.show_chat = False
            st.rerun()

    # 2. Configurações técnicas escondidas
    with st.expander("⚙️ Configurações da API & Dados", expanded=False):
        st.text_input("Chave API Gemini", type="password", key="gemini_api_key_input")
        if st.button("Limpar Conversa"):
            st.session_state.chat_history = []
            st.rerun()

    # 3. Inicializar histórico se não existir
    if "chat_history" not in st.session_state or not isinstance(st.session_state.chat_history, list):
        legado = st.session_state.get("ai_chat_history")
        st.session_state.chat_history = legado if isinstance(legado, list) and legado else [
            {"role": "assistant", "content": _BOAS_VINDAS}
        ]

    # 4. Container com altura fixa para rolar as mensagens
    chat_container = st.container(height=450, border=True)
    with chat_container:
        for msg in st.session_state.chat_history:
            papel = msg.get("role", "assistant")
            if papel not in {"user", "assistant"}:
                papel = "assistant"
            with st.chat_message(papel):
                st.write(msg.get("content", ""))

    # 5. Caixa de texto dentro do painel (o chat_input nativo some da coluna)
    with st.form("cti_chat_form", clear_on_submit=True, border=False):
        prompt = st.text_area(
            "Mensagem",
            placeholder="Pergunte ao Assistente CTI...",
            label_visibility="collapsed",
            height=90,
        )
        enviar = st.form_submit_button("Enviar", type="primary", width="stretch")
    if not enviar or not prompt or not str(prompt).strip():
        return

    texto = str(prompt).strip()
    st.session_state.chat_history.append({"role": "user", "content": texto})
    try:
        engine = _carregar_engine(ranking, _fingerprint(ranking))
        with st.spinner("Consultando cenários e manuais…"):
            resposta, fontes = engine.ask(
                texto,
                lang=get_lang(),
                history=st.session_state.chat_history[:-1],
                api_key=_chave_api(),
                extra_context=_contexto_foco(
                    ranking, n_cenarios, p_ruina, cena_sel, k, ano_enc, ano_sel
                ),
                cena_sel=cena_sel,
            )
        if fontes:
            resposta = f"{resposta}\n\nFontes: {' · '.join(fontes[:8])}"
    except Exception as exc:
        resposta = f"Não consegui responder agora: {exc}"
    st.session_state.chat_history.append({"role": "assistant", "content": resposta})
    st.session_state.ai_chat_history = st.session_state.chat_history
    st.rerun()


def render_chat(
    ranking: pd.DataFrame,
    n_cenarios: int,
    p_ruina: float,
    cena_sel: str,
    k: pd.Series,
    ano_enc: int,
    ano_sel: str | int = "Todos",
    *,
    compact: bool = False,
) -> None:
    _ = compact
    render_chat_panel(ranking, n_cenarios, p_ruina, cena_sel, k, ano_enc, ano_sel)


@resilient_view("aba Assistente de IA CTI")
def render(
    ranking: pd.DataFrame,
    n_cenarios: int,
    p_ruina: float,
    cena_sel: str,
    k: pd.Series,
    ano_enc: int,
    ano_sel: str | int = "Todos",
) -> None:
    render_chat_panel(ranking, n_cenarios, p_ruina, cena_sel, k, ano_enc, ano_sel)
