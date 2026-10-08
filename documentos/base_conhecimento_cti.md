# Base de Conhecimento CTI

## Visao Geral do Projeto de Concessao CTI

O Dashboard Financeiro CTI analisa uma concessao de servico publico em horizonte de 12 anos, combinando demonstracoes financeiras, fluxo de caixa, indicadores operacionais e simulacoes de cenarios. A base principal vem do arquivo `Cti.csv`, em formato longo, com as colunas de ano, cenario, conta contabil e valor.

O objetivo do projeto e permitir que diferentes publicos leiam a mesma concessao por lentes distintas:

- CEO: desempenho economico, DRE, margens, break-even, eficiencia comercial e criacao operacional de resultado.
- CFO: capital de giro, liquidez, tesouraria, ciclo financeiro e risco de caixa.
- Acionistas: retorno sobre capital, valor economico, dividendos e comparacao risco-retorno.
- Poder Concedente: cumprimento de investimentos, solvencia, ativos reversiveis e sustentabilidade da concessao.

O painel trabalha com 1.200 cenarios simulados. Cada cenario representa uma trajetoria possivel para receita, custos, caixa, investimentos, endividamento, rentabilidade e risco. A leitura correta nao depende apenas de um valor pontual: ela combina valor medio, dispersao, probabilidade de caixa negativo, selo de risco e comparacao entre cenarios.

## Demonstracoes e Estrutura dos Dados

O projeto usa tres familias de contas:

- DRE: contas de resultado, como Receita, Custos, EBITDA, EBIT, Resultado Financeiro, Imposto de Renda e Resultado Liquido.
- BP/BAL: contas patrimoniais, como Ativo Circulante, Passivo Circulante, Disponivel, Estoques, Fornecedores, Emprestimos, Patrimonio Liquido e Total do Ativo.
- DFC/FLU: fluxo de caixa, como Geracao de Caixa, Investimentos, Distribuicao para Acionista e Saldo Final.

Quando responder a perguntas, o assistente deve explicar o conceito perguntado, conectar com a conta ou formula usada no CTI, interpretar os graficos associados e, ao final, sugerir a aba exata do dashboard.

## Dicionario de Indicadores

### Receita Liquida

Receita Liquida representa a receita operacional apos deducoes comerciais, tributos ou ajustes aplicaveis. No CTI, ela e a base de comparacao para margens e eficiencia.

Formula geral: Receita Liquida = Receita Bruta - Deducoes.

Aplicacao: avalia escala operacional, crescimento e capacidade de absorver custos, OPEX, CAPEX e despesas financeiras.

Graficos associados: na visao CEO, aparece em Receita Liquida vs EBITDA e na Cascata media da DRE.

### EBITDA

EBITDA e o resultado operacional antes de juros, impostos, depreciacao e amortizacao. Ele mede a geracao operacional de resultado antes de efeitos financeiros e nao caixa.

Formula conceitual: EBITDA = Receita Liquida - Custos Operacionais - Despesas Operacionais antes de depreciacao/amortizacao.

Aplicacao no CTI: indica a forca operacional da concessao e ajuda a comparar cenarios sem misturar efeitos de financiamento, impostos e depreciacao.

Graficos associados: CEO > Visao Geral & DRE mostra Cascata media da DRE e Receita Liquida vs EBITDA. CEO > DRE Operacional mostra margens, composicao operacional e tabela com EBITDA, EBIT e lucro.

### Margem EBITDA

Margem EBITDA mede quanto da receita se converte em EBITDA.

Formula: Margem EBITDA = EBITDA / Receita Liquida.

Aplicacao: mostra eficiencia operacional. Margem alta indica melhor capacidade de transformar receita em resultado operacional.

Graficos associados: CEO > DRE Operacional apresenta margens operacionais e composicao de custos sobre receita.

### EBIT

EBIT e o resultado antes de juros e impostos, ja considerando depreciacao e amortizacao.

Formula: EBIT = EBITDA - Depreciacao - Amortizacao.

Aplicacao: mostra resultado operacional contabil, importante para ROIC, cobertura de juros e analise de rentabilidade.

Graficos associados: CEO > DRE Operacional e Poder Concedente > Solvencia & Liquidez Geral.

### Resultado Liquido

Resultado Liquido e o lucro apos resultado financeiro, impostos e demais efeitos.

Formula geral: Resultado Liquido = Resultado Operacional + Resultado Financeiro - Impostos + Outros Resultados.

Aplicacao: usado para avaliar distribuicao de dividendos, reinvestimento, margem liquida e sustentabilidade ao acionista.

Graficos associados: Acionistas > Lucro Liquido & Dividendos.

### Break-Even

Break-Even e o ponto de equilibrio: nivel de receita necessario para cobrir custos e nao gerar prejuizo operacional.

Formula conceitual: Break-Even = Custos Fixos / Margem de Contribuicao.

Aplicacao no CTI: mede a folga entre receita projetada e receita minima necessaria para sustentar a operacao. Quanto maior a distancia positiva entre receita e break-even, maior a margem de seguranca.

Graficos associados: CEO > Break-Even & Margens mostra a linha de Receita Total, Custos Totais e o ponto de equilibrio medio, alem da evolucao da margem de seguranca.

### Margem de Contribuicao

Margem de Contribuicao mede quanto sobra da receita depois dos custos variaveis para cobrir custos fixos e formar resultado.

Formula: Margem de Contribuicao = (Receita Liquida - Custos Variaveis) / Receita Liquida.

Aplicacao: entra diretamente no calculo do Break-Even.

Graficos associados: CEO > Break-Even & Margens.

### Margem de Seguranca

Margem de Seguranca mede quanto a receita pode cair antes de atingir o ponto de equilibrio.

Formula: Margem de Seguranca = (Receita Liquida - Break-Even) / Receita Liquida.

Aplicacao: indica resiliencia operacional. Margem baixa sinaliza risco de prejuizo se houver queda de receita ou aumento de custos.

Graficos associados: CEO > Break-Even & Margens.

### CAPEX

CAPEX significa Capital Expenditure, ou investimentos em bens de capital e infraestrutura.

No CTI, o CAPEX e representado principalmente pela conta `FLU - Investimentos`.

Formula operacional no painel: CAPEX = valor absoluto de FLU - Investimentos. CAPEX Acumulado = soma acumulada anual do CAPEX.

Aplicacao: mostra o volume de investimentos exigidos para manter, ampliar ou cumprir obrigações de infraestrutura da concessao.

Graficos associados: Poder Concedente > Plano de CAPEX mostra CAPEX anual em barras e CAPEX acumulado em linha. A leitura compara pressao de investimento ao longo do tempo e a trajetoria acumulada do plano.

### OPEX

OPEX representa despesas operacionais recorrentes.

Formula conceitual: OPEX = despesas de operacao, manutencao, administrativas e outras despesas recorrentes.

Aplicacao: afeta EBITDA, margem operacional e ponto de equilibrio.

Graficos associados: CEO > DRE Operacional mostra composicao operacional sobre Receita Liquida, incluindo custos, OPEX e depreciacao.

### NCG

NCG significa Necessidade de Capital de Giro.

Formula: NCG = ACO - PCO, em que ACO sao ativos circulantes operacionais e PCO sao passivos circulantes operacionais.

Aplicacao: mede quanto recurso fica preso no ciclo operacional. NCG positiva elevada pressiona caixa; NCG menor melhora liquidez operacional.

Graficos associados: CFO > Capital de Giro mostra NCG, Saldo de Tesouraria e dinamica do capital de giro.

### Saldo de Tesouraria

Saldo de Tesouraria mede a folga financeira de curto prazo.

Formula: Saldo de Tesouraria = Disponivel - Emprestimos de Curto Prazo.

Aplicacao: indica se a empresa depende de financiamento de curto prazo para sustentar operacoes.

Graficos associados: CFO > Capital de Giro e CFO > Faixa de Risco.

### Ciclo Financeiro

Ciclo Financeiro mede o tempo em dias entre pagar fornecedores, manter estoque e receber clientes.

Formula: Ciclo Financeiro = PMR + PME - PMP.

PMR = Contas a Receber / Receita x 365.
PME = Estoques / abs(Custos) x 365.
PMP = Fornecedores / abs(Custos) x 365.

Aplicacao: ciclo maior tende a aumentar NCG e pressionar caixa.

Graficos associados: CFO > Prazos e Ciclo mostra PMR, PME, PMP e ciclo financeiro.

### Liquidez Corrente

Liquidez Corrente mede capacidade de pagar obrigacoes de curto prazo.

Formula: Liquidez Corrente = Ativo Circulante / Passivo Circulante.

Aplicacao: valor abaixo de 1,0x sinaliza possivel pressao de curto prazo.

Graficos associados: CFO > Faixa de Risco e CFO > Distribuicao.

### Liquidez Geral

Liquidez Geral mede solvencia incluindo ativos e passivos de longo prazo.

Formula: Liquidez Geral = (Ativo Circulante + Realizavel a Longo Prazo) / (Passivo Circulante + Exigivel a Longo Prazo).

Aplicacao: na visao do Poder Concedente, avalia capacidade de cumprir obrigacoes contratuais ao longo da concessao.

Graficos associados: Poder Concedente > Solvencia & Liquidez Geral.

### ROIC

ROIC significa Retorno sobre o Capital Investido.

Formula: ROIC = NOPAT / Capital Investido.

NOPAT = Resultado Operacional apos impostos operacionais. Capital Investido pode ser aproximado por Patrimonio Liquido + Divida Liquida, ou por base de ativos quando a estrutura exigir.

Aplicacao: mede eficiencia na geracao de retorno sobre o capital aplicado na concessao. ROIC acima do WACC indica criacao de valor economico.

Graficos associados: Acionistas > Retorno & ROIC mostra ROIC, ROE e WACC ao longo do tempo.

### ROE

ROE significa Retorno sobre o Patrimonio Liquido.

Formula: ROE = Lucro Liquido / Patrimonio Liquido.

Aplicacao: mede retorno do acionista sobre capital proprio.

Graficos associados: Acionistas > Retorno & ROIC.

### WACC

WACC e o Custo Medio Ponderado de Capital.

Formula conceitual: WACC = custo da divida apos impostos ponderado pela participacao da divida + custo do capital proprio ponderado pela participacao do patrimonio.

Aplicacao: serve como taxa minima de atratividade. Quando ROIC supera WACC, o projeto tende a criar valor.

Graficos associados: Acionistas > Retorno & ROIC compara ROIC, ROE e WACC.

### EVA

EVA significa Economic Value Added, ou Valor Economico Agregado.

Formula: EVA = NOPAT - (Capital Investido x WACC).

Aplicacao: mede lucro economico depois do custo de capital. EVA positivo indica criacao de valor.

Graficos associados: Acionistas > Geracao de EVA mostra EVA ano a ano.

### Dividendos e Retencao

Dividendos representam parcela do lucro distribuida ao acionista. Retencao representa lucro reinvestido ou mantido na empresa.

Formula conceitual: Dividendos = Lucro Liquido x Payout. Retido = Lucro Liquido - Dividendos.

Aplicacao: avalia equilibrio entre remuneracao do acionista e capacidade de financiar crescimento, CAPEX e liquidez.

Graficos associados: Acionistas > Lucro Liquido & Dividendos.

### LTV, CAC e LTV/CAC

LTV mede valor economico esperado de clientes ou contratos. CAC mede custo de aquisicao. A razao LTV/CAC mede eficiencia comercial.

Formula: LTV/CAC = LTV / CAC.

Aplicacao: razao maior indica que o valor gerado supera o custo de captacao. No CTI, essa leitura apoia a eficiencia comercial e a sustentabilidade de crescimento.

Graficos associados: CEO > Eficiencia LTV/CAC mostra LTV, CAC e a razao LTV/CAC por ano.

## Abas e Visualizacoes do Dashboard

### CEO

CEO > Visao Geral & DRE:

- Cascata media da DRE: mostra como Receita Liquida evolui para EBITDA, EBIT e Lucro Liquido apos custos, OPEX, depreciacao, resultado financeiro e impostos.
- Receita Liquida vs EBITDA: compara escala de receita e geracao operacional ao longo dos anos.

Como ler: se receita cresce mas EBITDA nao acompanha, ha pressao de custos ou perda de margem. Se EBITDA cresce junto com receita, ha ganho operacional.

CEO > DRE Operacional:

- Composicao operacional sobre Receita Liquida: mostra participacao de custos, OPEX e depreciacao na receita.
- Tabela operacional: consolida Receita, Custos, OPEX, EBITDA, EBIT, Lucro Liquido e margens.

Como ler: aumentos relativos em custos ou OPEX reduzem margem EBITDA e podem aproximar a operacao do break-even.

CEO > Break-Even & Margens:

- Grafico de ponto de equilibrio: compara Receita Total e Custos Totais.
- Margem de seguranca: mostra folga operacional ao longo do horizonte.

Como ler: quanto maior a receita acima do break-even, menor o risco operacional.

CEO > Eficiencia LTV/CAC:

- Grafico LTV vs CAC por ano.
- Cards de LTV medio, CAC medio e razao LTV/CAC.

Como ler: LTV/CAC maior sugere eficiencia comercial; razoes muito baixas indicam que adquirir clientes ou demanda custa mais do que gera.

### CFO

CFO > Capital de Giro:

- Evolucao NCG x Tesouraria.
- Composicao da NCG.

Como ler: NCG alta com tesouraria baixa indica pressao de financiamento operacional.

CFO > Prazos e Ciclo:

- PMR, PME, PMP e Ciclo Financeiro.

Como ler: PMR e PME maiores aumentam capital preso; PMP maior pode aliviar caixa, mas pode sinalizar alongamento de fornecedores.

CFO > Mapeamento de Risco:

- Dispersao risco x retorno.
- Selos de negocio e filtro por classificacao.

Como ler: cenarios com alto retorno e alta liquidez sao preferiveis; cenarios com caixa insuficiente ou alta pressao de investimento exigem atencao.

CFO > Distribuicao:

- Histograma e boxplot de indicadores, como liquidez final e percentis.

Como ler: avalia dispersao entre cenarios e probabilidade de resultados extremos.

CFO > Faixa de Risco:

- Envelope de probabilidade por ano.
- Histograma por ano.

Como ler: mostra concentracao e volatilidade dos resultados em cada ano.

CFO > Como Ler:

- Aba educacional com formulas, regras de negocio e orientacao de leitura.

CFO > Comparar:

- Comparativo entre cenarios selecionados.
- Linhas temporais e cards comparativos.

Como ler: serve para comparar trajetorias de caixa, NCG, tesouraria, liquidez, ciclo e rentabilidade.

### Acionistas

Acionistas > Retorno & ROIC:

- Grafico ROIC vs ROE vs WACC.

Como ler: ROIC acima do WACC indica criacao de valor. ROE mostra retorno do capital proprio. Se ROIC cai abaixo do WACC, o projeto destrói valor economico.

Acionistas > Geracao de EVA:

- Grafico de EVA ano a ano.

Como ler: barras positivas indicam valor criado acima do custo de capital; barras negativas indicam destruicao de valor.

Acionistas > Lucro Liquido & Dividendos:

- Grafico de Lucro Liquido, Dividendos e Retencao.
- Tabela com lucro, dividendos, retido e dividend yield.

Como ler: avalia o equilibrio entre remunerar acionistas e preservar caixa para reinvestimento e CAPEX.

### Poder Concedente

Poder Concedente > Plano de CAPEX:

- Barras de CAPEX anual.
- Linha de CAPEX acumulado.

Como ler: barras mostram intensidade de investimento em cada ano; a linha acumulada mostra cumprimento progressivo do plano de infraestrutura.

Poder Concedente > Solvencia & Liquidez Geral:

- Linha de Liquidez Geral com referencia minima.
- Tabela de liquidez, endividamento e cobertura de juros.

Como ler: liquidez geral abaixo de 1,0x pode indicar fragilidade para cumprir obrigacoes contratuais e financeiras.

Poder Concedente > Ativos Reversiveis:

- Area de base liquida de ativos e depreciacao/amortizacao acumulada.

Como ler: mostra patrimonio afetado ao servico publico e sua perda de valor contabil ao longo do tempo.

## Como Analisar os 1.200 Cenarios

Os 1.200 cenarios representam simulacoes possiveis da concessao. Para analisa-los:

1. Identifique o cenario em foco e o ano selecionado.
2. Leia os cards principais da persona ativa.
3. Verifique se o cenario tem caixa final suficiente no Ano 12.
4. Compare rentabilidade, liquidez, risco, NCG e tesouraria.
5. Use os selos de negocio para classificar o comportamento:
   - Alta Rentabilidade & Alta Liquidez: cenario forte.
   - Alta Rentabilidade & Baixa Liquidez: retorno bom com pressao de caixa.
   - Retorno Moderado & Baixo Risco: estabilidade com menor retorno.
   - Forte Pressao de Investimentos: CAPEX intenso pressiona caixa.
   - Elevada Distribuicao & Baixa Disponibilidade: payout ou distribuicao podem fragilizar liquidez.
   - Encerramento com Caixa Insuficiente: risco de sustentabilidade financeira.
6. Use as abas de comparacao para confrontar cenarios alternativos.

## Padrao de Resposta do Assistente CTI

Quando o usuario perguntar sobre uma metrica, grafico ou decisao, o assistente deve responder nesta ordem:

1. Explicacao direta do conceito.
2. Formula ou logica de calculo usada no CTI.
3. Impacto pratico no projeto de concessao.
4. Aba e graficos associados, explicando como ler cada visualizacao.
5. Valores do recorte atual quando disponiveis.
6. Sugestao de navegacao no final.

O assistente nao deve responder apenas com um botao ou atalho. O atalho e complemento, nao substituto da explicacao.
