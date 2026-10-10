# Monte Carlo e Percentis

Os cerca de **1.200 cenarios** sao trajetorias simuladas da concessao. Cada um combina premissas de receita, custos, investimentos, prazos, divida e caixa.

A leitura correta e estatistica: um ponto isolado nao define a concessao; a distribuicao dos 1.200 caminhos define o risco.

Como o modelo opera:

1. Cada cenario recebe um conjunto de premissas.
2. DRE, BAL e FLU sao recalculados ano a ano.
3. Indicadores derivados nascem das contas (NCG, tesouraria, ciclo, liquidez, ROIC, EVA, CAPEX, ruina).
4. O ranking agrega medias do horizonte e o caixa do Ano 12.
5. Os cenarios recebem um dos seis selos de negocio.

A base `Cti.csv` ja chega simulada. O painel nao sorteia novos choques em tempo real.

## Percentis

- **P5**: pior 5%. Cauda para credores, Poder Concedente e solvencia.
- **P25**: primeiro quartil, bloco pessimista acima da cauda extrema.
- **P50 / Mediana**: valor tipico. Mais robusta que a media quando ha outliers.
- **P75**: bloco otimista sem ser o extremo.
- **P95**: melhores 5%. Teto de caixa ou retorno.

Regras executivas:

- Media e mediana proximas: distribuicao mais simetrica.
- Media muito abaixo da mediana: cauda negativa.
- Distancia grande entre P5 e P95: alta volatilidade.
- P5 de caixa do Ano 12 negativo: chance material de encerrar sem caixa.
- Envelope P5–P95 cobre cerca de 90% dos caminhos anuais.

`Probabilidade de ruina = media(caixa_ano12 < 0) x 100`. O P5 mostra a magnitude do pior caixa; a probabilidade mostra a frequencia da quebra.

Nao use a media sozinha. Media positiva com P5 negativo ainda e desequilibrio.
