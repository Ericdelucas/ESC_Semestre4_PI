"""Isolamento RBAC do Assistente CTI: prompt, retrieval e guardrail."""

from __future__ import annotations

import re
import unicodedata
from typing import Any

ROLE_LABELS = {
    "ceo": "CEO",
    "cfo": "CFO",
    "acionistas": "Acionistas",
    "concedente": "Poder Concedente",
}

ALL_ROLES = frozenset(ROLE_LABELS)
CEO_CFO = frozenset({"ceo", "cfo"})
CEO_CFO_ACI = frozenset({"ceo", "cfo", "acionistas"})
CEO_CFO_CONC = frozenset({"ceo", "cfo", "concedente"})
REGULATORIO = frozenset({"ceo", "cfo", "concedente", "acionistas"})

_TERMOS_CEO_CFO = (
    "ebitda",
    "ebit",
    "lucro liquido",
    "lucro líquido",
    "margem ebitda",
    "margem ebit",
    "margem operacional",
    "margem liquida",
    "margem líquida",
    "margem",
    "dre",
    "demonstracao de resultado",
    "demonstração de resultado",
    "roic",
    "roe",
    "eva",
    "wacc",
    "nopat",
    "ltv",
    "cac",
    "ltv/cac",
    "break-even",
    "break even",
    "ponto de equilibrio",
    "ponto de equilíbrio",
)

_TERMOS_OPERACIONAIS_CFO = (
    "ncg",
    "capital de giro",
    "tesouraria",
    "pmr",
    "pmp",
    "pme",
    "ciclo financeiro",
    "opex",
)

_TERMOS_GUARDRAIL_CONCEDENTE = (
    "ebitda",
    "ebit",
    "lucro líquido",
    "lucro liquido",
    "margem ebitda",
    "margem ebit",
    "margem operacional",
    "margem líquida",
    "margem liquida",
    "roic",
    "roe",
    "eva",
    "ltv",
    "cac",
    "wacc",
    "nopat",
)


def normalize_role(role: str | None) -> str:
    alvo = str(role or "").strip().lower()
    if alvo in {"poder concedente", "concedente", "granting authority"}:
        return "concedente"
    if alvo in {"acionistas", "shareholders"}:
        return "acionistas"
    if alvo in ALL_ROLES:
        return alvo
    return "ceo"


def role_label(role: str | None, lang: str = "pt") -> str:
    codigo = normalize_role(role)
    if lang == "en":
        return {
            "ceo": "CEO",
            "cfo": "CFO",
            "acionistas": "Shareholders",
            "concedente": "Granting Authority",
        }[codigo]
    return ROLE_LABELS[codigo]


def _norm(texto: str) -> str:
    return unicodedata.normalize("NFKD", texto.lower()).encode("ascii", "ignore").decode("ascii")


def visibility_for_source(source: str) -> frozenset[str]:
    """Classifica a visibilidade do documento pela pasta/tag."""
    caminho = source.replace("\\", "/").lower()
    if "ceo_only" in caminho or "/dre/" in caminho or "03_demonstracao" in caminho:
        return CEO_CFO if "/dre/" in caminho else frozenset({"ceo"})
    if any(chave in caminho for chave in ("01_margens", "03_break_even", "09_ltv", "graficos/01_ceo")):
        return frozenset({"ceo"})
    if any(chave in caminho for chave in ("graficos/02_cfo", "04_ncg", "05_prazos", "08_ruina", "fluxo_caixa/", "02_monte_carlo")):
        return CEO_CFO
    if any(chave in caminho for chave in ("02_retorno", "graficos/03_acionistas")):
        return CEO_CFO_ACI
    if any(chave in caminho for chave in ("07_capex_bar", "graficos/04_concedente", "03_imobilizado_outorga_bar")):
        return CEO_CFO_CONC
    if "06_liquidez" in caminho:
        return REGULATORIO
    if "graficos/05_comparacao" in caminho or "manual_executivo" in caminho:
        return CEO_CFO
    if any(chave in caminho for chave in ("04_stakeholders", "00_indice", "/ia/", "01_objeto", "03_constantes")):
        return REGULATORIO
    if "/balanco/" in caminho:
        return CEO_CFO_CONC
    if "/cenarios/" in caminho:
        return CEO_CFO
    return CEO_CFO


def document_allowed(metadata: dict[str, Any] | None, role: str | None) -> bool:
    codigo = normalize_role(role)
    if codigo == "ceo":
        return True
    meta = metadata or {}
    vis = meta.get("visibility") or meta.get("user_roles")
    if vis:
        permitidos = {str(item).strip().lower() for item in vis}
        return codigo in permitidos
    origem = str(meta.get("source") or "")
    return codigo in visibility_for_source(origem)


def deny_message(role: str | None, lang: str = "pt") -> str:
    codigo = normalize_role(role)
    label = role_label(codigo, lang)
    if codigo == "concedente":
        if lang == "en":
            return (
                f"Restricted access. As {label}, you may only access regulatory indicators, "
                "the CAPEX schedule and the Reversible Asset Base (BAR)."
            )
        return (
            f"Acesso restrito. Como {label}, você possui acesso apenas a indicadores regulatórios, "
            "cronograma de CAPEX e Base de Ativos Reversíveis (BAR)."
        )
    if codigo == "acionistas":
        if lang == "en":
            return (
                f"Restricted access. As {label}, you may only access return indicators (ROIC, ROE, EVA), "
                "the risk-return matrix, dividends/JCP and solvency."
            )
        return (
            f"Acesso restrito. Como {label}, você possui acesso aos indicadores de retorno (ROIC, ROE, EVA), "
            "matriz risco x retorno, distribuição de dividendos/JCP e solvência."
        )
    if lang == "en":
        return f"Restricted access. This content is exclusive to CEO/Board governance and is not available to the {label} profile."
    return f"Acesso restrito. Este conteúdo é exclusivo da governança do CEO/Conselho e não está disponível para o perfil {label}."


def question_is_blocked(question: str, role: str | None) -> bool:
    codigo = normalize_role(role)
    if codigo == "ceo":
        return False
    texto = _norm(question)
    if codigo == "concedente":
        return any(termo in texto for termo in _TERMOS_CEO_CFO)
    if codigo == "acionistas":
        operacionais = (
            "ebitda",
            "dre",
            "ltv",
            "cac",
            "ncg",
            "tesouraria",
            "pmr",
            "pmp",
            "pme",
            "ciclo financeiro",
            "break-even",
            "break even",
            "margem ebitda",
            "decisao de governanca",
            "conselho",
        )
        return any(termo in texto for termo in operacionais)
    if codigo == "cfo":
        return any(termo in texto for termo in ("ltv", "cac", "conselho", "governanca do ceo", "decisao do ceo"))
    return False


def sanitize_answer(answer: str, role: str | None, lang: str = "pt") -> str:
    """Guardrail: se a resposta vazou termo bloqueado, substitui pela mensagem de acesso negado."""
    codigo = normalize_role(role)
    if codigo == "ceo" or not answer:
        return answer
    texto = _norm(answer)
    if codigo == "concedente":
        vazou = any(termo in texto for termo in ("ebitda", "lucro liquido", "margem ebit", "margem operacional", "margem liquida"))
        if "margem" in texto and any(p in texto for p in ("ebitda", "ebit", "operacional", "liquida", "%")):
            vazou = True
        if vazou:
            return deny_message(codigo, lang)
    if codigo == "acionistas" and any(termo in texto for termo in ("ebitda", "ltv", "cac", "ncg ")):
        return deny_message(codigo, lang)
    return answer


def rbac_system_prompt(role: str | None, lang: str = "pt") -> str:
    codigo = normalize_role(role)
    label = role_label(codigo, lang)
    if lang == "en":
        base = (
            f"You are the CTI Project Assistant. The current user is authenticated with the profile: {label}.\n"
            "You MUST strictly respect this profile. Never reveal metrics, documents or analyses "
            "outside the allowed knowledge matrix. If the user asks for blocked content, reply ONLY "
            f"with: {deny_message(codigo, lang)}"
        )
        if codigo == "concedente":
            base += (
                "\nALLOWED: regulation, oversight, CAPEX invested in infrastructure, Reversible Asset Base (BAR), "
                "general liquidity and long-term solvency.\n"
                "DENIED: EBITDA, EBIT, net income, operating margins, detailed DRE, shareholder returns "
                "(ROIC/ROE/EVA), commercial strategy (LTV/CAC) and confidential board views."
            )
        elif codigo == "acionistas":
            base += (
                "\nALLOWED: ROIC, ROE, EVA, risk-return matrix, dividends/JCP and solvency.\n"
                "DENIED: internal CEO/CFO operating detail that is not part of the shareholder view."
            )
        elif codigo == "cfo":
            base += (
                "\nALLOWED: operating DRE, NWC, treasury, average terms, Monte Carlo risk tail, "
                "Granting Authority and Shareholders views.\n"
                "DENIED: CEO/Board-only governance decisions."
            )
        else:
            base += "\nThe CEO profile has unrestricted access to every metric, report and knowledge item."
        return base
    base = (
        f"Você é o Assistente do Projeto CTI. O usuário atual está autenticado com o perfil: {label}.\n"
        "Você DEVE respeitar estritamente este perfil. Nunca revele métricas, documentos ou análises "
        "fora da matriz de conhecimento permitida. Se o usuário pedir conteúdo bloqueado, responda SOMENTE "
        f"com: {deny_message(codigo, lang)}"
    )
    if codigo == "concedente":
        base += (
            "\nPERMITIDO: regulação, fiscalização, CAPEX investido em infraestrutura, Base de Ativos "
            "Reversíveis (BAR) e liquidez geral/solvência de longo prazo.\n"
            "NEGAR E BLOQUEAR: EBITDA, EBIT, Lucro Líquido, margens operacionais, DRE detalhada, "
            "retorno de acionistas (ROIC/ROE/EVA), estratégias comerciais (LTV/CAC) e visões "
            "confidenciais da diretoria."
        )
    elif codigo == "acionistas":
        base += (
            "\nPERMITIDO: ROIC, ROE, EVA, matriz risco x retorno, dividendos/JCP e solvência.\n"
            "NEGAR E BLOQUEAR: detalhes operacionais internos restritos da gestão do CFO/CEO "
            "que não pertençam à visão de acionista."
        )
    elif codigo == "cfo":
        base += (
            "\nPERMITIDO: DRE operacional, NCG, saldo de tesouraria, prazos médios, cauda de risco/"
            "Monte Carlo, visão do Poder Concedente e Acionistas.\n"
            "NEGAR E BLOQUEAR: decisões de governança exclusivas do CEO/Conselho."
        )
    else:
        base += "\nO perfil CEO tem acesso TOTAL e irrestrito a todas as métricas, relatórios e conhecimentos da base."
    return base


def sanitize_context(contexto: str, role: str | None) -> str:
    codigo = normalize_role(role)
    if codigo in {"ceo", "cfo"} or not contexto:
        return contexto
    padrao = re.compile(
        r"ebitda|ebit\b|lucro l[ií]quido|margem ebit|margem operacional|ltv|cac|wacc|nopat|dre -",
        re.IGNORECASE,
    )
    if codigo == "acionistas":
        padrao = re.compile(r"ebitda|ltv|cac|ncg|tesouraria|dre -|break-even", re.IGNORECASE)
    if codigo == "concedente":
        padrao = re.compile(
            r"ebitda|ebit\b|lucro l[ií]quido|margem ebit|margem operacional|margem l[ií]quida|"
            r"roic|roe|eva|ltv|cac|wacc|nopat|dre -|ncg|tesouraria|break-even",
            re.IGNORECASE,
        )
    linhas = [linha for linha in contexto.splitlines() if not padrao.search(linha)]
    return "\n".join(linhas)


def nav_target_allowed(nav_card: dict[str, str] | None, role: str | None) -> dict[str, str] | None:
    if not nav_card:
        return None
    codigo = normalize_role(role)
    destino = str(nav_card.get("persona") or "")
    if codigo == "ceo":
        return nav_card
    if codigo == "concedente" and destino != "concedente":
        return None
    if codigo == "acionistas" and destino not in {"acionistas", "concedente"}:
        return None
    if codigo == "cfo" and destino == "ceo" and str(nav_card.get("nav_key") or "").startswith("ceo_ltv"):
        return None
    return nav_card
