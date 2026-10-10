# BAL — Imobilizado, Intangivel, Outorga e BAR

## `BAL - Investimentos - Imobilizado`

Infraestrutura fisica da concessao. Peca bruta da base reversivel. Cresce com `FLU - Investimentos`.

## `BAL - Investimentos - Intangível`

Direitos, contratos e parcela intangivel. Em concessao costuma ser relevante. Amortizacao reduz a base liquida.

## `BAL - Depreciação Acumulada`

Redutora do imobilizado. Aumenta com `DRE - Depreciação e Amortização`. Sem CAPEX de reposicao, a BAR liquida erode.

## `BAL - Amortização - Intangível`

Desgaste do intangivel/outorga no periodo. Reduz EBIT e a base intangivel.

## `BAL - Amortização Acumulada`

Estoque acumulado de amortizacao. Mostra quanto do direito da concessao ja foi consumido.

## `BAL - Outorga da Concessão`

Ativo/direito do preco ou onus para explorar o servico publico. Coracao patrimonial da concessao. Eleva ativo e BAR; a amortizacao reduz EBIT. Nao e caixa. Desembolso aparece em `FLU - Investimentos`.

Onde ver: auditoria; Ativos Reversiveis; Plano de CAPEX se houver desembolso.

## Base de Ativos Reversiveis (BAR)

Nao e linha isolada no CSV; e metrica derivada.

- Card: `BAR = abs(BAL - Total do Ativo)`
- Grafico: `abs(Imobilizado) + abs(Intangível) - abs(Depreciação Acumulada) - abs(Amortização Acumulada)`

Queda da base liquida + CAPEX baixo = envelhecimento da concessao.

Onde ver: card do Poder Concedente; aba Ativos Reversiveis.

`Base Bruta = abs(Imobilizado) + abs(Intangível)`
`Base Líquida = Base Bruta - abs(Depreciação Acumulada) - abs(Amortização Acumulada)`
