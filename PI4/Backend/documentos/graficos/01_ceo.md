# Graficos — Visao CEO

Filtros globais: cenario em foco e ano. Com ano = Todos, cards usam o horizonte; graficos temporais ainda mostram 12 anos. O marcador ancora segue o ano da sidebar.

## Visao Geral & DRE

Objetivo: mostrar como a receita se transforma em lucro e se o EBITDA acompanha a escala.

### Cascata media da DRE

Waterfall da DRE media. Parte da Receita Liquida e caminha por Custos, OPEX, EBITDA, Depreciacao, Resultado Financeiro, IR/CS e Lucro Liquido. Medidas `relative` sobem ou descem; EBITDA e Lucro sao totais ancorados.

- Verdes aumentam resultado; vermelhos reduzem; totais escuros fecham o nivel.
- Custos e OPEX entram como deltas negativos (`-abs(valor)`).
- Primeiro total (EBITDA): o que sobrou da operacao antes de D&A e financas.
- Ultimo total (Lucro Liquido): resultado final medio.

Insights: receita alta com EBITDA baixo = custos/OPEX; EBITDA alto com lucro baixo = D&A, juros ou IR; queda longa Receita→EBITDA = ineficiencia; Resultado Financeiro negativo relevante = peso da divida.

### Receita Liquida vs EBITDA (12 anos)

Duas linhas, Ano 1–12. Juntas = escala operacional. Receita sobe e EBITDA nao = compressao de margem. Queda conjunta no terminal = concessao enfraquecendo.

Cruze com margem EBITDA, break-even e CAPEX. Crescimento de receita com custo crescente nao sustenta ROIC.

## DRE Operacional

Barras empilhadas de Custos, OPEX e Depreciacao em % da Receita Liquida. A altura da pilha e a parcela absorvida antes das financas. Custos dominantes = estrutura variavel; OPEX = operacao recorrente; D&A = base de ativos pesada.

Aumento do OPEX sobre receita reduz margem EBITDA e aproxima o break-even. Confirme na tabela operacional (Receita, Custos, OPEX, EBITDA, EBIT, Lucro e margens).

## Break-Even & Margens

Ponto de equilibrio medio: receita necessaria para cobrir custos fixos dada a margem de contribuicao. Receita acima = folga; abaixo = prejuizo operacional.

Margem de seguranca: percentual de queda de receita ainda cabivel antes do equilibrio. Linha baixa ou negativa = vulneravel. Queda com receita estavel = custos fixos ou perda de contribuicao.

Em estresse de demanda, esta e a primeira aba do CEO.

## Eficiencia LTV/CAC

LTV, CAC e razao por ano. LTV deve ficar acima do CAC. Razao = multiplicador de retorno por cliente/contrato.

Se o modelo usar fallbacks (ticket 4500, retencao 10 meses, investimento 100000, 1000 clientes), declare a premissa.

Razao < 1,0x destroi valor comercial; > 3,0x indica eficiencia. Razao alta com margem de seguranca baixa = aquisicao eficiente, estrutura de custos ainda fragil.
