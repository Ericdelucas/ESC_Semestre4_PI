# Manual executivo CTI — leitura dos cenários

Este manual alimenta o Assistente de IA do painel. A base `Cti.csv` contém cerca de **1.200 cenários** em um horizonte de **12 anos**, no perfil de concessão / infraestrutura.

## O que o painel responde

1. A operação come ou gera caixa? → **NCG** (Necessidade de Capital de Giro).
2. Dependemos de banco no curto prazo? → **Saldo de Tesouraria**.
3. Por quantos dias financiamos a operação? → **Ciclo Financeiro**.
4. Como os cenários se espalham em risco × retorno? → aba Mapeamento.
5. Qual a chance de caixa negativo no encerramento? → aba Distribuição & Probabilidades.

## Fórmulas

| Indicador | Fórmula |
|---|---|
| NCG | ACO − PCO (ativo operacional menos passivo operacional) |
| Saldo de Tesouraria | Disponível − Empréstimos de curto prazo |
| PMR | (Contas a Receber / Receita) × 365 |
| PME | (Estoques / abs(Custos)) × 365 |
| PMP | (Fornecedores / abs(Custos)) × 365 |
| Ciclo Financeiro | PMR + PME − PMP |
| Liquidez corrente | Ativo circulante / Passivo circulante |
| Rentabilidade | Resultado líquido / Receita |
| Risco | Passivo total / Ativo total |

## Selos de negócio

- Alta Rentabilidade & Alta Liquidez
- Alta Rentabilidade & Baixa Liquidez
- Retorno Moderado & Baixo Risco
- Forte Pressão de Investimentos
- Elevada Distribuição & Baixa Disponibilidade
- Encerramento com Caixa Insuficiente

## Como usar o assistente

O assistente abre em um painel retrátil à direita do dashboard (botão **🤖 Assistente CTI**). Ele consulta este manual, os demais arquivos de `documentos/` e os indicadores do cenário/filtro em foco (NCG, tesouraria e riscos).

Pergunte em linguagem de diretoria, por exemplo:

- Qual a probabilidade de caixa negativo no Ano 12?
- O que significa NCG positiva?
- Compare selos de pressão de investimento e caixa insuficiente.

Coloque PDFs e relatórios adicionais nesta pasta `documentos/` para o RAG indexá-los.
