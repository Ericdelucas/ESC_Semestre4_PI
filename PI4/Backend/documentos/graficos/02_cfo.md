# Graficos — Visao CFO

## Capital de Giro

### NCG x Tesouraria (12 anos)

Duas series em R$. O usuario pode ocultar uma linha. O marcador ancora destaca o ano filtrado.

- NCG subindo: a operacao prende mais caixa.
- Tesouraria caindo ou negativa: dependencia de emprestimo de curto prazo.
- NCG alta + tesouraria baixa: aperto classico de giro.
- Ambas melhorando: a operacao gera folga.

A trajetoria importa mais que um ano isolado. Cruze com ciclo financeiro e `FLU - Geração de Caixa`.

### Composicao da NCG

ACO = contas a receber (Clientes + Partes Relacionadas + SWAP) + estoques + creditos tributarios. PCO = fornecedores + encargos + tributos a pagar. `NCG = ACO − PCO`.

ACO maior que PCO produz NCG positiva. Crescimento de ACO por recebiveis e o diagnostico mais frequente de caixa preso. Crescimento de PCO alivia, mas pode ser atraso de pagamento.

## Prazos e Ciclo

Trajetoria de PMR, PME, PMP e Ciclo Financeiro.

- PMR e PME sobem: mais capital preso.
- PMP sobe: fornecedores financiam mais a operacao.
- `Ciclo = PMR + PME − PMP`. Ciclo alongado pressiona NCG.

Se so o PMR sobe, o problema e recebimento. Se o PMP sobe com tesouraria negativa, pode ser estresse com fornecedores, nao eficiencia.

## Mapeamento de Risco x Retorno

Dispersao dos 1.200 cenarios. X = risco (Passivo/Ativo); Y = rentabilidade (Resultado/Receita); tamanho = liquidez; cor = selo.

- Superior esquerdo: melhor equilibrio (mais retorno, menos risco).
- Inferior direito: pior equilibrio.
- Pontos grandes: mais liquidez.
- Filtro por selo isola uma zona.

Alta rentabilidade com ponto pequeno = selo amarelo. Caixa insuficiente concentra-se na zona de encerramento fragil.

## Distribuicao & Probabilidades

Boxplot do caixa do Ano 12 com P5, P50 e P95. Media tambem aparece.

- P5 negativo: cauda de ruina material.
- P50: caixa tipico.
- Distancia P5–P95: volatilidade terminal.
- Probabilidade de caixa negativo: frequencia da quebra, nao so a magnitude.

Credores e Poder Concedente leem P5. Acionistas leem P50 e P95. Media puxada para baixo com mediana positiva revela assimetria negativa.

Histograma: massa a esquerda de zero = muitos cenarios em ruina; concentrada a direita = terminal mais seguro.

## Faixa de Risco

Envelope P5–P95 da metrica escolhida (NCG, tesouraria, disponivel ou geracao de caixa), com mediana e media. Cobre cerca de 90% dos caminhos. Fora da faixa = comportamento extremo. Envelope que cruza zero = anos sistematicamente criticos.

## Como Ler

Aba educacional: formulas, regras de negocio e auditoria da base. Use para metodologia, dicionario rapido ou rastreabilidade do `Cti.csv`.
