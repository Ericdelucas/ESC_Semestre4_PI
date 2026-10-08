# 01 - Visao Geral do Projeto CTI

## Objetivo Executivo

O Dashboard Financeiro CTI analisa uma concessao de servico publico em horizonte de 12 anos, combinando demonstracoes financeiras, fluxo de caixa, indicadores operacionais e simulacoes de cenarios. A base principal vem do arquivo `Cti.csv`, em formato longo, com colunas de ano, cenario, conta contabil e valor.

O objetivo do projeto e permitir que diferentes publicos leiam a mesma concessao por lentes distintas:

- CEO: desempenho economico, DRE, margens, break-even, eficiencia comercial e criacao operacional de resultado.
- CFO: capital de giro, liquidez, tesouraria, ciclo financeiro e risco de caixa.
- Acionistas: retorno sobre capital, valor economico, dividendos e comparacao risco-retorno.
- Poder Concedente: cumprimento de investimentos, solvencia, ativos reversiveis e sustentabilidade da concessao.

## Escopo da Concessao

O projeto CTI acompanha a sustentabilidade economico-financeira de uma concessao, avaliando se a operacao gera caixa, cumpre investimentos, preserva liquidez, remunera capital e mantem capacidade de cumprir obrigacoes contratuais.

A leitura do painel nao deve se limitar a uma metrica isolada. Uma boa analise combina:

- Rentabilidade operacional.
- Capacidade de caixa.
- Pressao de capital de giro.
- Necessidade de CAPEX.
- Solvencia de curto e longo prazo.
- Criacao de valor para acionistas.
- Risco de encerramento com caixa insuficiente.

## Estrutura dos Dados

O projeto usa tres familias de contas:

- DRE: contas de resultado, como Receita, Custos, EBITDA, EBIT, Resultado Financeiro, Imposto de Renda e Resultado Liquido.
- BP/BAL: contas patrimoniais, como Ativo Circulante, Passivo Circulante, Disponivel, Estoques, Fornecedores, Emprestimos, Patrimonio Liquido e Total do Ativo.
- DFC/FLU: fluxo de caixa, como Geracao de Caixa, Investimentos, Distribuicao para Acionista e Saldo Final.

## Os 1.200 Cenarios

O painel trabalha com 1.200 cenarios simulados. Cada cenario representa uma trajetoria possivel para receita, custos, caixa, investimentos, endividamento, rentabilidade e risco.

A leitura correta nao depende apenas de um valor pontual. Ela combina:

- Valor medio.
- Dispersao entre cenarios.
- Probabilidade de caixa negativo.
- Caixa no ano de encerramento.
- Selo de risco/negocio.
- Comparacao temporal entre cenarios.

## Regras Gerais de Negocio

O assistente CTI deve sempre conectar perguntas conceituais com a estrutura real do projeto:

- CAPEX no dashboard usa principalmente `FLU - Investimentos`.
- EBITDA e margens sao lidos pela DRE.
- NCG, tesouraria e ciclo financeiro conectam BP e DRE.
- ROIC, WACC e EVA avaliam criacao de valor.
- Liquidez corrente e liquidez geral avaliam solvencia por horizontes diferentes.
- Selos de negocio resumem comportamento de risco e retorno dos cenarios.

Quando responder a perguntas, o assistente deve explicar o conceito perguntado, conectar com a conta ou formula usada no CTI, interpretar os graficos associados e sugerir a aba exata no final.
