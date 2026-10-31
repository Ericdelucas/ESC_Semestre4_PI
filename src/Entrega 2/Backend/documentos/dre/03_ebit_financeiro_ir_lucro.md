# DRE — EBIT, Financeiro, IR e Lucro

## `DRE - Depreciação e Amortização`

Efeito nao caixa de imobilizado, intangivel e outorga. Reduz EBITDA ate o EBIT. Entra nos custos fixos do break-even. Concessao recem-investida tem D&A alta e margem EBIT menor que margem EBITDA.

## `DRE - Resultado Operacional`

EBIT. Base de NOPAT, ROIC, EVA e cobertura de juros do concedente (`EBIT / abs(Despesas Financeiras)`).

`Margem EBIT = EBIT / Receita Líquida`.

Onde ver: DRE Operacional; Acionistas; Solvencia.

## `DRE - Outros Resultados Operacionais`

Itens operacionais fora da linha principal. Entram nos custos fixos do break-even.

## `DRE - Receitas Financeiras` e `DRE - Despesas Financeiras`

Juros ativos e juros da divida. A despesa financeira entra nos custos fixos e no DSCR (`EBITDA / abs(Despesas Financeiras)` no catalogo).

## `DRE - Resultado Financeiro`

Consolidacao financeira usada na cascata e no fallback do lucro. Negativo persistente = peso da divida.

## `DRE - Resultado Antes do Imposto de Renda`

LAIR / EBT. Base tributaria.

## `DRE - Imposto de Renda e Contribuição Social`

IR e CSLL. Aliquota do ROIC limitada a 34%.

## `DRE - Resultado Líquido`

Lucro do exercicio. Alimenta ROE, margem liquida, rentabilidade da matriz e dividendos (`max(Lucro, 0) x 35%`).

## `DRE - Resultado Líquido após Equivalência`

Resultado apos equivalencia patrimonial. Use o Resultado Liquido padrao nos KPIs oficiais; esta linha quando a pergunta for participacoes.

Onde ver: cascata (total final); Acionistas > Lucro Liquido & Dividendos; auditoria.
