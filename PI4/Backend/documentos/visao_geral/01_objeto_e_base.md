# Objeto da Concessao e Base CTI

O Dashboard Financeiro CTI analisa uma concessao de servico publico de infraestrutura. O objeto e a prestacao continuada de um servico essencial, com ativos de longo prazo, outorga, intangivel, endividamento e obrigacoes perante o Poder Concedente.

O capital fica imobilizado em infraestrutura reversivel. O caixa depende de receita tarifaria ou contratual. O equilibrio economico-financeiro precisa sobreviver a choques de demanda, custos e inflacao ao longo de mais de uma decada.

Horizonte oficial: **12 anos** (Ano 1 a Ano 12). O Ano 12 e o ponto de encerramento para ruina de caixa, caixa final e solvencia terminal.

Base primaria: `Cti.csv`, formato longo.

| Coluna | Conteudo |
|---|---|
| `ANO` | Ano do horizonte (`Ano 1` a `Ano 12`) |
| `CENA` | Cenario simulado (`Total Cen_00001` a cerca de `Total Cen_01200`) |
| `CONTA` | Rubrica BAL, DRE ou FLU |
| `VALOR` | Montante em reais |

Volume tipico: 1.200 cenarios x 12 anos x dezenas de contas. Nao e um unico balanco historico; e um laboratorio de planejamento.

Tres familias de contas:

- **DRE**: receita, tributos, custos, EBITDA, D&A, EBIT, resultado financeiro, IR/CS, lucro.
- **BAL**: circulante, realizavel LP, imobilizado/intangivel/outorga, passivo, exigivel LP, PL e totais.
- **FLU**: geracao de caixa, investimentos (CAPEX), distribuicao e saldos.

Contas tipicas de concessao: `BAL - Outorga da Concessão`, `BAL - Obrigações com o Poder Concedente`, intangivel e BAR.

A auditoria do cabecalho lista qualquer `CONTA` x `VALOR` do cenario e ano filtrados.
