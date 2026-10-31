# Graficos — Visao Poder Concedente

## Plano de CAPEX

Barras de CAPEX anual (`CAPEX = abs(FLU - Investimentos)`) e linha de CAPEX acumulado. `CAPEX / Receita Líquida` mede o peso do investimento sobre a operacao.

- Barras: intensidade em cada ano.
- Linha: cumprimento progressivo do plano de infraestrutura.

Pico de barras com tesouraria caindo = estresse classico de implantacao. Linha acumulada estagnada com BAR em queda = subinvestimento.

Aba obrigatoria para perguntas sobre CAPEX, investimentos e infraestrutura. Selo Forte Pressao de Investimentos usa a media absoluta desta conta no Q75.

## Solvencia & Liquidez Geral

Linha de liquidez geral com referencia tracejada em **1,0x**. Tabela de LG, endividamento e cobertura de juros.

`LG = (Ativo Circulante + Realizável a Longo Prazo) / (Passivo Circulante + Exigível a Longo Prazo)`

- Abaixo de 1,0x: alerta de solvencia de longo prazo.
- Queda continuada em direcao a 1,0x: deterioracao estrutural.
- Cobertura de juros `EBIT / abs(DRE - Despesas Financeiras)` < 1,0x: EBIT nao cobre juros.
- Endividamento alto: passivo consome a base de ativos.

O Poder Concedente nao se contenta com liquidez corrente. A concessao precisa honrar obrigacoes de curto e longo prazo ao longo dos 12 anos. Inclui `BAL - Obrigações com o Poder Concedente`.

## Ativos Reversiveis

Area da Base Liquida versus depreciacao/amortizacao acumulada.

`Base Bruta = abs(Imobilizado) + abs(Intangível)`
`Base Líquida = Base Bruta − abs(Depreciação Acumulada) − abs(Amortização Acumulada)`

Card BAR = `abs(BAL - Total do Ativo)`. Grafico usa a base liquida acima.

A base liquida e o patrimonio afetado ao servico. Se cai e o CAPEX nao reconstroi, a concessao envelhece. Combine com o card de Ativo Total e com o plano de CAPEX.

BAR robusta com LG < 1,0x ainda e risco: ha ativo, mas ha passivo demais. Leia tambem `BAL - Outorga da Concessão`.
