# Constantes do Modelo e Leitura Integrada

Constantes oficiais do painel:

- WACC de referencia: **10%**
- Payout de dividendos: **35%** do lucro liquido positivo
- Aliquota de IR teto: **34%**

Aliases da base: `BAL - Emprést` = `BAL - Empréstimos`; `BAL - Outros deb` = `BAL - Outros Débitos`; `BAL - Impostos` convive com `BAL - Tributos a pagar`.

## Formulas-base de giro e solvencia

- `ACO = Contas a Receber + Estoques + Creditos Tributarios`
- `PCO = Fornecedores + Encargos Sociais + Tributos a Pagar`
- `NCG = ACO - PCO`
- `Saldo de Tesouraria = Disponivel - Emprestimos`
- `PMR = Contas a Receber / Receita x 365`
- `PME = Estoques / abs(Custos) x 365`
- `PMP = Fornecedores / abs(Custos) x 365`
- `Ciclo Financeiro = PMR + PME - PMP`
- `Liquidez Corrente = Ativo Circulante / Passivo Circulante`
- `Liquidez Geral = (Ativo Circulante + Realizavel LP) / (Passivo Circulante + Exigivel LP)`
- `Risco = Total do Passivo / Total do Ativo`
- `Rentabilidade = Resultado Liquido / Receita`

## Ordem executiva de leitura

1. Identificar cenario, ano e persona.
2. Ler os cards do topo.
3. Verificar DRE e margens.
4. Cruzar NCG, tesouraria e ciclo.
5. Confrontar ROIC, WACC e EVA.
6. Conferir CAPEX, liquidez geral e ativos reversiveis.
7. Olhar a distribuicao dos 1.200 cenarios e a ruina no Ano 12.
8. Se houver duvida, usar Comparar A/B/C com deltas.

A DRE diz se a operacao gera resultado. O BAL diz se patrimonio e divida sustentam a concessao. O FLU diz se sobra caixa depois de CAPEX e distribuicao. EBITDA positivo nao impede quebra no Ano 12 se CAPEX, NCG ou dividendos consumirem o caixa.
