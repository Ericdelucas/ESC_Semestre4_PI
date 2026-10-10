# Indicadores — ROIC, ROE, WACC e EVA

## ROIC

Retorno sobre o capital investido. Teste de criacao de valor.

`aliquota = min(max(abs(DRE - IR/CS) / abs(EBIT), 0), 34%)`
`NOPAT = EBIT x (1 - aliquota)`
`Dívida Líquida = max(abs(BAL - Empréstimos) - abs(BAL - Disponível), 0)`
`Capital Investido = abs(PL) + Dívida Líquida` (fallback: Total do Ativo)
`ROIC = NOPAT / Capital Investido`

Grafico: Acionistas > Retorno & ROIC (ROIC vs ROE vs WACC).

Referencial: ROIC > 10% cria valor. Spread sustentado de 2–3 pontos e leitura confortavel.

## ROE

`ROE = DRE - Resultado Líquido / BAL - Patrimônio Líquido`

ROE alto com ROIC baixo pode ser so alavancagem.

## WACC

Ancora oficial do CTI: **10%**. Nao e recalculado por cenario. Linha de corte do grafico de ROIC e do EVA.

## EVA

`EVA = NOPAT - Capital Investido x 0.10`

Barras em Acionistas > Geracao de EVA. Positivo = valor criado; negativo = valor destruido. EVA positivo com tesouraria negativa ainda e risco de liquidez.
