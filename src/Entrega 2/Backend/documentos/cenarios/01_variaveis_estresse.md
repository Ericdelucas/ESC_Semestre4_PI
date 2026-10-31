# Cenarios — Variaveis de Estresse

Os cerca de 1.200 cenarios testam o equilibrio economico-financeiro da concessao. Cada um e uma trajetoria de 12 anos para receita, custos, investimentos, prazos, divida e caixa. O objetivo nao e um unico numero certo; e mapear a distribuicao e isolar caminhos que quebram solvencia, caixa ou criacao de valor.

A base `Cti.csv` ja chega simulada. O painel nao sorteia choques novos: recalcula indicadores, percentis, selos e comparacoes sobre as trajetorias existentes.

## Demanda e receita

`DRE - Receita` e `Receita Líquida` absorvem volume, tarifa e tributos. Choque de demanda cai sobre break-even, margem de seguranca, LTV e caixa. Receita menor com custo fixo estavel perde folga operacional primeiro.

Como identificar: Receita Liquida, Break-Even e Margem de Seguranca no CEO; depois se o EBITDA acompanhou. No comparador, Δ percentual de receita junto com Δ de EBITDA — receita que cai menos que o EBITDA indica alavancagem operacional negativa.

## Custos de insumos e OPEX

`DRE - Custos` e OPEX (`EBITDA − Margem Bruta`) representam insumos, operacao e despesas recorrentes. Inflacao de custos sem repasse tarifario comprime margem EBITDA, eleva o break-even e pode virar EVA negativo.

Como identificar: na DRE Operacional, a pilha Custos + OPEX sobre receita cresce. No ranking, rentabilidade media cai mesmo com receita ainda aceitavel.

## Inflacao, juros e estrutura financeira

Resultado financeiro, despesas financeiras, emprestimos e WACC de 10% formam o canal financeiro. Juros mais altos pesam no EBIT residual, na cobertura de juros e no EVA (`NOPAT − Capital Investido × 10%`). O modelo nao reestima WACC por cenario; o teste e se o ROIC permanece acima de 10%.

Sinais: cobertura < 1,0x, ROIC < WACC, tesouraria negativa, endividamento crescente, LG caindo a 1,0x.

## CAPEX e prazos operacionais

`FLU - Investimentos`, PMR, PME e PMP. CAPEX intenso pressiona caixa mesmo com EBITDA positivo. Alongamento de PMR ou PME aumenta NCG. PMP maior pode mascarar estresse de pagamento.

Como identificar: selo Forte Pressao de Investimentos (CAPEX medio no Q75) e trajetoria NCG x tesouraria divergente.
