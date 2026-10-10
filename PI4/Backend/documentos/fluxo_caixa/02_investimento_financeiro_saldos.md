# FLU — Investimento, Financeiro e Saldos

## `FLU - Investimentos`

CAPEX e aportes em ativos reversiveis/outorga.

`CAPEX = abs(FLU - Investimentos)`
`CAPEX acumulado = soma anual`

A pressao de investimentos do selo usa a media absoluta desta conta. Obrigatorio para perguntas de CAPEX.

Onde ver: Poder Concedente > Plano de CAPEX (barras anuais + linha acumulada).

## `FLU - Despesas Financeiras`

Juros pagos. Se a conta FLU estiver zerada, o utilitario pode copiar `DRE - Despesas Financeiras`.

`FCFE = (Geração de Caixa - Investimentos) - abs(Despesas Financeiras)`

## `FLU - Resultado Financeiro`

Efeito caixa consolidado do resultado financeiro. Cruze com a DRE.

## `FLU - Distribuição para Acionista`

Dividendos, JCP e demais distribuicoes. `dist_abs` do ranking. Selo Elevada Distribuicao & Baixa Disponibilidade: distribuicao no Q75 e liquidez no Q25.

No motor de acionistas: `Dividendos = max(Lucro Líquido, 0) x 35%`.

Onde ver: Acionistas > Lucro Liquido & Dividendos.

## `FLU - Saldo Inicial`

Caixa no inicio do ano. Deve encadear com o saldo final do ano anterior.

## `FLU - Saldo Final`

Caixa no fim do ano. `caixa_ano12` no ano maximo. Se residualmente zero, usa `BAL - Disponível`.

Define ruina (`caixa_ano12 < 0`), P5/P50/P95 e viabilidade terminal.

Onde ver: Distribuicao; Faixa de Risco; Comparar.
