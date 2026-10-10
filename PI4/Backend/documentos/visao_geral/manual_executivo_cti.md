# Manual executivo CTI

A base `Cti.csv` contém cerca de **1.200 cenários** em um horizonte de **12 anos**, no perfil de concessão / infraestrutura.

## O que o painel responde

1. A operação come ou gera caixa? → **NCG**.
2. Dependemos de banco no curto prazo? → **Saldo de Tesouraria**.
3. Por quantos dias financiamos a operação? → **Ciclo Financeiro**.
4. Como os cenários se espalham em risco × retorno? → aba Mapeamento.
5. Qual a chance de caixa negativo no encerramento? → aba Distribuição.

## Fórmulas-resumo

| Indicador | Fórmula |
|---|---|
| NCG | ACO − PCO |
| Tesouraria | Disponível − Empréstimos CP |
| PMR / PME / PMP | Recebíveis/Receita, Estoques/Custos, Fornecedores/Custos × 365 |
| Ciclo Financeiro | PMR + PME − PMP |
| Liquidez corrente | Ativo circulante / Passivo circulante |
| Rentabilidade | Resultado líquido / Receita |
| Risco | Passivo total / Ativo total |

## Selos

Alta Rentabilidade & Alta Liquidez; Alta Rentabilidade & Baixa Liquidez; Retorno Moderado & Baixo Risco; Forte Pressão de Investimentos; Elevada Distribuição & Baixa Disponibilidade; Encerramento com Caixa Insuficiente.

O assistente consulta os arquivos de `PI4/Backend/documentos/` (incluindo subpastas) e os indicadores do recorte. PDFs extras nessa árvore também entram no RAG.
