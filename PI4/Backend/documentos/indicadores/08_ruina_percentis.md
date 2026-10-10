# Indicadores — Ruina e Cauda P5/P95

`caixa_ano12 = FLU - Saldo Final` no Ano 12 (fallback `BAL - Disponível`)

`Probabilidade de ruína = média(caixa_ano12 < 0) × 100`

Percentis P5, P25, P50, P75 e P95 da distribuicao de caixa (e do envelope anual). Envelope P5–P95 cobre cerca de 90% dos caminhos.

Referencial: ruina 0%–5% controlada; > 15% alerta; P5 negativo = cauda material.

Nao use a media sozinha. Media positiva com P5 negativo ainda e desequilibrio.

Onde ver: CFO > Distribuicao (boxplot e histograma); CFO > Faixa de Risco (envelope).
