"""Classe principal do motor RAG e retrieval."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from typing import Any

import numpy as np
import pandas as pd
from langchain_core.documents import Document

try:
    import faiss
except ImportError:
    faiss = None

from .answers import gerar_llm, resolve_api_key
from .documents import docs_cenarios, docs_glossario, docs_manuais, status_documentos
from .embeddings import TfidfEmbeddings
from .rbac import (
    deny_message,
    document_allowed,
    question_is_blocked,
    sanitize_answer,
    sanitize_context,
)


def faiss_index(vectors: np.ndarray) -> Any:
    if faiss is None:
        raise RuntimeError("faiss-cpu não instalado")
    index = faiss.IndexFlatIP(int(vectors.shape[1]))
    index.add(vectors)
    return index


def prioridade_fonte(doc: Document, score: float) -> float:
    """Manual executivo e indicadores do CSV sobem na busca."""
    tipo = str(doc.metadata.get("tipo", ""))
    origem = str(doc.metadata.get("source", "")).lower()
    bonus = 0.0
    if tipo == "base_conhecimento":
        bonus += 0.60
    elif tipo == "manual_executivo" or "manual_executivo" in origem:
        bonus += 0.45
    elif tipo == "resumo":
        bonus += 0.35
    elif tipo == "selo":
        bonus += 0.25
    elif tipo == "cenario":
        bonus += 0.12
    return score + bonus


def _normalizar_texto(texto: str) -> str:
    return unicodedata.normalize("NFKD", texto.lower()).encode("ascii", "ignore").decode("ascii")


def _valores_recorte(contexto: str, chaves: tuple[str, ...]) -> str:
    linhas: list[str] = []
    for linha in contexto.splitlines():
        limpo = linha.strip()
        if not limpo.startswith("- "):
            continue
        if not chaves or any(chave.lower() in limpo.lower() for chave in chaves):
            linhas.append(limpo.removeprefix("- ").rstrip("."))
        if len(linhas) >= 4:
            break
    if not linhas:
        return ""
    if len(linhas) == 1:
        return linhas[0]
    return ", ".join(linhas[:-1]) + f" e {linhas[-1]}"


def _trechos_rag(contexto: str, termos: tuple[str, ...]) -> list[str]:
    blocos: list[str] = []
    atual: list[str] = []
    for linha in contexto.splitlines():
        if linha.startswith("Fonte:"):
            if atual:
                blocos.append(" ".join(atual).strip())
                atual = []
            continue
        if linha.startswith("Arquivos documentais") or linha.startswith("Aviso RAG"):
            continue
        if linha.strip().startswith("- "):
            continue
        if linha.strip():
            atual.append(linha.strip())
    if atual:
        blocos.append(" ".join(atual).strip())
    relevantes = []
    for bloco in blocos:
        baixo = _normalizar_texto(bloco)
        if termos and not any(termo in baixo for termo in termos):
            continue
        if len(bloco) < 40:
            continue
        relevantes.append(bloco)
        if len(relevantes) >= 3:
            break
    if relevantes:
        return relevantes
    if termos:
        return []
    return [bloco for bloco in blocos if len(bloco) >= 80][:2]


_GUIAS_METRICAS: dict[str, dict[str, object]] = {
    "ebitda": {
        "aliases": ("ebitda",),
        "termos": ("ebitda", "margem ebitda", "receita liquida"),
        "chaves": ("EBITDA", "Margem EBITDA", "Receita Liquida", "Receita"),
        "pt": (
            "EBITDA é o resultado operacional antes de juros, impostos, depreciação e amortização. "
            "Ele mostra a geração operacional de resultado da concessão sem misturar efeitos financeiros e não caixa.",
            "No CTI, o EBITDA vem da DRE. A margem EBITDA é EBITDA / Receita Líquida.",
            "Na concessão, um EBITDA forte indica capacidade de absorver OPEX, CAPEX e serviço da dívida. "
            "Se a receita cresce e o EBITDA não acompanha, há pressão de custos ou perda de margem.",
            "Os gráficos associados estão em CEO > Visão Geral & DRE (cascata média e Receita Líquida vs EBITDA) "
            "e em CEO > DRE Operacional (composição e margens). Na cascata, leia a passagem de receita para EBITDA; "
            "no gráfico temporal, compare se as duas linhas caminham juntas.",
            "Gostaria que eu abrisse CEO / Visão Geral & DRE para você ver esses gráficos no recorte atual?",
        ),
        "en": (
            "EBITDA is operating result before interest, taxes, depreciation and amortization. "
            "It shows the concession's operating generation without mixing financing or non-cash effects.",
            "In CTI, EBITDA comes from the income statement. EBITDA margin is EBITDA / Net Revenue.",
            "A strong EBITDA means the concession can absorb OPEX, CAPEX and debt service. "
            "If revenue rises but EBITDA does not follow, costs or margins are under pressure.",
            "Related charts sit in CEO > Overview & DRE (waterfall and Net Revenue vs EBITDA) and CEO > Operating DRE. "
            "In the waterfall, follow the path from revenue to EBITDA; in the time series, check whether both lines move together.",
            "Would you like me to open CEO / Overview & DRE so you can see these charts in the current slice?",
        ),
    },
    "roic": {
        "aliases": ("roic",),
        "termos": ("roic", "nopat", "capital investido", "wacc", "eva"),
        "chaves": ("ROIC", "Capital Investido", "NOPAT", "WACC", "EVA"),
        "pt": (
            "ROIC significa Retorno sobre o Capital Investido. Ele mede quanto resultado operacional "
            "depois de impostos a concessão gera para cada unidade de capital investido no negócio.",
            "A fórmula no CTI é ROIC = NOPAT / Capital Investido. NOPAT é o resultado operacional após "
            "impostos operacionais. O capital investido pode ser aproximado por Patrimônio Líquido + Dívida Líquida, "
            "ou pela base de ativos quando a estrutura exigir.",
            "Na prática, ROIC acima do WACC indica criação de valor econômico; abaixo do WACC, o projeto tende a destruir valor. "
            "É o indicador-chave para acionistas avaliarem se o capital da concessão está sendo bem remunerado.",
            "A visualização fica em Acionistas > Retorno & ROIC, no gráfico ROIC vs ROE vs WACC. "
            "Leia se a linha de ROIC permanece acima do WACC e compare com o ROE, que mede o retorno do capital próprio.",
            "Se quiser, posso abrir Acionistas / Retorno & ROIC para você comparar ROIC, ROE e WACC no recorte atual.",
        ),
        "en": (
            "ROIC is Return on Invested Capital. It measures how much after-tax operating result the concession "
            "generates for each unit of capital invested in the business.",
            "In CTI, ROIC = NOPAT / Invested Capital. NOPAT is operating result after operating taxes. "
            "Invested capital can be approximated as Equity + Net Debt, or by the asset base when needed.",
            "ROIC above WACC signals economic value creation; below WACC, the project tends to destroy value. "
            "It is the key shareholder metric for whether concession capital is being well rewarded.",
            "The chart is in Shareholders > Return & ROIC: ROIC vs ROE vs WACC. "
            "Check whether ROIC stays above WACC and compare it with ROE, which measures return on equity.",
            "Would you like me to open Shareholders / Return & ROIC so you can compare ROIC, ROE and WACC in the current slice?",
        ),
    },
    "capex": {
        "aliases": ("capex", "investimento", "investimentos"),
        "termos": ("capex", "investimentos", "infraestrutura", "flu - investimentos"),
        "chaves": ("CAPEX", "Investimentos", "CAPEX Acumulado", "Infraestrutura"),
        "pt": (
            "CAPEX significa Capital Expenditure: investimentos em bens de capital e infraestrutura da concessão.",
            "No CTI, o CAPEX é o valor absoluto da conta FLU - Investimentos. O CAPEX acumulado é a soma "
            "progressiva desses investimentos ao longo do horizonte de 12 anos.",
            "Para o Poder Concedente, o CAPEX mostra se o plano de infraestrutura está sendo cumprido. "
            "CAPEX intenso pressiona caixa e tesouraria, mesmo quando a operação é rentável.",
            "O gráfico está em Poder Concedente > Plano de CAPEX: barras mostram o investimento anual e a linha "
            "mostra o acumulado. Barras altas indicam pressão pontual; a linha crescente mostra o cumprimento do plano.",
            "Se quiser, posso abrir Poder Concedente / Plano de CAPEX para você ver o investimento anual e acumulado.",
        ),
        "en": (
            "CAPEX is Capital Expenditure: investment in capital goods and concession infrastructure.",
            "In CTI, CAPEX is the absolute value of FLU - Investimentos. Accumulated CAPEX is the running sum "
            "of those investments over the 12-year horizon.",
            "For the Granting Authority, CAPEX shows whether the infrastructure plan is being fulfilled. "
            "Heavy CAPEX pressures cash and treasury even when operations remain profitable.",
            "The chart is in Granting Authority > CAPEX Plan: bars show annual investment and the line shows the cumulative path. "
            "High bars mean a one-year squeeze; a rising line shows plan fulfillment.",
            "Would you like me to open Granting Authority / CAPEX Plan so you can see annual and accumulated investment?",
        ),
    },
    "ncg": {
        "aliases": ("ncg",),
        "termos": ("ncg", "capital de giro", "tesouraria"),
        "chaves": ("NCG",),
        "pt": (
            "NCG é a Necessidade de Capital de Giro: o recurso que a operação prende ou libera entre receber e pagar.",
            "A fórmula no CTI é NCG = ACO − PCO, em que ACO são os ativos circulantes operacionais e PCO os passivos circulantes operacionais.",
            "NCG positiva elevada pressiona caixa; NCG menor melhora a liquidez operacional da concessão.",
            "A leitura fica em CFO > Capital de Giro, no gráfico NCG × Tesouraria e na composição da NCG. "
            "NCG alta com tesouraria baixa indica pressão de financiamento operacional.",
            "Gostaria que eu abrisse CFO / Capital de Giro para cruzar NCG e tesouraria no recorte atual?",
        ),
        "en": (
            "NWC/NCG is the working-capital need: cash tied up or released between collections and payments.",
            "In CTI, NCG = operating current assets − operating current liabilities.",
            "A large positive NCG consumes cash; a smaller NCG improves operating liquidity.",
            "The view is CFO > Working Capital, with NCG vs Treasury and NCG composition. "
            "High NCG with weak treasury means operating funding pressure.",
            "Would you like me to open CFO / Working Capital to compare NCG and treasury in the current slice?",
        ),
    },
    "liquidez": {
        "aliases": ("liquidez", "solvencia", "solvência"),
        "termos": ("liquidez", "solvencia", "ativo circulante", "passivo circulante"),
        "chaves": ("Liquidez corrente", "Liquidez Geral"),
        "pt": (
            "Liquidez mede a capacidade de honrar obrigações. A liquidez corrente olha o curto prazo; "
            "a liquidez geral inclui ativos e passivos de longo prazo e avalia solvência da concessão.",
            "Liquidez corrente = Ativo Circulante / Passivo Circulante. "
            "Liquidez geral = (Ativo Circulante + Realizável a Longo Prazo) / (Passivo Circulante + Exigível a Longo Prazo).",
            "Valor abaixo de 1,0x sinaliza aperto. Para o Poder Concedente, a liquidez geral indica se a "
            "concessão consegue cumprir obrigações contratuais ao longo do horizonte.",
            "Liquidez corrente aparece em CFO > Faixa de Risco. Solvência de longo prazo fica em "
            "Poder Concedente > Solvência & Liquidez Geral, com linha de referência mínima.",
            "Quer que eu abra a aba de liquidez correspondente ao recorte que você está analisando?",
        ),
        "en": (
            "Liquidity measures the ability to meet obligations. Current liquidity is short-term; "
            "general liquidity includes long-term items and assesses concession solvency.",
            "Current liquidity = current assets / current liabilities. "
            "General liquidity = (current assets + long-term receivables) / (current liabilities + long-term payables).",
            "A reading below 1.0x signals tightness. For the Granting Authority, general liquidity shows "
            "whether contractual obligations can be met over the horizon.",
            "Current liquidity is in CFO > Risk Band. Long-term solvency is in Granting Authority > Solvency & General Liquidity.",
            "Would you like me to open the liquidity tab that matches the slice you are reviewing?",
        ),
    },
    "ciclo": {
        "aliases": ("ciclo", "pmr", "pme", "pmp"),
        "termos": ("ciclo financeiro", "pmr", "pme", "pmp"),
        "chaves": ("Ciclo Financeiro",),
        "pt": (
            "O ciclo financeiro mede, em dias, o tempo entre pagar fornecedores, manter estoque e receber clientes.",
            "Fórmula: Ciclo Financeiro = PMR + PME − PMP. PMR = Contas a Receber / Receita × 365; "
            "PME = Estoques / abs(Custos) × 365; PMP = Fornecedores / abs(Custos) × 365.",
            "Ciclo maior tende a aumentar a NCG e pressionar o caixa da concessão.",
            "A visualização está em CFO > Prazos e Ciclo. PMR e PME altos prendem caixa; PMP alto pode aliviar, "
            "mas também pode sinalizar alongamento de fornecedores.",
            "Posso abrir CFO / Prazos e Ciclo para você ver PMR, PME, PMP e o ciclo no recorte atual.",
        ),
        "en": (
            "The cash cycle measures, in days, the time between paying suppliers, holding inventory and collecting from customers.",
            "Cash cycle = DSO + DIO − DPO, using the CTI accounts for receivables, inventories, suppliers, revenue and costs.",
            "A longer cycle usually raises NCG and pressures concession cash.",
            "The view is CFO > Terms & Cycle. Higher DSO/DIO tie up cash; higher DPO can ease cash but may signal stretched suppliers.",
            "Would you like me to open CFO / Terms & Cycle to review DSO, DIO, DPO and the cycle in the current slice?",
        ),
    },
    "tesouraria": {
        "aliases": ("tesouraria", "saldo de tesouraria"),
        "termos": ("tesouraria", "disponivel", "emprestimos"),
        "chaves": ("Saldo de Tesouraria", "Saldo final"),
        "pt": (
            "O Saldo de Tesouraria mede a folga financeira de curto prazo da concessão.",
            "Fórmula no CTI: Saldo de Tesouraria = Disponível − Empréstimos de Curto Prazo.",
            "Saldo negativo indica dependência de banco no dia a dia; saldo positivo mostra folga imediata de caixa.",
            "O gráfico está em CFO > Capital de Giro, junto com a NCG. Cruze tesouraria fraca com NCG alta para "
            "identificar pressão de financiamento operacional.",
            "Gostaria que eu abrisse CFO / Capital de Giro para cruzar tesouraria e NCG?",
        ),
        "en": (
            "Treasury balance measures the concession's short-term cash slack.",
            "In CTI: Treasury = cash available − short-term loans.",
            "A negative balance means day-to-day bank dependence; a positive balance shows immediate cash slack.",
            "The chart is in CFO > Working Capital, next to NCG. Weak treasury with high NCG signals operating funding pressure.",
            "Would you like me to open CFO / Working Capital to compare treasury and NCG?",
        ),
    },
    "break": {
        "aliases": ("break", "equilibrio", "equilíbrio", "breakeven"),
        "termos": ("break-even", "ponto de equilibrio", "margem de seguranca", "margem de contribuicao"),
        "chaves": ("Ponto de equilibrio", "Margem de seguranca", "Margem de contribuicao", "Break-Even"),
        "pt": (
            "Break-Even é o ponto de equilíbrio: a receita mínima para cobrir custos e não gerar prejuízo operacional.",
            "Fórmula: Break-Even = Custos Fixos / Margem de Contribuição. "
            "Margem de segurança = (Receita Líquida − Break-Even) / Receita Líquida.",
            "Quanto maior a receita acima do break-even, maior a folga operacional da concessão. "
            "Margem de segurança baixa sinaliza vulnerabilidade a queda de receita ou alta de custos.",
            "Os gráficos estão em CEO > Break-Even & Margens: ponto de equilíbrio médio e margem de segurança no horizonte.",
            "Posso abrir CEO / Break-Even & Margens para você ver a folga operacional do recorte atual.",
        ),
        "en": (
            "Break-even is the revenue level needed to cover costs and avoid an operating loss.",
            "Break-even = fixed costs / contribution margin. "
            "Margin of safety = (net revenue − break-even) / net revenue.",
            "The farther revenue sits above break-even, the more operating slack the concession has. "
            "A thin safety margin means vulnerability to a revenue drop or cost increase.",
            "Charts are in CEO > Break-Even & Margins: average break-even and safety margin over the horizon.",
            "Would you like me to open CEO / Break-Even & Margins to review operating slack in the current slice?",
        ),
    },
    "wacc": {
        "aliases": ("wacc",),
        "termos": ("wacc", "custo medio", "roic", "eva"),
        "chaves": ("WACC", "ROIC", "EVA"),
        "pt": (
            "WACC é o Custo Médio Ponderado de Capital: a taxa mínima de atratividade do capital da concessão.",
            "Conceitualmente, WACC combina o custo da dívida após impostos e o custo do capital próprio, "
            "ponderados pelas respectivas participações na estrutura de capital.",
            "Quando o ROIC supera o WACC, o projeto tende a criar valor; quando fica abaixo, o EVA tende a ser negativo.",
            "Compare WACC, ROIC e ROE em Acionistas > Retorno & ROIC e veja o EVA ano a ano em Acionistas > Geração de EVA.",
            "Quer que eu abra Acionistas / Retorno & ROIC para confrontar ROIC e WACC?",
        ),
        "en": (
            "WACC is the Weighted Average Cost of Capital: the minimum required return on concession capital.",
            "It blends after-tax debt cost and equity cost, weighted by the capital structure.",
            "When ROIC exceeds WACC, the project tends to create value; below WACC, EVA tends to turn negative.",
            "Compare WACC, ROIC and ROE in Shareholders > Return & ROIC, then review yearly EVA in Shareholders > EVA Generation.",
            "Would you like me to open Shareholders / Return & ROIC to compare ROIC and WACC?",
        ),
    },
    "eva": {
        "aliases": ("eva",),
        "termos": ("eva", "valor economico", "nopat", "wacc"),
        "chaves": ("EVA", "ROIC", "WACC"),
        "pt": (
            "EVA significa Economic Value Added, ou Valor Econômico Agregado.",
            "Fórmula: EVA = NOPAT − (Capital Investido × WACC).",
            "EVA positivo indica criação de valor acima do custo de capital; EVA negativo indica destruição de valor econômico.",
            "O gráfico está em Acionistas > Geração de EVA, com barras ano a ano. Barras positivas mostram valor criado; negativas, valor destruído.",
            "Posso abrir Acionistas / Geração de EVA para você ver a trajetória no recorte atual.",
        ),
        "en": (
            "EVA is Economic Value Added.",
            "EVA = NOPAT − (Invested Capital × WACC).",
            "Positive EVA means value created above the cost of capital; negative EVA means economic value destruction.",
            "The chart is in Shareholders > EVA Generation, with year-by-year bars. Positive bars show value created; negative bars show value destroyed.",
            "Would you like me to open Shareholders / EVA Generation to review the path in the current slice?",
        ),
    },
    "opex": {
        "aliases": ("opex",),
        "termos": ("opex", "despesas operacionais", "ebitda"),
        "chaves": ("OPEX", "EBITDA", "Custos"),
        "pt": (
            "OPEX representa as despesas operacionais recorrentes da concessão: operação, manutenção, administrativas e correlatas.",
            "No CTI, o OPEX entra na DRE e reduz o EBITDA. Ele também afeta o ponto de equilíbrio.",
            "OPEX crescente sem ganho de receita comprime margem e aproxima a operação do break-even.",
            "Leia OPEX na composição da DRE em CEO > DRE Operacional e na cascata de CEO > Visão Geral & DRE.",
            "Gostaria que eu abrisse CEO / DRE Operacional para ver o peso do OPEX no recorte atual?",
        ),
        "en": (
            "OPEX is recurring operating expenditure: operations, maintenance, administrative and related costs.",
            "In CTI, OPEX sits in the income statement, reduces EBITDA and affects break-even.",
            "Rising OPEX without revenue gains compresses margin and pushes the operation toward break-even.",
            "Read OPEX in CEO > Operating DRE composition and in the CEO > Overview & DRE waterfall.",
            "Would you like me to open CEO / Operating DRE to see the OPEX weight in the current slice?",
        ),
    },
    "ltv": {
        "aliases": ("ltv", "cac"),
        "termos": ("ltv", "cac", "eficiencia comercial"),
        "chaves": ("LTV", "CAC"),
        "pt": (
            "LTV mede o valor econômico esperado de clientes ou contratos. CAC mede o custo de aquisição. "
            "A razão LTV/CAC mede eficiência comercial.",
            "Fórmula: LTV/CAC = LTV / CAC.",
            "Razão maior indica que o valor gerado supera o custo de captação e sustenta o crescimento da concessão.",
            "A aba é CEO > Eficiência LTV/CAC, com LTV vs CAC por ano e a razão. Razões muito baixas indicam aquisição cara demais.",
            "Posso abrir CEO / Eficiência LTV/CAC para você ver a razão no recorte atual.",
        ),
        "en": (
            "LTV is expected customer or contract value. CAC is acquisition cost. LTV/CAC measures commercial efficiency.",
            "LTV/CAC = LTV / CAC.",
            "A higher ratio means generated value exceeds acquisition cost and supports concession growth.",
            "The tab is CEO > LTV/CAC Efficiency, with yearly LTV vs CAC and the ratio. Very low ratios mean acquisition is too expensive.",
            "Would you like me to open CEO / LTV/CAC Efficiency to review the ratio in the current slice?",
        ),
    },
}


def _escolher_guia(pergunta: str) -> dict[str, object] | None:
    for guia in _GUIAS_METRICAS.values():
        if any(alias in pergunta for alias in guia["aliases"]):
            return guia
    return None


def _resposta_sem_llm(question: str, extra_context: str, lang: str) -> str:
    pergunta = _normalizar_texto(question)
    idioma = "en" if lang == "en" else "pt"
    fechamento = (
        "Would you like me to open a related dashboard tab, or would you rather analyze another indicator?"
        if idioma == "en"
        else "Gostaria que eu direcionasse você para a aba relacionada ou quer analisar outro indicador?"
    )
    if re.search(r"\b(o que e|o que é|what is|api)\b", pergunta) and "api" in pergunta:
        if idioma == "en":
            return (
                "An API is a defined way for systems to communicate, exposing functions or data "
                "through documented requests and responses. Would you like to connect this idea "
                "to the CTI dashboard data flow, or analyze another indicator?"
            )
        return (
            "API é uma interface que permite que sistemas conversem entre si por meio de regras, "
            "requisições e respostas bem definidas. Quer que eu conecte esse conceito ao fluxo de "
            "dados do Dashboard CTI ou prefere analisar outro indicador?"
        )

    guia = _escolher_guia(pergunta)
    pergunta_de_conta = bool(re.search(r"\b(bal|dre|flu)\b|outorga|concedente|imobilizado|intangivel", pergunta))
    chaves = tuple(guia["chaves"]) if guia else ()
    if guia:
        termos = tuple(guia["termos"])
    elif pergunta_de_conta:
        termos = tuple(token for token in pergunta.split() if len(token) > 2)
    else:
        termos = tuple(token for token in pergunta.split() if len(token) > 3)
    valores = _valores_recorte(extra_context, chaves)
    trechos = _trechos_rag(extra_context, termos)
    partes: list[str] = []

    if guia:
        conceito, formula, impacto, grafico, nav = guia[idioma]
        partes.extend([conceito, formula, impacto, grafico])
    elif trechos:
        partes.append(trechos[0])
        if len(trechos) > 1:
            partes.append(trechos[1])
    elif pergunta_de_conta and idioma == "en":
        partes.append(
            "This is a CTI ledger item from BAL, DRE or FLU. I can define the account, the related "
            "formulas and its effect on the concession, then point to the dashboard location."
        )
    elif pergunta_de_conta:
        partes.append(
            "Esta é uma rubrica do plano de contas CTI (BAL, DRE ou FLU). Posso definir a conta, "
            "as fórmulas ligadas e o impacto na concessão, e indicar onde vê-la no dashboard ou na auditoria da base."
        )
    elif idioma == "en":
        partes.append(
            "I can answer from the active CTI dashboard dataset when the question refers to "
            "project indicators, DRE, BP, DFC, scenarios, or dashboard navigation."
        )
    else:
        partes.append(
            "Posso responder com base na base ativa do Dashboard CTI quando a pergunta envolver "
            "indicadores, DRE, BP, DFC, cenários ou navegação do painel."
        )

    if valores:
        if idioma == "en":
            partes.append(f"In the current CTI slice, the available reading is {valores}.")
        else:
            partes.append(f"No recorte atual do Dashboard CTI, a leitura disponível é {valores}.")
    elif guia:
        if idioma == "en":
            partes.append("I do not have a numeric value for this indicator in the supplied local context.")
        else:
            partes.append("Não há um valor numérico deste indicador no contexto local fornecido.")

    if guia and trechos:
        extra = trechos[0]
        if extra not in " ".join(partes):
            partes.insert(1, extra)

    partes.append(guia[idioma][-1] if guia else fechamento)
    return "\n\n".join(partes)


@dataclass
class RagEngine:
    documents: list[Document]
    embeddings: TfidfEmbeddings
    vectors: np.ndarray
    backend: str
    manual_sources: list[str] = field(default_factory=list)
    document_status: dict[str, object] = field(default_factory=dict)
    _index: object | None = field(default=None, repr=False)

    @classmethod
    def from_ranking(cls, ranking: pd.DataFrame) -> "RagEngine":
        manuais = docs_manuais()
        doc_status = status_documentos()
        manual_sources = sorted({str(doc.metadata.get("source", "documento")) for doc in manuais})
        docs = docs_cenarios(ranking) + docs_glossario() + manuais
        if not docs:
            docs = [Document(page_content="Base CTI sem documentos.", metadata={"source": "vazio"})]
        texts = [d.page_content for d in docs]
        emb = TfidfEmbeddings()
        emb.fit(texts)
        vectors = np.asarray(emb.embed_documents(texts), dtype=np.float32)
        backend = "numpy"
        index = None
        try:
            index = faiss_index(vectors)
            backend = "faiss"
        except Exception:
            index = None
        return cls(
            documents=docs,
            embeddings=emb,
            vectors=vectors,
            backend=backend,
            manual_sources=manual_sources,
            document_status=doc_status,
            _index=index,
        )

    def retrieve(self, query: str, k: int = 8, cena_sel: str | None = None, user_role: str | None = None) -> list[Document]:
        if not query.strip() or not self.documents:
            return []
        permitidos = [doc for doc in self.documents if document_allowed(doc.metadata, user_role)]
        if not permitidos:
            return []
        ids_permitidos = {id(doc) for doc in permitidos}
        k = max(1, min(k, len(permitidos)))
        pool = min(len(self.documents), max(k * 8, 48))
        q = np.asarray([self.embeddings.embed_query(query)], dtype=np.float32)
        if self._index is not None:
            scores, idxs = self._index.search(q, pool)
            pares = [
                (float(scores[0][pos]), int(idxs[0][pos]))
                for pos in range(len(idxs[0]))
                if 0 <= int(idxs[0][pos]) < len(self.documents)
            ]
        else:
            sims = self.vectors @ q[0]
            ordem = np.argsort(-sims)[:pool]
            pares = [(float(sims[int(i)]), int(i)) for i in ordem]
        ranqueados = sorted(
            ((prioridade_fonte(self.documents[i], score), i) for score, i in pares if id(self.documents[i]) in ids_permitidos),
            reverse=True,
        )
        hits = [self.documents[i] for _, i in ranqueados[:k]]
        if not cena_sel:
            return hits
        ids_hit = {id(doc) for doc in hits}
        extras: list[Document] = []
        alvo = f"cenario/{cena_sel}"
        for doc in permitidos:
            src = str(doc.metadata.get("source", ""))
            tipo = str(doc.metadata.get("tipo", ""))
            if src == alvo or tipo in {"resumo", "manual_executivo", "base_conhecimento"}:
                if id(doc) not in ids_hit:
                    extras.append(doc)
                    ids_hit.add(id(doc))
        return (extras + hits)[: k + 2]

    def ask(
        self,
        question: str,
        *,
        lang: str,
        history: list[dict[str, str]],
        api_key: str | None = None,
        extra_context: str = "",
        cena_sel: str | None = None,
        user_role: str | None = None,
    ) -> tuple[str, list[str]]:
        if question_is_blocked(question, user_role):
            return deny_message(user_role, lang), []
        hits = self.retrieve(question, cena_sel=cena_sel, user_role=user_role)
        fontes = []
        for doc in hits:
            src = str(doc.metadata.get("source", "contexto"))
            if src not in fontes:
                fontes.append(src)
        if extra_context.strip() and "foco-atual" not in fontes:
            fontes.insert(0, "foco-atual")
        contexto = "\n\n".join(
            f"Fonte: {doc.metadata.get('source', 'contexto')}\n{doc.page_content}" for doc in hits
        )
        if extra_context.strip():
            contexto = sanitize_context(extra_context.strip(), user_role) + "\n\n" + contexto
        contexto = sanitize_context(contexto, user_role)
        if not self.manual_sources:
            aviso = (
                "Aviso RAG: nenhum arquivo .pdf, .md ou .txt foi indexado nas pastas de documentos. "
                "A resposta deve deixar claro que usa apenas os dados em tempo real do Dashboard CTI "
                "e conhecimento geral, sem base documental externa."
            )
            contexto = aviso + "\n\n" + contexto
        else:
            fontes_visiveis = [src for src in self.manual_sources if document_allowed({"source": src}, user_role)]
            if fontes_visiveis:
                contexto = (
                    "Arquivos documentais indexados no RAG: "
                    + ", ".join(fontes_visiveis[:8])
                    + ("\n\n" if contexto else "")
                    + contexto
                )
        chave = resolve_api_key(api_key)
        if not chave:
            resposta_sem_llm = sanitize_answer(_resposta_sem_llm(question, contexto, lang), user_role, lang)
            if not self.manual_sources:
                if lang == "en":
                    resposta_sem_llm = (
                        "Note: I did not find indexed .pdf, .md or .txt files in the documents folders, "
                        "so I am using only real-time CTI Dashboard data and general knowledge. "
                        + resposta_sem_llm
                    )
                else:
                    resposta_sem_llm = (
                        "Observação: não encontrei arquivos .pdf, .md ou .txt indexados nas pastas de documentos, "
                        "então estou usando apenas os dados em tempo real do Dashboard CTI e conhecimento geral. "
                        + resposta_sem_llm
                    )
            return resposta_sem_llm, fontes
        resposta = sanitize_answer(gerar_llm(question, contexto, lang, history, chave, user_role=user_role), user_role, lang)
        return resposta, fontes
