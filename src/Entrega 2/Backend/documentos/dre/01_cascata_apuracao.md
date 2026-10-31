# DRE — Cascata de Apuracao

Sinais da base importam: custos, tributos, depreciacao e IR frequentemente entram negativos.

Encadeamento oficial do motor `build_dre`:

1. `Receita Líquida = DRE - Receita + DRE - Tributos`
2. `Margem Bruta = Receita Líquida + DRE - Custos`
3. `OPEX = DRE - EBITDA - Margem Bruta`
4. `EBIT = DRE - Resultado Operacional`
5. `Resultado Financeiro = DRE - Resultado Financeiro`
6. `EBT / LAIR = DRE - Resultado Antes do Imposto de Renda`
7. `IR/CS = DRE - Imposto de Renda e Contribuição Social`
8. `Lucro Líquido = DRE - Resultado Líquido`

Fallback do lucro se o informado for residualmente zero:

`Lucro Líquido = EBIT + Resultado Financeiro + IR/CS`

Aliquota efetiva do ROIC: `min(max(abs(IR/CS) / abs(EBIT), 0), 34%)`.

Onde ver a cascata: CEO > Visao Geral & DRE (waterfall media). Custos e OPEX entram como deltas negativos. EBITDA e Lucro Liquido sao totais ancorados.

Leitura: receita alta com EBITDA baixo = pressao de custos/OPEX; EBITDA alto com lucro baixo = D&A, juros ou IR.
