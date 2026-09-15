"""Internacionalização PT-BR / EN-US do dashboard CTI."""

from __future__ import annotations

from typing import Any

import streamlit as st

DEFAULT_LANG = "pt"
SUPPORTED_LANGS = ("pt", "en")

LANG_OPTIONS = {
    "pt": "🇧🇷 Português",
    "en": "🇺🇸 English",
}

# Selos canônicos (PT) → chave i18n
SELO_KEYS: dict[str, str] = {
    "Alta Rentabilidade & Alta Liquidez": "selo.alta_alta",
    "Alta Rentabilidade & Baixa Liquidez": "selo.alta_baixa",
    "Retorno Moderado & Baixo Risco": "selo.mod_baixo",
    "Forte Pressão de Investimentos": "selo.pressao",
    "Elevada Distribuição & Baixa Disponibilidade": "selo.dist_baixa",
    "Encerramento com Caixa Insuficiente": "selo.caixa_insuf",
}

TEXTS: dict[str, dict[str, str]] = {
    "pt": {
        "lang.label": "Idioma / Language",
        "app.title": "Painel financeiro CTI",
        "app.caption": "Leitura executiva dos cenários de planejamento · capital de giro, risco × retorno e probabilidade de caixa",
        "app.footer": "CTI · Dashboard modular · dados: Cti.csv",
        "sidebar.filters": "Filtros",
        "sidebar.year": "Ano do horizonte",
        "sidebar.scenario": "Cenário em foco",
        "sidebar.base": "Base",
        "sidebar.rows": "Linhas brutas",
        "sidebar.scenarios": "Cenários",
        "sidebar.years": "Anos",
        "filter.all": "Todos",
        "filter.year_n": "Ano {n}",
        "scenario.prefix": "Cenário",
        "persona.label": "Visão do stakeholder",
        "persona.geral": "Visão Geral",
        "persona.cfo": "CFO & Credores",
        "persona.acionistas": "Acionistas",
        "persona.concedente": "Poder Concedente",
        "nav.capital_giro": "Capital de giro",
        "nav.prazos": "Prazos e ciclo",
        "nav.mapeamento": "Mapeamento de Risco × Retorno",
        "nav.distribuicao": "Distribuição & Probabilidades",
        "nav.faixa": "Faixa de risco",
        "nav.comparar": "Comparar cenários",
        "nav.como_ler": "Como ler estes números",
        "header.focus": "Cenário em foco: **{cena}**",
        "header.avg_all": "Valores médios ao longo dos 12 anos.",
        "header.avg_year": "Valores do **Ano {ano}**.",
        "banner.showing": "Exibindo dados de: {cena} | Ano {ano}",
        "audit.title": "🔍 Conferir dados brutos (Auditoria)",
        "audit.found": "{n} registros encontrados na base para **{cena}** · recorte **{recorte}**.",
        "audit.empty": "Nenhuma linha da base corresponde a este recorte.",
        "kpi.ncg": "NCG",
        "kpi.treasury": "Saldo de Tesouraria",
        "kpi.cycle": "Ciclo Financeiro",
        "kpi.liquidity": "Liquidez corrente",
        "kpi.profitability": "Rentabilidade",
        "kpi.result": "Resultado líquido (média)",
        "kpi.risk": "Risco (Passivo/Ativo)",
        "kpi.ruin_prob": "Prob. caixa negativo Ano 12",
        "persona.blurb.geral_ncg": "",
        "persona.blurb.cfo": "Foco em solvência, giro e capacidade de honrar dívida no curto prazo.",
        "persona.blurb.acionistas": "Foco em retorno, resultado e liquidez que sustenta distribuição.",
        "persona.blurb.concedente": "Foco em continuidade operacional, caixa de encerramento e sustentabilidade do horizonte.",
        "txt.ncg.na": "Sem dado",
        "txt.ncg.pos": "A operação consome caixa: clientes/estoques prendem mais recurso do que fornecedores financiam.",
        "txt.ncg.neg": "A operação gera caixa: fornecedores e obrigações financiam parte do giro.",
        "txt.ncg.zero": "NCG equilibrada.",
        "txt.treasury.na": "Sem dado",
        "txt.treasury.ok": "Caixa disponível cobre (ou supera) os empréstimos de curto prazo — menor dependência de banco no dia a dia.",
        "txt.treasury.bad": "Empréstimos de curto prazo superam o disponível — a empresa depende de bancos para financiar a rotina.",
        "txt.cycle.na": "Sem dado",
        "txt.cycle.long": "Ciclo longo ({dias}): a empresa precisa financiar a operação com recurso próprio por mais tempo.",
        "txt.cycle.mod": "Ciclo positivo moderado ({dias}): ainda há intervalo a financiar entre pagar e receber.",
        "txt.cycle.neg": "Ciclo negativo ({dias}): a empresa recebe antes de pagar — situação favorável de caixa.",
        "cap.evolution": "#### Evolução no tempo (cenário selecionado)",
        "cap.ncg_source": "#### De onde vem a NCG",
        "chart.evolution": "Evolução Temporal",
        "chart.ncg_comp": "Composição da NCG",
        "chart.year": "Ano",
        "chart.indicator": "Indicador",
        "chart.component": "Componente",
        "comp.aco": "Ativo operacional (receber + estoques + créditos)",
        "comp.pco": "Passivo operacional (fornecedores + encargos + tributos)",
        "comp.ncg": "NCG (= ACO − PCO)",
        "prazos.title": "#### Prazos médios (dias)",
        "prazos.pmr": "PMR — receber de clientes",
        "prazos.pme": "PME — giro de estoque",
        "prazos.pmp": "PMP — pagar fornecedores",
        "prazos.cycle": "Ciclo financeiro",
        "prazos.chart": "Trajetória dos prazos médios",
        "prazos.days": "Dias",
        "prazos.term": "Prazo",
        "prazos.help": (
            "**Em linguagem simples**\n\n"
            "- **PMR alto** → clientes demoram a pagar → mais caixa preso.\n"
            "- **PMP alto** → fornecedores dão mais prazo → ajuda o caixa.\n"
            "- **Ciclo financeiro** = quantos dias a empresa precisa “adiantar” do próprio bolso."
        ),
        "map.title": "### Matriz Risco × Retorno",
        "map.caption": "Distribuição consolidada dos {n} cenários simulados para avaliação de rentabilidade, liquidez e endividamento.",
        "map.filter": "Filtrar",
        "map.clear": "Remover filtro",
        "map.active": "Filtro ativo: **{selo}**",
        "map.scenarios_n": "{n} cenários",
        "map.search": "Buscar e destacar cenário",
        "map.none": "(nenhum)",
        "map.chart_title": "Matriz Risco × Retorno · {n} cenários visíveis",
        "map.x": "Risco (Passivo / Ativo)",
        "map.y": "Rentabilidade (Resultado / Receita)",
        "map.size": "Liquidez (≥0)",
        "map.selo": "Selo",
        "map.comp_exp": "Comparador side-by-side (Cenário A vs Cenário B)",
        "map.comp_a": "Cenário A (ex.: pior caso P5 de caixa)",
        "map.comp_b": "Cenário B (ex.: base P50 de caixa)",
        "map.metric": "Métrica",
        "map.scene_a": "Cenário A",
        "map.scene_b": "Cenário B",
        "map.comp_cap": "**A:** {a} · **B:** {b} · ✓ = mais seguro/rentável na métrica",
        "map.focus.cfo": "Ênfase em risco e liquidez (solvência).",
        "map.focus.acionistas": "Ênfase em rentabilidade (eixo Y).",
        "map.focus.concedente": "Ênfase em selos de pressão de investimento e caixa de encerramento.",
        "map.focus.geral": "Visão equilibrada risco × retorno.",
        "map.m.profit": "Rentabilidade (%)",
        "map.m.risk": "Risco (Passivo/Ativo)",
        "map.m.liq": "Liquidez acumulada",
        "map.m.cycle": "Ciclo Financeiro (dias)",
        "dist.title": "### Distribuição & Probabilidades",
        "dist.caption": "Leitura de cauda de risco para credores e concessão — foco no encerramento do horizonte.",
        "dist.prob": "Probabilidade de caixa negativo no Ano {ano}",
        "dist.ruin": "Cenários em ruína de caixa",
        "dist.median": "Mediana do caixa no Ano 12",
        "dist.alert_hi": "Alerta de liquidez: {p:.1f}% dos cenários encerram o Ano {ano} com caixa insuficiente.",
        "dist.alert_mid": "Há cauda de risco: {p:.1f}% dos cenários terminam com caixa negativo no Ano {ano}.",
        "dist.alert_ok": "Nenhum cenário encerra o Ano {ano} com caixa negativo nesta base.",
        "dist.box_title": "Boxplot / percentis — cauda de risco do caixa final",
        "dist.box_y": "Caixa de encerramento (R$)",
        "dist.box_name": "Caixa Ano {ano}",
        "dist.foot": "P5/P95 ajudam credores a ler extremos: quanto de caixa resta nos piores e melhores 5% dos cenários.",
        "dist.prob_axis": "Probabilidade",
        "dist.hist_title": "Distribuição da liquidez final (Ano {ano}) · {n} cenários",
        "faixa.title": "#### Envelope de probabilidade (todos os cenários)",
        "faixa.caption": "Cada ponto é um cenário. A faixa sombreada cobre 90% dos casos (percentis 5 e 95). A mediana é o caminho mais típico; as linhas de extremo são o pior e o melhor caso.",
        "faixa.metric": "Métrica da nuvem",
        "faixa.risk_title": "Faixa de risco — {metric}",
        "faixa.median": "Mediana no horizonte",
        "faixa.mean": "Média no horizonte",
        "faixa.worst": "Pior caso (extremo)",
        "faixa.best": "Melhor caso (extremo)",
        "faixa.hist": "#### Histograma por ano",
        "faixa.hist_year": "Ano da distribuição",
        "faixa.hist_all": "O filtro da barra lateral está em **Todos** — escolha o ano do histograma acima.",
        "faixa.hist_fixed": "Usando o ano do filtro lateral: **Ano {ano}**.",
        "faixa.dist_title": "Distribuição de {metric}",
        "cmp.title": "#### Comparador lado a lado",
        "cmp.caption": "Escolha **2 ou 3** cenários para ver a mesma métrica no horizonte e os KPIs na mesma tela.",
        "cmp.select": "Cenários para comparar",
        "cmp.need2": "Selecione pelo menos dois cenários (máximo três).",
        "cmp.metric": "Métrica do gráfico",
        "cmp.chart": "{metric}: comparação no horizonte",
        "cmp.row.cash": "Caixa disponível",
        "cmp.row.gen": "Geração de caixa",
        "cmp.row.ncg": "NCG",
        "cmp.row.treasury": "Saldo de tesouraria",
        "cmp.row.liq": "Liquidez corrente",
        "cmp.row.cycle": "Ciclo financeiro",
        "cmp.row.profit": "Rentabilidade",
        "metric.cash_available": "Caixa disponível",
        "metric.cash_generation": "Geração de caixa",
        "metric.treasury": "Saldo de tesouraria",
        "metric.ncg": "NCG",
        "selo.alta_alta": "Alta Rentabilidade & Alta Liquidez",
        "selo.alta_baixa": "Alta Rentabilidade & Baixa Liquidez",
        "selo.mod_baixo": "Retorno Moderado & Baixo Risco",
        "selo.pressao": "Forte Pressão de Investimentos",
        "selo.dist_baixa": "Elevada Distribuição & Baixa Disponibilidade",
        "selo.caixa_insuf": "Encerramento com Caixa Insuficiente",
        "fmt.bn": "bi",
        "fmt.mn": "mi",
        "fmt.days": "dias",
        "como_ler.body": """### O que este painel responde

1. **A operação come ou gera caixa?** → olhe a **NCG**.
2. **Dependemos de banco no curto prazo?** → olhe o **Saldo de Tesouraria**.
3. **Por quantos dias financiamos a operação?** → olhe o **Ciclo Financeiro**.
4. **Como os {n} cenários se espalham em risco × retorno?** → aba **Mapeamento de Risco × Retorno**.
5. **Qual a chance de caixa negativo no encerramento?** → aba **Distribuição & Probabilidades**.
6. **Qual a faixa de caixa no horizonte?** → aba Faixa de risco.
7. **Como dois ou três cenários se comparam no tempo?** → aba Comparar cenários.

Use o seletor de **Visão do stakeholder** para priorizar os KPIs do topo.

### Fórmulas

| Indicador | Fórmula |
|---|---|
| NCG | ACO − abs(PCO) |
| Saldo de Tesouraria | Disponível − Empréstimos CP |
| PMR | (Contas a Receber / Receita) × 365 |
| PME | (Estoques / abs(Custos)) × 365 |
| PMP | (Fornecedores / abs(Custos)) × 365 |
| Ciclo Financeiro | PMR + PME − PMP |

Cenário atual: **{cena}** · Rentabilidade {rent} · Risco {risco} · Prob. caixa negativo Ano {ano}: **{p_ruina:.1f}%**.
""",
    },
    "en": {
        "lang.label": "Language / Idioma",
        "app.title": "CTI Financial Dashboard",
        "app.caption": "Executive view of planning scenarios · working capital, risk vs return and cash probability",
        "app.footer": "CTI · Modular dashboard · data: Cti.csv",
        "sidebar.filters": "Filters",
        "sidebar.year": "Horizon year",
        "sidebar.scenario": "Focus scenario",
        "sidebar.base": "Source",
        "sidebar.rows": "Raw rows",
        "sidebar.scenarios": "Scenarios",
        "sidebar.years": "Years",
        "filter.all": "All",
        "filter.year_n": "Year {n}",
        "scenario.prefix": "Scenario",
        "persona.label": "Stakeholder view",
        "persona.geral": "Overview",
        "persona.cfo": "CFO & Creditors",
        "persona.acionistas": "Shareholders",
        "persona.concedente": "Granting Authority",
        "nav.capital_giro": "Working Capital",
        "nav.prazos": "Terms & Cycle",
        "nav.mapeamento": "Risk vs Return Matrix",
        "nav.distribuicao": "Distribution & Probabilities",
        "nav.faixa": "Risk Band",
        "nav.comparar": "Compare Scenarios",
        "nav.como_ler": "How to Read These Numbers",
        "header.focus": "Focus scenario: **{cena}**",
        "header.avg_all": "Average values over the 12-year horizon.",
        "header.avg_year": "Values for **Year {ano}**.",
        "banner.showing": "Showing data for: {cena} | Year {ano}",
        "audit.title": "🔍 Review raw data (Audit)",
        "audit.found": "{n} records found for **{cena}** · slice **{recorte}**.",
        "audit.empty": "No rows match this filter.",
        "kpi.ncg": "NWC",
        "kpi.treasury": "Treasury Balance",
        "kpi.cycle": "Cash Conversion Cycle",
        "kpi.liquidity": "Current Liquidity",
        "kpi.profitability": "Profitability",
        "kpi.result": "Net Income (avg)",
        "kpi.risk": "Risk (Liabilities/Assets)",
        "kpi.ruin_prob": "Prob. negative cash Year 12",
        "persona.blurb.cfo": "Focus on solvency, turnover and short-term debt capacity.",
        "persona.blurb.acionistas": "Focus on return, earnings and liquidity that supports distributions.",
        "persona.blurb.concedente": "Focus on operating continuity, closing cash and horizon sustainability.",
        "txt.ncg.na": "No data",
        "txt.ncg.pos": "Operations consume cash: receivables/inventory tie up more resources than suppliers fund.",
        "txt.ncg.neg": "Operations generate cash: suppliers and obligations help fund working capital.",
        "txt.ncg.zero": "Balanced NWC.",
        "txt.treasury.na": "No data",
        "txt.treasury.ok": "Available cash covers (or exceeds) short-term loans — lower day-to-day bank dependence.",
        "txt.treasury.bad": "Short-term loans exceed cash on hand — the firm relies on banks to fund routine needs.",
        "txt.cycle.na": "No data",
        "txt.cycle.long": "Long cycle ({dias}): the firm must self-fund operations for longer.",
        "txt.cycle.mod": "Moderate positive cycle ({dias}): there is still a funding gap between paying and collecting.",
        "txt.cycle.neg": "Negative cycle ({dias}): the firm collects before it pays — a cash-friendly position.",
        "cap.evolution": "#### Evolution over time (selected scenario)",
        "cap.ncg_source": "#### Where NWC comes from",
        "chart.evolution": "Time Evolution",
        "chart.ncg_comp": "NWC Composition",
        "chart.year": "Year",
        "chart.indicator": "Indicator",
        "chart.component": "Component",
        "comp.aco": "Operating current assets (receivables + inventory + tax credits)",
        "comp.pco": "Operating current liabilities (suppliers + payroll + taxes)",
        "comp.ncg": "NWC (= OCA − OCL)",
        "prazos.title": "#### Average terms (days)",
        "prazos.pmr": "DSO — collect from customers",
        "prazos.pme": "DIO — inventory turnover",
        "prazos.pmp": "DPO — pay suppliers",
        "prazos.cycle": "Cash conversion cycle",
        "prazos.chart": "Average terms trajectory",
        "prazos.days": "Days",
        "prazos.term": "Term",
        "prazos.help": (
            "**In plain language**\n\n"
            "- **High DSO** → customers pay slowly → more cash tied up.\n"
            "- **High DPO** → suppliers grant more time → helps cash.\n"
            "- **Cash conversion cycle** = days the firm must fund from its own pocket."
        ),
        "map.title": "### Risk vs Return Matrix",
        "map.caption": "Consolidated distribution of {n} simulated scenarios for profitability, liquidity and leverage.",
        "map.filter": "Filter",
        "map.clear": "Clear filter",
        "map.active": "Active filter: **{selo}**",
        "map.scenarios_n": "{n} scenarios",
        "map.search": "Search and highlight scenario",
        "map.none": "(none)",
        "map.chart_title": "Risk vs Return Matrix · {n} scenarios visible",
        "map.x": "Risk (Liabilities / Assets)",
        "map.y": "Profitability (Income / Revenue)",
        "map.size": "Liquidity (≥0)",
        "map.selo": "Badge",
        "map.comp_exp": "Side-by-side comparator (Scenario A vs B)",
        "map.comp_a": "Scenario A (e.g. P5 cash worst case)",
        "map.comp_b": "Scenario B (e.g. P50 cash base)",
        "map.metric": "Metric",
        "map.scene_a": "Scenario A",
        "map.scene_b": "Scenario B",
        "map.comp_cap": "**A:** {a} · **B:** {b} · ✓ = safer/more profitable on the metric",
        "map.focus.cfo": "Emphasis on risk and liquidity (solvency).",
        "map.focus.acionistas": "Emphasis on profitability (Y axis).",
        "map.focus.concedente": "Emphasis on investment-pressure badges and closing cash.",
        "map.focus.geral": "Balanced risk vs return view.",
        "map.m.profit": "Profitability (%)",
        "map.m.risk": "Risk (Liabilities/Assets)",
        "map.m.liq": "Accumulated liquidity",
        "map.m.cycle": "Cash Conversion Cycle (days)",
        "dist.title": "### Distribution & Probabilities",
        "dist.caption": "Tail-risk reading for creditors and concession — focus on horizon close-out.",
        "dist.prob": "Probability of negative cash in Year {ano}",
        "dist.ruin": "Scenarios in cash shortfall",
        "dist.median": "Median cash in Year 12",
        "dist.alert_hi": "Liquidity alert: {p:.1f}% of scenarios end Year {ano} with insufficient cash.",
        "dist.alert_mid": "There is a risk tail: {p:.1f}% of scenarios end Year {ano} with negative cash.",
        "dist.alert_ok": "No scenario ends Year {ano} with negative cash in this dataset.",
        "dist.box_title": "Boxplot / percentiles — final cash risk tail",
        "dist.box_y": "Closing cash (BRL)",
        "dist.box_name": "Cash Year {ano}",
        "dist.foot": "P5/P95 help creditors read extremes: cash left in the worst and best 5% of scenarios.",
        "dist.prob_axis": "Probability",
        "dist.hist_title": "Final liquidity distribution (Year {ano}) · {n} scenarios",
        "faixa.title": "#### Probability envelope (all scenarios)",
        "faixa.caption": "Each point is a scenario. The shaded band covers 90% of cases (5th–95th percentiles). The median is the typical path; extremes are worst and best cases.",
        "faixa.metric": "Cloud metric",
        "faixa.risk_title": "Risk band — {metric}",
        "faixa.median": "Horizon median",
        "faixa.mean": "Horizon mean",
        "faixa.worst": "Worst case (extreme)",
        "faixa.best": "Best case (extreme)",
        "faixa.hist": "#### Histogram by year",
        "faixa.hist_year": "Distribution year",
        "faixa.hist_all": "Sidebar filter is **All** — pick the histogram year above.",
        "faixa.hist_fixed": "Using the sidebar year filter: **Year {ano}**.",
        "faixa.dist_title": "Distribution of {metric}",
        "cmp.title": "#### Side-by-side comparator",
        "cmp.caption": "Pick **2 or 3** scenarios to compare the same metric over the horizon and KPIs on one screen.",
        "cmp.select": "Scenarios to compare",
        "cmp.need2": "Select at least two scenarios (max three).",
        "cmp.metric": "Chart metric",
        "cmp.chart": "{metric}: horizon comparison",
        "cmp.row.cash": "Available cash",
        "cmp.row.gen": "Cash generation",
        "cmp.row.ncg": "NWC",
        "cmp.row.treasury": "Treasury balance",
        "cmp.row.liq": "Current liquidity",
        "cmp.row.cycle": "Cash conversion cycle",
        "cmp.row.profit": "Profitability",
        "metric.cash_available": "Available cash",
        "metric.cash_generation": "Cash generation",
        "metric.treasury": "Treasury balance",
        "metric.ncg": "NWC",
        "selo.alta_alta": "High Profitability & High Liquidity",
        "selo.alta_baixa": "High Profitability & Low Liquidity",
        "selo.mod_baixo": "Moderate Return & Low Risk",
        "selo.pressao": "Strong Investment Pressure",
        "selo.dist_baixa": "High Distribution & Low Availability",
        "selo.caixa_insuf": "Closing with Insufficient Cash",
        "fmt.bn": "bn",
        "fmt.mn": "mn",
        "fmt.days": "days",
        "como_ler.body": """### What this dashboard answers

1. **Do operations consume or generate cash?** → look at **NWC**.
2. **Do we depend on banks short term?** → look at **Treasury Balance**.
3. **How many days do we fund operations?** → look at the **Cash Conversion Cycle**.
4. **How do the {n} scenarios spread in risk vs return?** → **Risk vs Return Matrix**.
5. **What is the chance of negative closing cash?** → **Distribution & Probabilities**.
6. **What is the cash band over the horizon?** → **Risk Band**.
7. **How do two or three scenarios compare over time?** → **Compare Scenarios**.

Use **Stakeholder view** to prioritize top KPIs.

### Formulas

| Indicator | Formula |
|---|---|
| NWC | OCA − abs(OCL) |
| Treasury Balance | Cash − ST Loans |
| DSO | (Receivables / Revenue) × 365 |
| DIO | (Inventory / abs(COGS)) × 365 |
| DPO | (Payables / abs(COGS)) × 365 |
| Cash Conversion Cycle | DSO + DIO − DPO |

Current scenario: **{cena}** · Profitability {rent} · Risk {risco} · Prob. negative cash Year {ano}: **{p_ruina:.1f}%**.
""",
    },
}


def get_lang() -> str:
    lang = st.session_state.get("lang", DEFAULT_LANG)
    return lang if lang in SUPPORTED_LANGS else DEFAULT_LANG


def set_lang(lang: str) -> None:
    st.session_state["lang"] = lang if lang in SUPPORTED_LANGS else DEFAULT_LANG


def t(key: str, lang: str | None = None, **kwargs: Any) -> str:
    """Retorna texto traduzido; fallback PT se a chave não existir no idioma ativo."""
    code = lang or get_lang()
    bucket = TEXTS.get(code) or TEXTS[DEFAULT_LANG]
    text = bucket.get(key)
    if text is None:
        text = TEXTS[DEFAULT_LANG].get(key, key)
    if kwargs:
        try:
            return text.format(**kwargs)
        except (KeyError, ValueError):
            return text
    return text


def get_text(key: str, lang: str | None = None, **kwargs: Any) -> str:
    """Alias de ``t`` (API pedida no briefing)."""
    return t(key, lang, **kwargs)


def translate_selo(nome_pt: str, lang: str | None = None) -> str:
    key = SELO_KEYS.get(nome_pt)
    return t(key, lang) if key else nome_pt
