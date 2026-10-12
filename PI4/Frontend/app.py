"""Orquestrador do dashboard CTI."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(line_buffering=True)
except Exception:
    pass

logging.basicConfig(
    level=logging.INFO,
    stream=sys.stdout,
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
    force=True,
)

import pandas as pd
import streamlit as st

PI4_ROOT = Path(__file__).resolve().parents[1]
if str(PI4_ROOT) not in sys.path:
    sys.path.insert(0, str(PI4_ROOT))

from Backend.diag import diag, log_ambiente, log_ia
from Backend.metrics import montar_indicadores
from src.controllers.auth import (
    flush_login_email_toast,
    is_authenticated,
    render_login,
    render_logout_button,
)
from src.config.i18n import t
from src.controllers.bootstrap import carregar_estado, montar_contexto
from src.controllers.data_input import has_custom_data, render_data_input
from src.controllers.modals import ensure_modal_state, is_relatorio_open
from src.controllers.navigation import render_pagina
from src.controllers.page_setup import configure_page
from src.controllers.sidebar import render_language_selector, render_persona, render_sidebar
from src.controllers.stability import preparar_troca_vista
from src.views.ai_assistant.panel import render_floating_chat

log_ia("app.py carregado — Streamlit e assistente de IA activos")


def montar_indicadores_customizados(df):
    """Evita recalcular indicadores de bases customizadas em todo rerun."""
    cache = st.session_state.setdefault("cti_custom_indicator_cache", {})
    signature = (
        st.session_state.get("cti_active_dataset_name"),
        bool(st.session_state.get("cti_default_dataset_modified")),
        id(df),
        len(df),
    )
    if cache.get("signature") != signature:
        cache["signature"] = signature
        cache["value"] = montar_indicadores(df)
    return cache["value"]


def main() -> None:
    log_ia(
        f"RERUN Streamlit main() chat_aberto={st.session_state.get('chat_ia_open')} "
        f"pending={bool(st.session_state.get('cti_chat_pending_prompt'))} "
        f"ws_ok={st.session_state.get('_cti_ws_ok')} "
        f"mensagens={len(st.session_state.get('messages') or [])}"
    )
    configure_page()
    if not st.session_state.get("_cti_ws_ok"):
        st.session_state["_cti_ws_ok"] = True
        log_ia("handshake websocket — primeiro rerun leve")
        st.info("A abrir o painel CTI...")
        st.rerun()
    diag("app", "Streamlit main() a arrancar")
    if not st.session_state.get("_cti_env_logged"):
        log_ambiente("app")
        st.session_state["_cti_env_logged"] = True
    ensure_modal_state()
    render_language_selector()
    if not is_authenticated():
        diag("app", "ecran de login — a API so sera chamada no clique Entrar")
        logging.info("[app] ecran de login — a API so sera chamada no clique Entrar")
        render_login()
        st.stop()
    flush_login_email_toast()
    render_logout_button()
    estado = carregar_estado()
    if estado is None:
        diag("app", "carregar_estado devolveu None — st.stop")
        st.stop()
    df, ind, ranking = estado
    diag("app", f"estado df={len(df):,} ind={len(ind):,} ranking={len(ranking):,} fonte=local")
    df = render_data_input(df)
    if has_custom_data():
        if df is None or df.empty or "CENA" not in df.columns:
            st.error(
                "A coluna CENA não foi encontrada no ficheiro enviado. "
                "No formato largo use ID_Cenario ou Nome_Cenario; no formato longo use CENA."
            )
        else:
            try:
                ind, ranking = montar_indicadores_customizados(df)
            except Exception as exc:  # noqa: BLE001
                st.error(
                    f"Não foi possível calcular os indicadores da base enviada: {type(exc).__name__}: {exc}. "
                    "A barra lateral permanece disponível para restaurar a base original."
                )
                if "CENA" not in getattr(ranking, "columns", []):
                    ranking = pd.DataFrame({"CENA": df["CENA"].dropna().unique()})
                if "CENA" not in getattr(ind, "columns", []):
                    ind = ranking.copy()

    n_cenarios = int(ranking["CENA"].nunique()) if "CENA" in getattr(ranking, "columns", []) else 0
    ano_sel, cena_sel, anos, cenas = render_sidebar(df, ind, n_cenarios)
    diag("app", f"filtros ano={ano_sel} cena={cena_sel} n_cenarios={n_cenarios} fonte=local")
    persona = render_persona()
    if preparar_troca_vista(persona, ano_sel, cena_sel):
        diag("app", f"troca leve persona={persona} ano={ano_sel} cena={cena_sel}")
        st.info(t("ui.loading_view", persona=t(f"persona.{persona}")))
        if not is_relatorio_open():
            render_floating_chat()
        st.rerun()
    diag("app", f"persona={persona} a montar contexto e pagina")
    try:
        ctx = montar_contexto(
            df, ind, ranking, ano_sel=ano_sel, cena_sel=cena_sel, anos=anos, cenas=cenas, persona=persona
        )
        render_pagina(ctx)
        st.session_state["cti_chat_ctx"] = {
            "n_cenarios": ctx.n_cenarios,
            "p_ruina": ctx.p_ruina,
            "cena_sel": ctx.cena_sel,
            "ano_sel": ctx.ano_sel,
            "ano_enc": ctx.ano_enc,
            "persona": ctx.persona,
            "k": ctx.k.to_dict() if hasattr(ctx.k, "to_dict") else {},
            "ranking": None,
        }
    except Exception as exc:  # noqa: BLE001
        diag("app", f"pagina FALHOU {type(exc).__name__}: {exc}")
        st.error(t("ui.render_error", label=t(f"persona.{persona}"), detail=f"{type(exc).__name__}: {exc}"))
    if not is_relatorio_open():
        render_floating_chat()


main()
