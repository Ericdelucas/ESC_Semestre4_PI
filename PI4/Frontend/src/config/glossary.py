"""Glossário executivo dos indicadores — tooltips PT-BR / EN-US."""

from __future__ import annotations

from src.config.i18n import DEFAULT_LANG, get_lang

# Textos curtos (2–3 frases) para o parâmetro help= do Streamlit.
GLOSSARIO: dict[str, dict[str, str]] = {
    "pt": {
        "ncg": (
            "Necessidade de Capital de Giro: recursos para financiar a operação "
            "entre pagamentos e recebimentos. NCG positiva consome caixa; negativa gera caixa."
        ),
        "treasury": (
            "Recursos líquidos de curto prazo (disponível menos empréstimos CP) "
            "para cobrir déficits operacionais. Valor negativo indica dependência de banco no dia a dia."
        ),
        "cycle": (
            "Tempo, em dias, entre pagar fornecedores e receber das vendas (PMR + PME − PMP). "
            "Quanto maior, mais tempo a empresa financia a operação com recurso próprio."
        ),
        "liquidity": (
            "Capacidade de honrar obrigações de curto prazo com ativos circulantes. "
            "Acima de 1x indica folga; abaixo de 1x indica aperto de caixa."
        ),
        "profitability": (
            "Resultado líquido em relação à receita. Mostra quanto das vendas se converte em lucro no recorte."
        ),
        "result": (
            "Resultado líquido médio no recorte selecionado. Indica lucro ou prejuízo do período analisado."
        ),
        "risk": (
            "Relação passivo / ativo. Quanto maior, maior a alavancagem e a dependência de capital de terceiros."
        ),
        "ruin_prob": (
            "Percentual de cenários que encerram o Ano 12 com caixa negativo. "
            "Mede a chance de insolvência de caixa no horizonte."
        ),
        "pmr": (
            "Prazo médio de recebimento: dias que os clientes levam para pagar. PMR alto prende mais caixa na operação."
        ),
        "pme": (
            "Prazo médio de estocagem: dias que o estoque fica parado. PME alto aumenta a necessidade de giro."
        ),
        "pmp": (
            "Prazo médio de pagamento: dias para pagar fornecedores. PMP alto é financiamento espontâneo e alivia o caixa."
        ),
        "aco": (
            "Ativo circulante operacional: contas a receber, estoques e créditos. É o lado que prende recurso na operação."
        ),
        "pco": (
            "Passivo circulante operacional: fornecedores, encargos e tributos. É o financiamento espontâneo da operação."
        ),
        "cash_available": (
            "Saldo de caixa e equivalentes disponível. Mostra a liquidez imediata do cenário no recorte."
        ),
        "cash_generation": (
            "Caixa gerado ou consumido pelas operações no período. Indica a capacidade de autofinanciamento."
        ),
        "ruin_count": (
            "Quantidade de cenários que terminam o horizonte com caixa negativo. Complementa a probabilidade de ruína."
        ),
        "median_cash": (
            "Valor central do caixa no Ano 12: metade dos cenários fica acima e metade abaixo deste ponto."
        ),
        "p5": "Pior 5% dos cenários: só 5% encerram com caixa ainda menor. Leitura de cauda de risco para credores.",
        "p25": "Primeiro quartil: 25% dos cenários encerram o horizonte com caixa abaixo deste valor.",
        "p50": "Mediana: valor típico do caixa de encerramento — metade dos cenários fica de cada lado.",
        "p75": "Terceiro quartil: 75% dos cenários encerram com caixa abaixo deste valor.",
        "p95": "Melhores 5% dos cenários: apenas 5% encerram com caixa ainda maior.",
        "ncg_treasury": (
            "Trajetória da NCG (caixa preso ou gerado na operação) e do Saldo de Tesouraria no horizonte. "
            "O marcador âncora segue o ano escolhido na barra lateral."
        ),
        "ncg_composition": (
            "A NCG é ACO − PCO: ativo operacional (receber + estoques) menos passivo operacional (fornecedores e obrigações)."
        ),
        "prazos": (
            "PMR e PME prendem caixa; PMP alivia. O ciclo financeiro (PMR + PME − PMP) é quantos dias a empresa adianta do próprio bolso."
        ),
        "risk_return": (
            "Cada ponto é um cenário. O eixo X é risco (passivo/ativo); o Y é rentabilidade; o tamanho do ponto é a liquidez."
        ),
        "dist_overview": (
            "Leitura de cauda: probabilidade e volume de cenários com caixa negativo no encerramento, mais a mediana do caixa final."
        ),
        "faixa_envelope": (
            "A faixa sombreada cobre 90% dos cenários (P5–P95). A mediana é o caminho típico; as bordas são o pior e o melhor caso."
        ),
        "cmp_overview": (
            "Compara 2 ou 3 cenários na mesma métrica ao longo do horizonte. Os cards repetem caixa, NCG, tesouraria, liquidez e ciclo."
        ),
        "sidebar_year": (
            "Recorta KPIs e gráficos para um ano do horizonte de 12 anos. Use Todos para a média do período."
        ),
        "sidebar_scenario": (
            "Cenário simulado em destaque. Os KPIs do topo e os gráficos de evolução seguem este recorte."
        ),
        "persona": (
            "Alterna a visão: CEO (estratégia/risco), CFO (liquidez), Acionistas (retorno) e Poder Concedente (continuidade operacional)."
        ),
        "metric_picker": (
            "Indicador do gráfico. NCG, tesouraria, caixa disponível e geração de caixa descrevem o capital de giro no horizonte."
        ),
        "cmp_select": (
            "Selecione 2 ou 3 cenários para ver a mesma métrica no tempo e os KPIs lado a lado."
        ),
        "map_search": (
            "Destaca um cenário na matriz risco × retorno para localizá-lo entre os pontos."
        ),
        "map_comp": (
            "Escolha um cenário para comparar rentabilidade, risco, liquidez acumulada e ciclo financeiro lado a lado."
        ),
        "faixa_median": "Mediana da métrica escolhida no horizonte, entre todos os cenários.",
        "faixa_mean": "Média da métrica escolhida no horizonte, entre todos os cenários.",
        "faixa_worst": "Extremo desfavorável da métrica no horizonte (pior caso entre os cenários).",
        "faixa_best": "Extremo favorável da métrica no horizonte (melhor caso entre os cenários).",
        "faixa_hist_year": (
            "Ano cuja distribuição é mostrada no histograma. Com o filtro lateral em Todos, escolha o ano aqui."
        ),
    },
    "en": {
        "ncg": (
            "Net working capital needed to fund daily operations between payments and collections. "
            "Positive NWC consumes cash; negative NWC generates cash."
        ),
        "treasury": (
            "Short-term net resources (cash minus ST loans) to cover operating shortfalls. "
            "A negative balance means day-to-day bank dependence."
        ),
        "cycle": (
            "Days between paying suppliers and collecting from sales (DSO + DIO − DPO). "
            "The longer it is, the longer the firm self-funds operations."
        ),
        "liquidity": (
            "Ability to meet short-term obligations with current assets. Above 1x is slack; below 1x is a cash squeeze."
        ),
        "profitability": (
            "Net income over revenue. Shows how much of sales converts into profit in the selected slice."
        ),
        "result": (
            "Average net income in the selected slice. Indicates profit or loss for the period under review."
        ),
        "risk": (
            "Liabilities over assets. Higher values mean more leverage and greater reliance on third-party capital."
        ),
        "ruin_prob": (
            "Share of scenarios that end Year 12 with negative cash. Measures the chance of cash insolvency at the horizon."
        ),
        "pmr": (
            "Days sales outstanding: how long customers take to pay. High DSO ties up more cash in operations."
        ),
        "pme": (
            "Days inventory outstanding: how long stock sits idle. High DIO raises the working-capital need."
        ),
        "pmp": (
            "Days payable outstanding: how long the firm takes to pay suppliers. High DPO is spontaneous funding and eases cash."
        ),
        "aco": (
            "Operating current assets: receivables, inventory and tax credits. This is the side that ties up cash in operations."
        ),
        "pco": (
            "Operating current liabilities: suppliers, payroll and taxes. This is spontaneous funding of operations."
        ),
        "cash_available": (
            "Cash and cash equivalents on hand. Shows the scenario's immediate liquidity in the selected slice."
        ),
        "cash_generation": (
            "Cash generated or consumed by operations in the period. Indicates self-funding capacity."
        ),
        "ruin_count": (
            "Number of scenarios that end the horizon with negative cash. Complements the shortfall probability."
        ),
        "median_cash": (
            "Center of Year-12 cash: half of the scenarios sit above this point and half below."
        ),
        "p5": "Worst 5% of scenarios: only 5% end with even less cash. Tail-risk reading for creditors.",
        "p25": "Lower quartile: 25% of scenarios end the horizon with cash below this value.",
        "p50": "Median: typical closing-cash outcome — half the scenarios on each side.",
        "p75": "Upper quartile: 75% of scenarios end with cash below this value.",
        "p95": "Best 5% of scenarios: only 5% end with even more cash.",
        "ncg_treasury": (
            "Path of NWC (cash tied up or generated by operations) and Treasury Balance over the horizon. "
            "The anchor marker follows the year chosen in the sidebar."
        ),
        "ncg_composition": (
            "NWC is OCA − OCL: operating assets (receivables + inventory) minus operating liabilities (suppliers and obligations)."
        ),
        "prazos": (
            "DSO and DIO tie up cash; DPO eases it. The cash conversion cycle (DSO + DIO − DPO) is how many days the firm funds from its own pocket."
        ),
        "risk_return": (
            "Each point is a scenario. The X axis is risk (liabilities/assets); Y is profitability; point size is liquidity."
        ),
        "dist_overview": (
            "Tail-risk reading: probability and count of scenarios with negative closing cash, plus median final cash."
        ),
        "faixa_envelope": (
            "The shaded band covers 90% of scenarios (P5–P95). The median is the typical path; the edges are worst and best cases."
        ),
        "cmp_overview": (
            "Compare 2 or 3 scenarios on the same metric over the horizon. Cards repeat cash, NWC, treasury, liquidity and cycle."
        ),
        "sidebar_year": (
            "Slices KPIs and charts to one year of the 12-year horizon. Use All for the period average."
        ),
        "sidebar_scenario": (
            "Highlighted simulated scenario. Top KPIs and evolution charts follow this slice."
        ),
        "persona": (
            "Switches the view: CEO (strategy/risk), CFO (liquidity), Shareholders (return) and Granting Authority (regulation)."
        ),
        "metric_picker": (
            "Chart indicator. NWC, treasury, available cash and cash generation describe working capital over the horizon."
        ),
        "cmp_select": (
            "Pick 2 or 3 scenarios to see the same metric over time and KPIs side by side."
        ),
        "map_search": (
            "Highlights a scenario on the risk vs return matrix so you can find it among the points."
        ),
        "map_comp": (
            "Pick a scenario to compare profitability, risk, accumulated liquidity and cash conversion cycle side by side."
        ),
        "faixa_median": "Median of the selected metric over the horizon, across all scenarios.",
        "faixa_mean": "Mean of the selected metric over the horizon, across all scenarios.",
        "faixa_worst": "Unfavorable extreme of the metric over the horizon (worst case across scenarios).",
        "faixa_best": "Favorable extreme of the metric over the horizon (best case across scenarios).",
        "faixa_hist_year": (
            "Year whose distribution is shown in the histogram. When the sidebar filter is All, pick the year here."
        ),
    },
}

NUVEM_HELP: dict[str, str] = {
    "metric.cash_available": "cash_available",
    "metric.cash_generation": "cash_generation",
    "metric.treasury": "treasury",
    "metric.ncg": "ncg",
}

PERCENTIL_HELP: dict[str, str] = {
    "P5": "p5",
    "P25": "p25",
    "P50": "p50",
    "P75": "p75",
    "P95": "p95",
}


def glossary(key: str) -> str:
    """Retorna a definição no idioma ativo; fallback PT se a chave não existir."""
    lang = get_lang()
    bucket = GLOSSARIO.get(lang) or GLOSSARIO[DEFAULT_LANG]
    text = bucket.get(key)
    if text is None:
        return GLOSSARIO[DEFAULT_LANG].get(key, "")
    return text


def help_text(key: str) -> str | None:
    """Texto para o parâmetro ``help`` do Streamlit; ``None`` se a chave for desconhecida."""
    text = glossary(key)
    return text or None


def help_join(*keys: str) -> str | None:
    """Concatena definições (ex.: métrica + leitura do card)."""
    partes = [glossary(k) for k in keys]
    texto = "\n\n".join(p for p in partes if p)
    return texto or None
