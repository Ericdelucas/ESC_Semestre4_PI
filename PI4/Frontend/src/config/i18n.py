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
        "persona.ceo": "CEO",
        "persona.cfo": "CFO",
        "persona.acionistas": "Acionistas",
        "persona.docente": "Poder Concedente",
        "persona.geral": "Visão Geral",
        "persona.concedente": "Poder Concedente",
        "persona.teste": "Teste",
        "nav.cfo": "CFO",
        "nav.acionistas": "Acionistas",
        "nav.docente": "Poder Concedente",
        "nav.capital_giro": "Capital de giro",
        "nav.prazos": "Prazos e ciclo",
        "nav.mapeamento": "Mapeamento de Risco × Retorno",
        "nav.distribuicao": "Distribuição & Probabilidades",
        "nav.faixa": "Faixa de risco",
        "nav.comparar": "Comparar cenários",
        "nav.assistente": "🤖 Assistente IA",
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
        "kpi.ebitda_margin": "Margem EBITDA",
        "kpi.retorno": "Retorno esperado",
        "kpi.selo_top": "Selo predominante",
        "kpi.selo_ret": "Selo de maior retorno",
        "kpi.n_cenarios": "Cenários simulados",
        "kpi.horizonte": "Horizonte (anos)",
        "kpi.r2": "R² (EBITDA × resultado)",
        "kpi.cv_caixa": "CV caixa Ano 12",
        "persona.blurb.geral_ncg": "",
        "persona.blurb.ceo": "Visão estratégica: viabilidade de longo prazo, rentabilidade e exposição a riscos nos 1.200 cenários.",
        "persona.blurb.cfo": "Visão de liquidez: NCG, tesouraria, ciclo financeiro e dependência de financiamento bancário.",
        "persona.blurb.acionistas": "Visão do investidor: criação de valor (EVA), retorno sobre o capital (ROIC) e eficiência de dividendos.",
        "persona.blurb.docente": "Visão metodológica: validação do modelo, engenharia de cenários e rastreabilidade da base.",
        "persona.blurb.concedente": "Visão do órgão regulador: cumprimento do plano de investimentos (CAPEX) e saúde financeira contínua da concessão.",
        "persona.blurb.teste": "",
        "stake.ceo.title": "### Visão estratégica — CEO",
        "stake.ceo.exec": "#### Resumo executivo",
        "stake.ceo.viable_ok": "Projeto **viável** no horizonte: apenas {p:.1f}% dos cenários encerram com caixa negativo. Selo predominante: **{selo}** ({n} de {total}).",
        "stake.ceo.viable_mid": "Atenção: {p:.1f}% dos cenários encerram com caixa negativo. Selo predominante: **{selo}** ({n} de {total}).",
        "stake.ceo.viable_bad": "Alerta de viabilidade: {p:.1f}% dos cenários encerram com caixa negativo. Selo predominante: **{selo}** ({n} de {total}).",
        "stake.ceo.chart_rev": "#### Receitas × custos e acúmulo de caixa (cenário em foco)",
        "stake.cfo.title": "### Visão de liquidez — CFO",
        "stake.cfo.alerts": "#### Alertas de caixa",
        "stake.cfo.chart": "#### NCG × Saldo de Tesouraria no horizonte",
        "stake.aci.title": "### Visão de retorno — Acionistas",
        "stake.aci.chart": "#### Matriz risco × retorno por selo",
        "stake.aci.table": "#### Sensibilidade do caixa final (Ano 12)",
        "stake.doc.title": "### Visão regulatória — Poder Concedente",
        "stake.doc.method": "#### Metodologia da simulação",
        "stake.doc.method_body": "A base `Cti.csv` alimenta **{n} cenários** em um horizonte de **{anos} anos**.\n\nDrivers típicos do modelo: trajetórias de **EBITDA**, choques de **IPCA/deflação** e custo de capital ligado à **Selic**. Os indicadores de NCG, tesouraria, ciclo e risco são derivados conta a conta a partir do balanço, DRE e fluxo.\n\nA métrica R² conecta **EBITDA médio** ao **resultado líquido médio** entre cenários (adererência do driver ao resultado).",
        "stake.doc.trace": "#### Rastreabilidade — amostra da base bruta",
        "stake.doc.rag": "#### Validação do pipeline RAG",
        "stake.doc.rag_ok": "Índice RAG disponível via API em `http://localhost:8000/api/health` (manuais em `Backend/documentos/` + cenários em `Cti.csv`).",
        "stake.missing.rev": "Colunas de receita/custos/caixa indisponíveis neste recorte.",
        "stake.missing.rank": "Ranking vazio.",
        "stake.missing.caixa12": "Caixa Ano 12 indisponível.",
        "txt.bank.na": "Sem dado de tesouraria para avaliar dependência bancária.",
        "txt.bank.dep": "Dependência de empréstimos no curto prazo: saldo de tesouraria negativo (disponível insuficiente frente a empréstimos CP).",
        "txt.bank.ok": "Tesouraria sem pressão imediata de empréstimos CP: disponível cobre a dívida de curto prazo neste recorte.",
        "chart.receita": "Receita",
        "chart.custo": "Custos",
        "chart.caixa_acum": "Caixa (disponível)",
        "chart.rev_cost": "Receitas × custos e caixa",
        "table.percentil": "Percentil",
        "table.caixa12": "Caixa Ano 12",
        "table.p10": "P10 (pessimista)",
        "table.p50": "P50 (mediana)",
        "table.p90": "P90 (otimista)",
        "selo.dist.title": "Distribuição dos selos de risco",
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
        "map.focus.docente": "Ênfase na validação metodológica dos selos e cenários simulados.",
        "map.focus.geral": "Visão equilibrada risco × retorno.",
        "map.focus.ceo": "Ênfase em viabilidade de longo prazo e exposição a riscos.",
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
        "ai.title": "🤖 Assistente de IA CTI",
        "ai.caption": "Motor analítico nativo com contexto da base ativa, DRE, BP, DFC e indicadores CTI.",
        "ai.placeholder": "Pergunte ao Assistente CTI...",
        "ai.welcome": "Assistente de Análise CTI pronto. Como posso ajudar com os indicadores de EBITDA, NCG, Liquidez ou navegação pelo dashboard?",
        "ai.sources": "Fontes consultadas",
        "ai.no_key": "Sem `GOOGLE_API_KEY` o assistente só recupera trechos. Para respostas geradas, cole a chave em Configurações, no `.env` ou em `.streamlit/secrets.toml`.",
        "ai.clear": "Limpar conversa",
        "ai.thinking": "Consultando cenários e manuais…",
        "ai.api_key": "Chave da API Gemini",
        "ai.api_key_help": "Obtenha em Google AI Studio. A chave fica só nesta sessão, no .env ou nos secrets do Streamlit.",
        "ai.indexed": "Índice RAG: {n_docs} trechos · {n_cen} cenários · backend {backend}",
        "ai.extra_focus": "Contexto da tela: cenário em foco {cena}; {n} cenários na base; prob. caixa negativo Ano {ano}: {p_ruina}%; rentabilidade do recorte {rent}.",
        "ai.toggle": "🤖 Assistente CTI",
        "ai.close": "Fechar",
        "ai.toggle_help": "Abre a barra lateral direita, sem sair da análise.",
        "ai.settings": "⚙️ Configurações",
    },
    "en": {
        "lang.label": "Language / Idioma",
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
        "persona.ceo": "CEO",
        "persona.cfo": "CFO",
        "persona.acionistas": "Shareholders",
        "persona.docente": "Granting Authority",
        "persona.geral": "Overview",
        "persona.concedente": "Granting Authority",
        "persona.teste": "Test",
        "nav.cfo": "CFO",
        "nav.acionistas": "Shareholders",
        "nav.docente": "Granting Authority",
        "nav.capital_giro": "Working Capital",
        "nav.prazos": "Terms & Cycle",
        "nav.mapeamento": "Risk vs Return Matrix",
        "nav.distribuicao": "Distribution & Probabilities",
        "nav.faixa": "Risk Band",
        "nav.comparar": "Compare Scenarios",
        "nav.assistente": "🤖 AI Assistant",
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
        "kpi.ebitda_margin": "EBITDA margin",
        "kpi.retorno": "Expected return",
        "kpi.selo_top": "Predominant badge",
        "kpi.selo_ret": "Highest-return badge",
        "kpi.n_cenarios": "Simulated scenarios",
        "kpi.horizonte": "Horizon (years)",
        "kpi.r2": "R² (EBITDA × income)",
        "kpi.cv_caixa": "Year-12 cash CV",
        "persona.blurb.ceo": "Strategic view: long-term viability, profitability and risk exposure across 1,200 scenarios.",
        "persona.blurb.cfo": "Liquidity view: NWC, treasury, cash cycle and short-term bank funding dependence.",
        "persona.blurb.acionistas": "Investor view: value creation (EVA), return on capital (ROIC), and dividend efficiency.",
        "persona.blurb.docente": "Methodological view: model validation, scenario engineering and data lineage.",
        "persona.blurb.concedente": "Regulator view: fulfillment of the investment plan (CAPEX) and continuous financial health of the concession.",
        "persona.blurb.teste": "",
        "stake.ceo.title": "### Strategic view — CEO",
        "stake.ceo.exec": "#### Executive summary",
        "stake.ceo.viable_ok": "Project looks **viable**: only {p:.1f}% of scenarios end with negative cash. Predominant badge: **{selo}** ({n} of {total}).",
        "stake.ceo.viable_mid": "Caution: {p:.1f}% of scenarios end with negative cash. Predominant badge: **{selo}** ({n} of {total}).",
        "stake.ceo.viable_bad": "Viability alert: {p:.1f}% of scenarios end with negative cash. Predominant badge: **{selo}** ({n} of {total}).",
        "stake.ceo.chart_rev": "#### Revenue × costs and cash build-up (focus scenario)",
        "stake.cfo.title": "### Liquidity view — CFO",
        "stake.cfo.alerts": "#### Cash alerts",
        "stake.cfo.chart": "#### NWC × Treasury balance over the horizon",
        "stake.aci.title": "### Return view — Shareholders",
        "stake.aci.chart": "#### Risk vs return matrix by badge",
        "stake.aci.table": "#### Closing-cash sensitivity (Year 12)",
        "stake.doc.title": "### Regulatory view — Granting Authority",
        "stake.doc.method": "#### Simulation methodology",
        "stake.doc.method_body": "The `Cti.csv` dataset feeds **{n} scenarios** over a **{anos}-year** horizon.\n\nTypical drivers: **EBITDA** paths, **IPCA/deflation** shocks and funding cost tied to **Selic**. NWC, treasury, cycle and risk are derived account-by-account from balance sheet, income statement and cash flow.\n\nR² links average **EBITDA** to average **net income** across scenarios (driver-to-outcome fit).",
        "stake.doc.trace": "#### Traceability — raw sample",
        "stake.doc.rag": "#### RAG pipeline check",
        "stake.doc.rag_ok": "RAG index available via API at `http://localhost:8000/api/health` (manuals in `Backend/documentos/` + scenarios in `Cti.csv`).",
        "stake.missing.rev": "Revenue/cost/cash columns unavailable for this cut.",
        "stake.missing.rank": "Empty ranking.",
        "stake.missing.caixa12": "Year-12 cash unavailable.",
        "txt.bank.na": "No treasury data to assess bank funding dependence.",
        "txt.bank.dep": "Short-term bank funding dependence: negative treasury balance (cash below short-term loans).",
        "txt.bank.ok": "No immediate short-term loan pressure: available cash covers ST debt in this cut.",
        "chart.receita": "Revenue",
        "chart.custo": "Costs",
        "chart.caixa_acum": "Cash (available)",
        "chart.rev_cost": "Revenue × costs and cash",
        "table.percentil": "Percentile",
        "table.caixa12": "Year-12 cash",
        "table.p10": "P10 (downside)",
        "table.p50": "P50 (median)",
        "table.p90": "P90 (upside)",
        "selo.dist.title": "Risk-badge distribution",
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
        "map.focus.docente": "Emphasis on methodological validation of badges and simulated scenarios.",
        "map.focus.geral": "Balanced risk vs return view.",
        "map.focus.ceo": "Emphasis on long-term viability and risk exposure.",
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
        "ai.title": "🤖 CTI AI Assistant",
        "ai.caption": "Native analytical engine with active dataset, Income Statement, Balance Sheet, Cash Flow and CTI indicators.",
        "ai.placeholder": "Ask the CTI Assistant...",
        "ai.welcome": "CTI Analysis Assistant ready. How can I help with EBITDA, NWC, Liquidity or dashboard navigation?",
        "ai.sources": "Sources",
        "ai.no_key": "Without `GOOGLE_API_KEY` the assistant only retrieves excerpts. For generated answers, paste the key under Settings, in `.env` or `.streamlit/secrets.toml`.",
        "ai.clear": "Clear Chat",
        "ai.thinking": "Consulting scenarios and manuals…",
        "ai.api_key": "Gemini API key",
        "ai.api_key_help": "Get it from Google AI Studio. The key stays in this session, .env or Streamlit secrets.",
        "ai.indexed": "RAG index: {n_docs} chunks · {n_cen} scenarios · {backend} backend",
        "ai.extra_focus": "Screen context: focus scenario {cena}; {n} scenarios in the dataset; prob. negative cash Year {ano}: {p_ruina}%; slice profitability {rent}.",
        "ai.toggle": "🤖 CTI Assistant",
        "ai.close": "Close",
        "ai.toggle_help": "Opens the right sidebar without leaving the analysis.",
        "ai.settings": "⚙️ Settings",
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
