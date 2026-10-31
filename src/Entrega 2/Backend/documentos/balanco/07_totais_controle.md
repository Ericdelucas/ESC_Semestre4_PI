# BAL — Totais de Controle

## `BAL - Total do Ativo`

Soma do ativo. Controle patrimonial e proxy da BAR no card (`BAR = abs(Total do Ativo)`).

Deve fechar com o lado direito na identidade contabil.

Usa-se como:

- denominador do risco: `Total do Passivo / Total do Ativo`
- denominador do ROA: `DRE - Resultado Líquido / Total do Ativo`
- fallback do capital investido quando PL + divida liquida <= 0

Onde ver: card BAR; matriz risco x retorno; auditoria.

## `BAL - Total do Passivo`

Total do lado do passivo / exigibilidades usadas no risco.

`Risco = abs(Total do Passivo) / abs(Total do Ativo)`

Valor proximo do ativo total = equity residual. Endividamento complementar:

`(Passivo Circulante + Exigível a Longo Prazo) / Total do Ativo`

Onde ver: matriz risco x retorno; Solvencia (endividamento).
