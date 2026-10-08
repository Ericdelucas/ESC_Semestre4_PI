"""Painel conversacional do Assistente CTI."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from src.config.i18n import get_lang
from src.controllers.bootstrap import AppContext
from src.controllers.resilience import resilient_view

_BOAS_VINDAS = (
    "Assistente de Análise CTI pronto. Como posso ajudar com os indicadores de EBITDA, "
    "NCG, Liquidez ou navegação pelo dashboard?"
)
CHAT_NAV_CARDS_KEY = "cti_chat_nav_cards"
NAV_TARGETS = {
    "acionistas_retorno": {
        "label": "Retorno & ROIC",
        "persona": "acionistas",
        "description": "Visão de Acionistas com ROIC, ROE e WACC para avaliar retorno sobre o capital investido.",
        "terms": ("roic", "retorno sobre o capital", "capital investido", "roe", "wacc", "retorno do acionista", "retorno acionista"),
    },
    "acionistas_eva": {
        "label": "Geração de EVA",
        "persona": "acionistas",
        "description": "Visão de Acionistas com criação de valor econômico acima do custo de capital.",
        "terms": ("eva", "valor economico", "valor econômico", "criacao de valor", "criação de valor", "lucro economico", "lucro econômico"),
    },
    "acionistas_dividendos": {
        "label": "Lucro Líquido & Dividendos",
        "persona": "acionistas",
        "description": "Visão de Acionistas com lucro líquido, dividendos e reinvestimento.",
        "terms": ("dividendos", "dividendo", "payout", "lucro liquido", "lucro líquido", "reinvestimento"),
    },
    "concedente_capex": {
        "label": "Plano de CAPEX",
        "persona": "concedente",
        "description": "Visão de Poder Concedente com CAPEX anual e acumulado dos investimentos da concessão.",
        "terms": ("capex", "capital expenditure", "investimento", "investimentos", "infraestrutura", "plano de capex"),
    },
    "concedente_solvencia": {
        "label": "Solvência & Liquidez Geral",
        "persona": "concedente",
        "description": "Visão de Poder Concedente com liquidez geral, endividamento e cobertura de juros.",
        "terms": ("liquidez geral", "solvencia", "solvência", "obrigacoes contratuais", "obrigações contratuais"),
    },
    "concedente_ativos": {
        "label": "Ativos Reversíveis",
        "persona": "concedente",
        "description": "Visão de Poder Concedente com base líquida de ativos reversíveis.",
        "terms": ("ativos reversiveis", "ativos reversíveis", "base de ativos", "patrimonio", "patrimônio"),
    },
    "ceo_geral": {
        "label": "Visão Geral & DRE",
        "persona": "ceo",
        "description": "Resumo executivo com a cascata média da DRE e a evolução Receita Líquida vs EBITDA.",
        "terms": ("visao geral", "visão geral", "receita", "grafico de ebitda", "gráfico de ebitda"),
    },
    "ceo_dre": {
        "label": "DRE Operacional",
        "persona": "ceo",
        "description": "Aba com Receita Líquida, EBITDA, EBIT, Lucro Líquido e margens operacionais por ano.",
        "terms": ("dre", "dre operacional", "ebitda", "margem ebitda", "margem bruta", "margem ebit", "lucro liquido", "lucro líquido"),
    },
    "ceo_break_even": {
        "label": "Break-Even & Margens",
        "persona": "ceo",
        "description": "Seção de análise detalhada de margens, ponto de equilíbrio e margem de segurança.",
        "terms": ("break-even", "break even", "breakeven", "ponto de equilibrio", "ponto de equilíbrio", "margem de seguranca", "margem de segurança"),
    },
    "ceo_ltv_cac": {
        "label": "Eficiência LTV/CAC",
        "persona": "ceo",
        "description": "Aba com os indicadores LTV, CAC e razão LTV/CAC por ano.",
        "terms": ("ltv", "cac", "ltv/cac", "eficiencia", "eficiência"),
    },
    "capital_giro": {
        "label": "Capital de Giro",
        "persona": "cfo",
        "description": "Aba do CFO com NCG, Saldo de Tesouraria e dinâmica de capital de giro.",
        "terms": ("ncg", "capital de giro", "saldo de tesouraria", "tesouraria"),
    },
    "faixa": {
        "label": "Faixa de Risco",
        "persona": "cfo",
        "description": "Aba com leitura de risco, liquidez corrente e enquadramento dos indicadores por cenário.",
        "terms": ("liquidez", "liquidez corrente", "risco", "faixa de risco", "solvencia", "solvência"),
    },
    "como_ler": {
        "label": "Como Ler",
        "persona": "cfo",
        "description": "Aba de orientação com fórmulas, leitura dos indicadores e apoio para auditoria da base.",
        "terms": ("auditoria", "formula", "fórmula", "formulas", "fórmulas", "como ler", "regras de negocio", "regras de negócio"),
    },
}


def _inicializar_historico() -> None:
    if "messages" in st.session_state and isinstance(st.session_state.messages, list):
        st.session_state.messages = _sanitize_messages(st.session_state.messages)
        st.session_state.setdefault(CHAT_NAV_CARDS_KEY, {})
        return
    legado = st.session_state.get("chat_history", st.session_state.get("ai_chat_history"))
    st.session_state.messages = _sanitize_messages(legado) if isinstance(legado, list) and legado else [
        {"role": "assistant", "content": _BOAS_VINDAS}
    ]
    st.session_state.setdefault(CHAT_NAV_CARDS_KEY, {})
    _sync_historico_legado()


def _resetar_historico() -> None:
    st.session_state.messages = [{"role": "assistant", "content": _BOAS_VINDAS}]
    st.session_state[CHAT_NAV_CARDS_KEY] = {}
    _sync_historico_legado()


def _sync_historico_legado() -> None:
    st.session_state.messages = _sanitize_messages(st.session_state.messages)
    st.session_state.chat_history = st.session_state.messages
    st.session_state.ai_chat_history = st.session_state.messages


def _sanitize_messages(messages: list[dict[str, object]]) -> list[dict[str, str]]:
    limpas: list[dict[str, str]] = []
    for msg in messages:
        if not isinstance(msg, dict):
            continue
        role = str(msg.get("role", "assistant"))
        if role not in {"user", "assistant"}:
            role = "assistant"
        limpas.append({"role": role, "content": str(msg.get("content", ""))})
    return limpas


def _render_mensagens() -> None:
    for idx, msg in enumerate(st.session_state.messages):
        papel = msg.get("role", "assistant")
        if papel not in {"user", "assistant"}:
            papel = "assistant"
        with st.chat_message(papel):
            st.markdown(msg.get("content", ""))
            nav_card = st.session_state.get(CHAT_NAV_CARDS_KEY, {}).get(str(idx))
            if isinstance(nav_card, dict) and not nav_card.get("dismissed"):
                render_navigation_card(nav_card, idx)


def _render_chat_input_panel() -> str:
    with st.form("cti_chat_input_form", clear_on_submit=True, border=False):
        prompt = st.text_input(
            "Mensagem",
            placeholder="Pergunte algo sobre o projeto ou peça para ir a uma aba...",
            label_visibility="collapsed",
            key="cti_chat_text_input",
        )
        enviar = st.form_submit_button("Enviar", type="primary", width="stretch")
    return str(prompt or "").strip() if enviar else ""


def _normalizar_texto(texto: str) -> str:
    mapa = str.maketrans("áàâãäéèêëíìîïóòôõöúùûüç", "aaaaaeeeeiiiiooooouuuuc")
    return texto.lower().translate(mapa)


def detectar_intencao_navegacao(user_prompt: str, *, exigir_gatilho: bool = True) -> dict[str, str] | None:
    texto = _normalizar_texto(user_prompt)
    gatilhos = (
        "onde",
        "fica",
        "leve",
        "ir para",
        "abrir",
        "mostre",
        "mostrar",
        "grafico",
        "gráfico",
        "aba",
        "secao",
        "seção",
        "o que e",
        "o que é",
        "explique",
        "analise",
        "analisar",
    )
    if exigir_gatilho and not any(_normalizar_texto(gatilho) in texto for gatilho in gatilhos):
        return None
    for nav_key, cfg in NAV_TARGETS.items():
        if any(_normalizar_texto(term) in texto for term in cfg["terms"]):
            return {
                "nav_key": nav_key,
                "target_tab_name": cfg["label"],
                "persona": cfg["persona"],
                "description": cfg["description"],
            }
    return None


def render_navigation_card(nav_card: dict[str, str], message_idx: int) -> None:
    target_tab_name = nav_card["target_tab_name"]
    st.info(f"Atalho para visualização: {nav_card['description']}")
    col1, col2 = st.columns([1, 1])

    with col1:
        if st.button(f"🔗 Abrir {target_tab_name}", key=f"nav_open_{message_idx}_{nav_card['nav_key']}"):
            st.session_state["pending_nav_key"] = nav_card["nav_key"]
            st.session_state["pending_persona_id"] = nav_card.get("persona")
            st.session_state["active_tab"] = target_tab_name
            st.rerun()

    with col2:
        if st.button("❌ Cancelar", key=f"nav_cancel_{message_idx}_{nav_card['nav_key']}"):
            st.session_state[CHAT_NAV_CARDS_KEY][str(message_idx)]["dismissed"] = True
            _sync_historico_legado()
            st.toast("Navegação cancelada.")
            st.rerun()


def gerar_resposta_ia(
    user_prompt: str,
    *,
    df_ativo: pd.DataFrame,
    ind: pd.DataFrame,
    ranking: pd.DataFrame,
    n_cenarios: int,
    p_ruina: float,
    cena_sel: str,
    k: pd.Series,
    ano_enc: int,
    ano_sel: str | int = "Todos",
    persona: str = "cfo",
) -> str:
    """Chama o RAG/LLM com contexto financeiro da base ativa."""
    from .context import _carregar_engine, _chave_api, _contexto_foco, _fingerprint, contexto_dataset_ativo

    engine = _carregar_engine(ranking, _fingerprint(ranking))
    contexto = "\n\n".join(
        [
            contexto_dataset_ativo(
                df_ativo,
                ind,
                ranking,
                cena_sel=cena_sel,
                ano_sel=ano_sel,
                persona=persona,
                k=k,
            ),
            _contexto_foco(ranking, n_cenarios, p_ruina, cena_sel, k, ano_enc, ano_sel),
        ]
    )
    resposta, fontes = engine.ask(
        user_prompt,
        lang=get_lang(),
        history=st.session_state.messages[:-1],
        api_key=_chave_api(),
        extra_context=contexto,
        cena_sel=cena_sel,
    )
    _ = fontes
    return resposta


def _render_configuracoes() -> None:
    with st.expander("Configurações da API & Dados", expanded=False):
        st.text_input("Chave API Gemini", type="password", key="gemini_api_key_input")
        if st.button("Limpar Conversa"):
            _resetar_historico()
            st.rerun()


def _df_or_empty(df: pd.DataFrame | None) -> pd.DataFrame:
    if isinstance(df, pd.DataFrame):
        return df
    return pd.DataFrame(columns=["ANO", "CENA", "CONTA", "VALOR", "ano_num"])


def _ind_or_ranking(ind: pd.DataFrame | None, ranking: pd.DataFrame) -> pd.DataFrame:
    return ind if isinstance(ind, pd.DataFrame) else ranking.copy()


def _garantir_fechamento_conversacional(texto: str) -> str:
    if texto.strip().endswith("?"):
        return texto
    return (
        texto.rstrip()
        + "\n\nGostaria que eu direcionasse você para uma aba relacionada ou quer analisar outro indicador?"
    )


_CHAT_PANEL_CSS = """
<style>
div[class*="st-key-cti_chat_messages"],
div[class*="st-key-cti_chat_input_area"] {
  min-width: 0 !important;
  max-width: 100% !important;
  background: #0E1117 !important;
  background-color: #0E1117 !important;
  color: #F0F6FC !important;
  opacity: 1 !important;
}
div[class*="st-key-cti_chat_messages"] [data-testid="stChatMessage"],
div[data-testid="stChatMessage"] {
  background: #161B22 !important;
  background-color: #161B22 !important;
  border: 1px solid #30363D !important;
  border-radius: 10px !important;
  color: #F0F6FC !important;
  opacity: 1 !important;
  max-width: 100% !important;
  overflow-wrap: anywhere !important;
  word-break: normal !important;
}
div[data-testid="stChatMessage"] p,
div[data-testid="stChatMessage"] li,
div[data-testid="stChatMessage"] span {
  color: #F0F6FC !important;
  overflow-wrap: anywhere !important;
  word-break: normal !important;
}
div[class*="st-key-cti_chat_input_area"] {
  border-top: 1px solid #30363D !important;
  padding-top: 0.65rem !important;
}
div[class*="st-key-cti_chat_input_area"] input {
  background: #0B0F14 !important;
  color: #F0F6FC !important;
}
</style>
"""


_FLOATING_CHAT_CSS = """
<style>
div[class*="st-key-cti_chat_fab"] {
  position: fixed !important;
  right: 18px !important;
  bottom: 18px !important;
  z-index: 999999 !important;
  width: 64px !important;
}
div[class*="st-key-cti_chat_fab"] button {
  border-radius: 999px !important;
  min-height: 54px !important;
  width: 54px !important;
  padding: 0 !important;
  font-size: 1.3rem !important;
  box-shadow: 0 10px 28px rgba(0,0,0,.28) !important;
}
div[class*="st-key-cti_chat_panel"] {
  position: fixed !important;
  right: 18px !important;
  bottom: 84px !important;
  z-index: 999999 !important;
  width: min(420px, calc(100vw - 32px)) !important;
  max-height: min(720px, calc(100vh - 120px)) !important;
  overflow: auto !important;
  background: #0E1117 !important;
  background-color: #0E1117 !important;
  opacity: 1 !important;
  border: 1px solid #30363D !important;
  border-radius: 12px !important;
  padding: 16px !important;
  box-shadow: 0 18px 56px rgba(0,0,0,.72) !important;
  color: #F0F6FC !important;
}
div[class*="st-key-cti_chat_panel"] > div,
div[class*="st-key-cti_chat_panel"] [data-testid="stVerticalBlock"],
div[class*="st-key-cti_chat_panel"] [data-testid="stElementContainer"] {
  background: #0E1117 !important;
  background-color: #0E1117 !important;
  opacity: 1 !important;
}
div[class*="st-key-cti_chat_panel"] [data-testid="stChatMessage"] {
  font-size: .92rem !important;
  background: #161B22 !important;
  border: 1px solid #30363D !important;
  border-radius: 10px !important;
  padding: 8px !important;
}
div[class*="st-key-cti_chat_messages"] {
  max-height: min(440px, calc(100vh - 310px)) !important;
  overflow-y: auto !important;
  padding-right: 4px !important;
  margin-bottom: 10px !important;
  background: #0E1117 !important;
}
div[class*="st-key-cti_chat_input_area"] {
  position: sticky !important;
  bottom: 0 !important;
  z-index: 2 !important;
  background: #0E1117 !important;
  border-top: 1px solid #30363D !important;
  padding-top: 10px !important;
}
div[class*="st-key-cti_chat_input_area"] form {
  margin-bottom: 0 !important;
}
div[data-testid="stPopoverBody"], .floating-chat-container {
  background-color: #0E1117 !important;
  opacity: 1 !important;
  border: 1px solid #30363D !important;
  box-shadow: 0px 8px 24px rgba(0, 0, 0, 0.5) !important;
  z-index: 999999 !important;
}
@media (max-width: 640px) {
  div[class*="st-key-cti_chat_fab"] {
    right: 12px !important;
    bottom: 12px !important;
    width: 58px !important;
  }
  div[class*="st-key-cti_chat_fab"] button {
    min-height: 50px !important;
    width: 50px !important;
  }
  div[class*="st-key-cti_chat_panel"] {
    left: 8px !important;
    right: 8px !important;
    bottom: 72px !important;
    width: calc(100vw - 16px) !important;
    max-height: calc(100dvh - 88px) !important;
    padding: 12px !important;
    border-radius: 10px !important;
  }
  div[class*="st-key-cti_chat_panel"] h3 {
    font-size: 1.05rem !important;
    margin-bottom: 0.25rem !important;
  }
  div[class*="st-key-cti_chat_panel"] button {
    min-height: 2.4rem !important;
  }
  div[class*="st-key-cti_chat_messages"] {
    max-height: calc(100dvh - 260px) !important;
    padding-right: 2px !important;
  }
  div[class*="st-key-cti_chat_input_area"] {
    padding-top: 8px !important;
  }
  div[class*="st-key-cti_chat_input_area"] input {
    font-size: 16px !important;
  }
}
</style>
"""


def _abrir_chat() -> None:
    st.session_state.chat_open = True


def _fechar_chat() -> None:
    st.session_state.chat_open = False


def render_floating_chat(ctx: AppContext) -> None:
    """Renderiza o assistente em um painel flutuante acionado por botao."""
    st.session_state.setdefault("chat_open", False)
    st.markdown(_FLOATING_CHAT_CSS, unsafe_allow_html=True)

    if not st.session_state.chat_open:
        with st.container(key="cti_chat_fab"):
            st.button("🤖", key="cti_chat_open_btn", help="Abrir Assistente CTI", on_click=_abrir_chat)
        return

    with st.container(key="cti_chat_panel", border=False):
        col_title, col_close = st.columns([0.82, 0.18], vertical_alignment="center")
        with col_title:
            st.subheader("Assistente CTI")
        with col_close:
            st.button("×", key="cti_chat_close_btn", help="Fechar", on_click=_fechar_chat)
        render_chat_panel(
            ctx.ranking,
            ctx.n_cenarios,
            ctx.p_ruina,
            ctx.cena_sel,
            ctx.k,
            ctx.ano_enc,
            ctx.ano_sel,
            df_ativo=ctx.df,
            ind=ctx.ind,
            persona=ctx.persona,
            show_title=False,
        )


def render_chat_panel(
    ranking: pd.DataFrame,
    n_cenarios: int,
    p_ruina: float,
    cena_sel: str,
    k: pd.Series,
    ano_enc: int,
    ano_sel: str | int = "Todos",
    df_ativo: pd.DataFrame | None = None,
    ind: pd.DataFrame | None = None,
    *,
    persona: str = "cfo",
    show_title: bool = True,
) -> None:
    st.markdown(_CHAT_PANEL_CSS, unsafe_allow_html=True)
    if show_title:
        st.subheader("Assistente CTI")
    _render_configuracoes()
    _inicializar_historico()
    with st.container(key="cti_chat_messages", border=False):
        _render_mensagens()

    with st.container(key="cti_chat_input_area", border=False):
        user_prompt = _render_chat_input_panel()
    if not user_prompt:
        return

    st.session_state.messages.append({"role": "user", "content": user_prompt})

    nav_card = detectar_intencao_navegacao(user_prompt, exigir_gatilho=False)
    try:
        with st.spinner("Consultando cenários, DRE, BP, DFC e manuais..."):
            response_text = gerar_resposta_ia(
                user_prompt,
                df_ativo=_df_or_empty(df_ativo),
                ind=_ind_or_ranking(ind, ranking),
                ranking=ranking,
                n_cenarios=n_cenarios,
                p_ruina=p_ruina,
                cena_sel=cena_sel,
                k=k,
                ano_enc=ano_enc,
                ano_sel=ano_sel,
                persona=persona,
            )
    except Exception as exc:
        response_text = f"Não consegui responder agora: {exc}"
    if nav_card is None:
        nav_card = detectar_intencao_navegacao(response_text, exigir_gatilho=False)
    if nav_card:
        response_text = (
            f"{response_text}\n\n"
            f"Também encontrei uma seção relacionada: **{nav_card['target_tab_name']}**."
        )
    response_text = _garantir_fechamento_conversacional(response_text)

    assistant_message_idx = len(st.session_state.messages)
    assistant_message = {"role": "assistant", "content": response_text}
    if nav_card:
        st.session_state.setdefault(CHAT_NAV_CARDS_KEY, {})[str(assistant_message_idx)] = nav_card
    st.session_state.messages.append(assistant_message)
    _sync_historico_legado()
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
