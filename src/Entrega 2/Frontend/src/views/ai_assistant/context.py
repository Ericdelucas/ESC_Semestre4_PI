"""Contexto e cache do Assistente CTI."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from src.controllers.kpis import kpis_por_persona
from Backend.metrics.financial_kpis import build_financial_statement as _financeiro
from src.controllers.kpis.constants import (
    CONTA_CUSTOS,
    CONTA_EBITDA,
    CONTA_FLU_INVESTIMENTOS,
    CONTA_OUTROS_RESULTADOS,
    CONTA_RECEITA,
    CONTA_TRIBUTOS,
)
from src.controllers.kpis.helpers import _safe_div, _valor_conta_raw
from Backend.diag import log_ia
from src.config.i18n import get_lang, t, translate_dataset_name
from src.models.formatting import cena_rotulo, fmt_pct, fmt_rs, is_all_scenarios
from src.models.rag_engine import RagEngine, build_focus_context, resolve_api_key
from src.models.rag_engine.formatters import dias, pct, rs


def _fingerprint(ranking: pd.DataFrame) -> str:
    n = int(ranking.shape[0])
    caixa = ranking["caixa_ano12"] if "caixa_ano12" in ranking.columns else pd.Series(dtype=float)
    media = float(caixa.mean()) if not caixa.empty else 0.0
    return f"{n}:{media:.4f}"


@st.cache_resource(show_spinner=t("ai.indexing"))
def _carregar_engine(_ranking: pd.DataFrame, fingerprint: str) -> RagEngine:
    import time

    t0 = time.time()
    log_ia(f"carregar_engine: inicio fingerprint={fingerprint} ranking={len(_ranking)}")
    engine = RagEngine.from_ranking(_ranking)
    log_ia(
        f"carregar_engine: OK backend={engine.backend} docs={len(engine.documents)} "
        f"em {time.time() - t0:.2f}s"
    )
    return engine


def _chave_api() -> str | None:
    colada = str(st.session_state.get("gemini_api_key_input", "")).strip()
    if colada:
        st.session_state["google_api_key"] = colada
        log_ia(f"chave: a usar chave colada na UI len={len(colada)}")
        return colada
    antiga = str(st.session_state.get("google_api_key", "")).strip()
    if antiga:
        log_ia(f"chave: a usar chave da sessao len={len(antiga)}")
        return antiga
    try:
        for nome in ("GOOGLE_API_KEY", "GEMINI_API_KEY"):
            val = str(st.secrets.get(nome, "")).strip()
            if val:
                log_ia(f"chave: a usar secrets.{nome} len={len(val)}")
                return val
    except Exception as exc:  # noqa: BLE001
        log_ia(f"chave: secrets indisponiveis ({type(exc).__name__})")
    chave = resolve_api_key()
    log_ia(f"chave: ambiente {'presente' if chave else 'AUSENTE'} len={len(chave or '')}")
    return chave


def _contexto_foco(
    ranking: pd.DataFrame,
    n_cenarios: int,
    p_ruina: float,
    cena_sel: str,
    k: pd.Series,
    ano_enc: int,
    ano_sel: str | int,
) -> str:
    lang = get_lang()
    rent = fmt_pct(k["rentabilidade"]) if "rentabilidade" in k.index else "—"
    if lang == "en":
        intro = (
            f"Screen context: focus scenario {cena_rotulo(cena_sel)}; "
            f"{n_cenarios:,} scenarios in the dataset; probability of negative cash in Year {ano_enc}: {p_ruina:.1f}%; "
            f"slice profitability {rent}."
        )
    else:
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
        lang=lang,
    )
    return f"{intro}\n{detalhe}"


def _safe_mean(frame: pd.DataFrame, column: str) -> float:
    if frame.empty or column not in frame.columns:
        return float("nan")
    return float(pd.to_numeric(frame[column], errors="coerce").mean())


def _conta_total(df: pd.DataFrame, conta: str, cena_sel: str, ano_sel: str | int) -> float:
    if df.empty or not {"CENA", "CONTA", "VALOR"}.issubset(df.columns):
        return float("nan")
    base = df.loc[df["CONTA"] == conta].copy()
    if not is_all_scenarios(cena_sel):
        base = base.loc[base["CENA"] == cena_sel]
    if ano_sel != "Todos" and "ano_num" in base.columns:
        base = base.loc[pd.to_numeric(base["ano_num"], errors="coerce") == int(ano_sel)]
    if base.empty:
        return float("nan")
    serie = pd.to_numeric(base["VALOR"], errors="coerce")
    return float(serie.mean() if is_all_scenarios(cena_sel) else serie.sum())


def _peca_resumo(df: pd.DataFrame, prefixo: str, cena_sel: str, ano_sel: str | int, limite: int = 8) -> str:
    if df.empty or not {"CENA", "CONTA", "VALOR"}.issubset(df.columns):
        return "- Sem linhas disponiveis."
    contas = [conta for conta in df["CONTA"].dropna().unique() if str(conta).startswith(prefixo)]
    if not contas:
        return "- Sem linhas para o recorte atual."
    base = df.loc[df["CONTA"].isin(contas)]
    if not is_all_scenarios(cena_sel):
        base = base.loc[base["CENA"] == cena_sel]
    if ano_sel != "Todos" and "ano_num" in base.columns:
        base = base.loc[pd.to_numeric(base["ano_num"], errors="coerce") == int(ano_sel)]
    if base.empty:
        return "- Sem linhas para o recorte atual."
    base = base.assign(VALOR=pd.to_numeric(base["VALOR"], errors="coerce").fillna(0))
    agrupado = base.groupby("CONTA", as_index=False)["VALOR"]
    resumo = agrupado.mean() if is_all_scenarios(cena_sel) else agrupado.sum()
    resumo["abs_valor"] = resumo["VALOR"].abs()
    resumo = resumo.sort_values("abs_valor", ascending=False).head(limite)
    return "\n".join(f"- {row.CONTA}: {rs(float(row.VALOR))}" for row in resumo.itertuples(index=False))


def _contexto_dre_legacy(df: pd.DataFrame, cena_sel: str, ano_sel: str | int) -> str:
    dre = _dre(df, cena_sel)
    if ano_sel != "Todos" and not dre.empty:
        dre = dre.loc[pd.to_numeric(dre["ano_num"], errors="coerce") == int(ano_sel)]
    be = _break_even_df(df, cena_sel)
    if ano_sel != "Todos" and not be.empty:
        be = be.loc[pd.to_numeric(be["ano_num"], errors="coerce") == int(ano_sel)]
    receita = _safe_mean(dre, "Receita Líquida")
    ebitda = _safe_mean(dre, "EBITDA")
    lucro = _safe_mean(dre, "Lucro Líquido")
    margem_ebitda = ebitda / receita if receita else float("nan")
    margem_liquida = lucro / receita if receita else float("nan")
    break_even = _safe_mean(be, "Break-Even")
    margem_seg = _safe_mean(be, "Margem de Segurança (%)")
    margem_contrib = _safe_mean(be, "Margem de Contribuição (%)")
    return "\n".join(
        [
            "DRE e rentabilidade do recorte:",
            f"- Receita Liquida media: {rs(receita)}",
            f"- EBITDA medio: {rs(ebitda)}",
            f"- Margem EBITDA media: {pct(margem_ebitda)}",
            f"- Lucro Liquido medio: {rs(lucro)}",
            f"- Margem liquida media: {pct(margem_liquida)}",
            f"- Ponto de equilibrio medio: {rs(break_even)}",
            f"- Margem de contribuicao media: {pct(margem_contrib)}",
            f"- Margem de seguranca media: {pct(margem_seg)}",
        ]
    )


def _contexto_dre(df: pd.DataFrame, cena_sel: str, ano_sel: str | int) -> str:
    receita = _valor_conta_raw(df, cena_sel, CONTA_RECEITA, ano_sel)
    ebitda = _valor_conta_raw(df, cena_sel, CONTA_EBITDA, ano_sel)
    tributos = _valor_conta_raw(df, cena_sel, CONTA_TRIBUTOS, ano_sel)
    custos = _valor_conta_raw(df, cena_sel, CONTA_CUSTOS, ano_sel)
    outros = _valor_conta_raw(df, cena_sel, CONTA_OUTROS_RESULTADOS, ano_sel)
    margem_ebitda = _safe_div(ebitda, receita)
    margem_contribuicao_rs = (receita - abs(tributos)) - abs(custos)
    margem_contribuicao_pct = _safe_div(margem_contribuicao_rs, receita)
    break_even = _safe_div(abs(outros), margem_contribuicao_pct)
    return "\n".join(
        [
            "DRE e rentabilidade do recorte calculados com os mesmos helpers dos cartoes CEO:",
            f"- Receita do cartao: {fmt_rs(receita)}",
            f"- EBITDA Operacional do cartao: {fmt_rs(ebitda)}",
            f"- Margem EBITDA do cartao: {margem_ebitda * 100:.1f}%" if pd.notna(margem_ebitda) else "- Margem EBITDA do cartao: —",
            f"- Ponto de Equilibrio (Break-Even) do cartao: {fmt_rs(break_even)}",
            f"- Margem de contribuicao usada no Break-Even: {margem_contribuicao_pct * 100:.1f}%" if pd.notna(margem_contribuicao_pct) else "- Margem de contribuicao usada no Break-Even: —",
        ]
    )


def _contexto_cartoes_visuais(
    persona: str,
    k: pd.Series,
    ranking: pd.DataFrame,
    df: pd.DataFrame,
    cena_sel: str,
    ano_sel: str | int,
) -> str:
    itens = kpis_por_persona(persona, k, ranking, df, cena_sel, ano_sel)
    linhas = [
        "Cartoes visuais do topo no estado atual da tela. Estes valores tem prioridade absoluta nas respostas:",
    ]
    for item in itens:
        titulo = item[0]
        valor = item[1]
        detalhe = item[2] if len(item) > 2 else None
        sufixo = f" ({detalhe})" if detalhe else ""
        linhas.append(f"- {titulo}: {valor}{sufixo}")
    return "\n".join(linhas)


def _contexto_acionistas(df: pd.DataFrame, cena_sel: str, ano_sel: str | int) -> str:
    dados = _financeiro(df, cena_sel)
    if dados.empty:
        return "Acionistas e retorno: sem dados financeiros suficientes para ROIC/EVA no recorte atual."
    if ano_sel != "Todos" and "ano_num" in dados.columns:
        dados = dados.loc[pd.to_numeric(dados["ano_num"], errors="coerce") == int(ano_sel)]
    roic = _safe_mean(dados, "ROIC")
    roe = _safe_mean(dados, "ROE")
    wacc = _safe_mean(dados, "WACC")
    eva = _safe_mean(dados, "EVA")
    dividendos = _safe_mean(dados, "Dividendos")
    return "\n".join(
        [
            "Acionistas e retorno do recorte. Use estes dados quando a pergunta envolver ROIC, ROE, WACC, EVA, dividendos ou capital investido:",
            f"- ROIC medio: {fmt_pct(roic)}",
            f"- ROE medio: {fmt_pct(roe)}",
            f"- WACC medio: {fmt_pct(wacc)}",
            f"- EVA medio: {fmt_rs(eva)}",
            f"- Dividendos medios: {fmt_rs(dividendos)}",
            "- Aba recomendada para ROIC: Acionistas > Retorno & ROIC.",
        ]
    )


def _contexto_concedente(df: pd.DataFrame, cena_sel: str, ano_sel: str | int) -> str:
    capex = abs(_valor_conta_raw(df, cena_sel, CONTA_FLU_INVESTIMENTOS, ano_sel))
    return "\n".join(
        [
            "Poder Concedente e investimentos do recorte. Use estes dados quando a pergunta envolver CAPEX, investimentos, infraestrutura, solvencia ou ativos reversiveis:",
            f"- CAPEX / investimentos do recorte: {fmt_rs(capex)}",
            "- Conta usada para CAPEX no dashboard: FLU - Investimentos.",
            "- Aba recomendada para CAPEX: Poder Concedente > Plano de CAPEX.",
        ]
    )


def contexto_dataset_ativo(
    df: pd.DataFrame,
    ind: pd.DataFrame,
    ranking: pd.DataFrame,
    *,
    cena_sel: str,
    ano_sel: str | int,
    persona: str = "cfo",
    k: pd.Series | None = None,
    user_role: str | None = None,
) -> str:
    """Resume a base ativa para o motor analitico nativo do Dashboard CTI."""
    import time

    from src.models.rag_engine.rbac import normalize_role

    t0 = time.time()
    log_ia(
        f"contexto: inicio df={len(df)} ind={len(ind)} ranking={len(ranking)} "
        f"cena={cena_sel} ano={ano_sel} persona={persona}"
    )
    papel = normalize_role(user_role or persona)
    modo_leve = len(df) > 20_000
    if modo_leve:
        log_ia(f"contexto: MODO LEVE — df tem {len(df):,} linhas; sem varrer a base longa (evita 429)")
    lang = get_lang()
    en = lang == "en"
    nome_base = translate_dataset_name(st.session_state.get("cti_active_dataset_name", "Base Padrão (Original)"), lang)
    anos_src = ind if isinstance(ind, pd.DataFrame) and "ano_num" in ind.columns else df
    anos = sorted(pd.to_numeric(anos_src.get("ano_num", pd.Series(dtype=float)), errors="coerce").dropna().astype(int).unique())
    if "CENA" in ranking.columns:
        n_cenas = int(ranking["CENA"].nunique())
    elif isinstance(ind, pd.DataFrame) and "CENA" in ind.columns:
        n_cenas = int(ind["CENA"].nunique())
    else:
        n_cenas = int(df["CENA"].nunique()) if "CENA" in df.columns else 0
    if "CENA" not in ind.columns:
        foco = pd.DataFrame()
    elif is_all_scenarios(cena_sel):
        foco = ind.copy()
    else:
        foco = ind.loc[ind["CENA"] == cena_sel].copy()
    if ano_sel != "Todos" and not foco.empty:
        foco = foco.loc[pd.to_numeric(foco["ano_num"], errors="coerce") == int(ano_sel)]
    if is_all_scenarios(cena_sel) or "CENA" not in ranking.columns or ranking.empty:
        rank_foco = ranking.mean(numeric_only=True) if isinstance(ranking, pd.DataFrame) and not ranking.empty else pd.Series(dtype=object)
    else:
        match = ranking.loc[ranking["CENA"] == cena_sel]
        rank_foco = match.iloc[0] if not match.empty else pd.Series(dtype=object)

    year_label = f"Year {ano_sel}" if en and ano_sel != "Todos" else (t("filter.all") if str(ano_sel) in {"Todos", "All", "__all__"} else f"Ano {ano_sel}")
    linhas = (
        [
            "Native analytical engine for the CTI Dashboard - answer strictly from these locally recalculated active-dataset values.",
            f"Active dataset: {nome_base}. Rows: {len(df):,}. Scenarios: {n_cenas:,}. Years: {anos[0] if anos else 'n/a'} to {anos[-1] if anos else 'n/a'}.",
            f"Current screen slice: scenario {cena_rotulo(cena_sel)} ({cena_sel}); selected year: {year_label}.",
            f"Active dashboard persona/view: {persona}.",
            f"Authenticated profile (RBAC): {papel}.",
            "When diagnosing metrics, cite the values below directly when available.",
            "",
        ]
        if en
        else [
            "Motor analitico nativo do Dashboard CTI - responda estritamente com estes dados locais recalculados da base ativa.",
            f"Base ativa: {nome_base}. Linhas: {len(df):,}. Cenarios: {n_cenas:,}. Anos: {anos[0] if anos else 'n/d'} a {anos[-1] if anos else 'n/d'}.",
            f"Recorte atual da tela: cenario {cena_rotulo(cena_sel)} ({cena_sel}); ano selecionado: {year_label}.",
            f"Persona/visao ativa do painel: {persona}.",
            f"Perfil autenticado (RBAC): {papel}.",
            "Ao diagnosticar metricas, cite diretamente os valores abaixo quando estiverem disponiveis.",
            "",
        ]
    )
    try:
        if modo_leve:
            k_vis = k if isinstance(k, pd.Series) else pd.Series(dtype=float)
            linhas.append("Visual cards (light mode, without rescanning the long dataset):" if en else "Cartoes visuais (modo leve, sem recalcular na base longa):")
            for nome, valor in k_vis.items():
                linhas.append(f"- {nome}: {valor}")
        else:
            linhas.append(
                _contexto_cartoes_visuais(
                    persona,
                    k if isinstance(k, pd.Series) else pd.Series(dtype=float),
                    ranking,
                    df,
                    cena_sel,
                    ano_sel,
                )
            )
    except Exception as exc:  # noqa: BLE001
        log_ia(f"contexto: cartoes FALHOU {type(exc).__name__}: {exc}")
        linhas.append(f"Visual cards unavailable ({type(exc).__name__})." if en else f"Cartoes visuais indisponiveis ({type(exc).__name__}).")
    if papel in {"ceo", "cfo", "acionistas"} and not modo_leve:
        try:
            linhas.extend(["", _contexto_acionistas(df, cena_sel, ano_sel)])
        except Exception as exc:  # noqa: BLE001
            log_ia(f"contexto: acionistas FALHOU {type(exc).__name__}: {exc}")
            linhas.append(f"Retorno de acionistas indisponivel ({type(exc).__name__}).")
    if papel in {"ceo", "cfo", "concedente"} and not modo_leve:
        linhas.extend(["", _contexto_concedente(df, cena_sel, ano_sel)])
    if papel in {"ceo", "cfo"}:
        extra_dre = [] if modo_leve else ["", _contexto_dre(df, cena_sel, ano_sel)]
        linhas.extend(
            extra_dre
            + (
                [
                    "",
                    "Working capital, liquidity and risk for the slice:",
                    f"- Average NWC: {rs(_safe_mean(foco, 'NCG'))}",
                    f"- Average Treasury Balance: {rs(_safe_mean(foco, 'Saldo_Tesouraria'))}",
                    f"- Average Cash Conversion Cycle: {dias(_safe_mean(foco, 'Ciclo_Financeiro'))}",
                    f"- Average current liquidity: {_safe_mean(foco, 'liquidez'):.2f}x",
                    f"- Average liability/asset risk: {pct(_safe_mean(foco, 'risco'))}",
                ]
                if en
                else [
                    "",
                    "Capital de giro, liquidez e risco do recorte:",
                    f"- NCG media: {rs(_safe_mean(foco, 'NCG'))}",
                    f"- Saldo de Tesouraria medio: {rs(_safe_mean(foco, 'Saldo_Tesouraria'))}",
                    f"- Ciclo Financeiro medio: {dias(_safe_mean(foco, 'Ciclo_Financeiro'))}",
                    f"- Liquidez corrente media: {_safe_mean(foco, 'liquidez'):.2f}x",
                    f"- Risco medio Passivo/Ativo: {pct(_safe_mean(foco, 'risco'))}",
                ]
            )
        )
    else:
        linhas.extend(
            [
                "",
                "Regulatory/solvency reading for the slice:" if en else "Leitura regulatória/solvência do recorte:",
                f"- Average current liquidity: {_safe_mean(foco, 'liquidez'):.2f}x" if en else f"- Liquidez corrente media: {_safe_mean(foco, 'liquidez'):.2f}x",
                f"- Average investments: {rs(_safe_mean(foco, 'investimentos'))}" if en else f"- Investimentos medios: {rs(_safe_mean(foco, 'investimentos'))}",
            ]
        )
    linhas.extend(
        [
            f"- Scenario badge: {rank_foco.get('selo', 'n/a')}" if en else f"- Selo do cenario: {rank_foco.get('selo', 'n/d')}",
            f"- Cash in the closing year: {rs(float(rank_foco.get('caixa_ano12', float('nan')))) if len(rank_foco) else 'n/a'}" if en else f"- Caixa no ano de encerramento: {rs(float(rank_foco.get('caixa_ano12', float('nan')))) if len(rank_foco) else 'n/d'}",
        ]
    )
    if papel in {"ceo", "cfo"}:
        pecas = [] if modo_leve else [
            f"- Saldo final medio: {rs(_conta_total(df, 'FLU - Saldo Final', cena_sel, ano_sel))}",
            "Principais contas DFC no recorte:",
            _peca_resumo(df, "FLU -", cena_sel, ano_sel),
            "",
            "Principais contas BP no recorte:",
            _peca_resumo(df, "BAL -", cena_sel, ano_sel),
            "",
            "Principais contas DRE no recorte:",
            _peca_resumo(df, "DRE -", cena_sel, ano_sel),
        ]
        linhas.extend(
            (
                [
                    "",
                    "Cash flow and cash:",
                    f"- Average cash generation: {rs(_safe_mean(foco, 'geracao_caixa'))}",
                    f"- Average investments: {rs(_safe_mean(foco, 'investimentos'))}",
                    *pecas,
                    "",
                    "CTI business formulas:",
                    "- NWC = Operating Assets - Operating Liabilities.",
                    "- Treasury Balance = Cash Available - Short-Term Loans.",
                    "- Cash Conversion Cycle = DSO + DIO - DPO.",
                    "- EBITDA Margin = EBITDA / Net Revenue.",
                    "- ROIC = NOPAT / Invested Capital.",
                    "- EVA = NOPAT - (Invested Capital x WACC).",
                    "- CAPEX = CF - Investments.",
                    "- Break-Even = Fixed Costs / Contribution Margin.",
                ]
                if en
                else [
                    "",
                    "DFC e caixa:",
                    f"- Geracao de Caixa media: {rs(_safe_mean(foco, 'geracao_caixa'))}",
                    f"- Investimentos medios: {rs(_safe_mean(foco, 'investimentos'))}",
                    *pecas,
                    "",
                    "Formulas de negocio CTI:",
                    "- NCG = ACO - PCO.",
                    "- Saldo de Tesouraria = Disponivel - Emprestimos CP.",
                    "- Ciclo Financeiro = PMR + PME - PMP.",
                    "- Margem EBITDA = EBITDA / Receita Liquida.",
                    "- ROIC = NOPAT / Capital Investido.",
                    "- EVA = NOPAT - (Capital Investido x WACC).",
                    "- CAPEX = FLU - Investimentos.",
                    "- Break-Even = Custos Fixos / Margem de Contribuicao.",
                ]
            )
        )
    elif papel == "concedente":
        pecas_reg = [] if modo_leve else [
            _peca_resumo(df, "FLU - Investimentos", cena_sel, ano_sel),
            _peca_resumo(df, "BAL -", cena_sel, ano_sel),
        ]
        linhas.extend(
            (
                [
                    "",
                    "Regulatory accounts for the slice:",
                    *pecas_reg,
                    "",
                    "Allowed formulas:",
                    "- CAPEX = CF - Investments.",
                    "- General Liquidity = Total Assets / (Current Liabilities + Long-Term Liabilities).",
                    "- RAB = net reversible asset base of the concession.",
                ]
                if en
                else [
                    "",
                    "Contas regulatórias do recorte:",
                    *pecas_reg,
                    "",
                    "Formulas permitidas:",
                    "- CAPEX = FLU - Investimentos.",
                    "- Liquidez Geral = Ativo total / (Passivo circulante + exigível LP).",
                    "- BAR = base líquida de ativos reversíveis da concessão.",
                ]
            )
        )
    elif papel == "acionistas":
        linhas.extend(
            (
                [
                    "",
                    "Allowed formulas:",
                    "- ROIC = NOPAT / Invested Capital.",
                    "- EVA = NOPAT - (Invested Capital x WACC).",
                    "- DY = Dividends / Invested Capital.",
                ]
                if en
                else [
                    "",
                    "Formulas permitidas:",
                    "- ROIC = NOPAT / Capital Investido.",
                    "- EVA = NOPAT - (Capital Investido x WACC).",
                    "- DY = Dividendos / Capital Investido.",
                ]
            )
        )
    texto = "\n".join(linhas)
    log_ia(f"contexto: pronto chars={len(texto)} modo_leve={modo_leve} em {time.time() - t0:.2f}s")
    return texto
