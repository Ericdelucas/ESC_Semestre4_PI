# Cenarios — Isolamento de Caminhos Criticos

Um cenario e critico quando ameaca inadimplencia operacional, caixa negativo ou quebra do equilibrio economico-financeiro.

Filtro pratico no painel:

1. Abrir o cenario na sidebar e ler os cards da persona.
2. Verificar `caixa_ano12` e a probabilidade de ruina do conjunto.
3. Localizar o ponto na matriz risco x retorno e o selo.
4. Confirmar liquidez corrente, liquidez geral e tesouraria.
5. Confirmar ROIC versus WACC e o sinal do EVA.
6. Confirmar CAPEX e BAR se a pergunta for regulatoria.
7. Comparar com 1 ou 2 cenarios de controle na aba Comparar (P50 e, se quiser, P95).

## Ruina de caixa

Criterio objetivo: `caixa_ano12 < 0`. Selo **Encerramento com Caixa Insuficiente**, prioridade maxima.

- Probabilidade de ruina = percentual do ranking com caixa_ano12 negativo.
- P5 do caixa do Ano 12 mostra a magnitude da cauda.
- Envelope P5–P95 mostra em que ano o caixa cruza zero com frequencia.

Nao use a media de caixa sozinha. Media positiva com P5 negativo e ruina elevada ainda e desequilibrio.

## Inadimplencia operacional

Sinais: LC < 1,0x; tesouraria negativa (`Disponível` < `Empréstimos`); ciclo alongado com NCG crescente; PMP que sobe enquanto tesouraria cai; cobertura de juros < 1,0x.

Retrato financeiro de incapacidade de honrar obrigacoes de curto prazo, nao default juridico automatico.

## Quebra do equilibrio economico-financeiro

Sinais: ROIC persistente < 10%; EVA negativo no terminal; margem de seguranca negativa; LG < 1,0x; CAPEX obrigatorio com caixa terminal negativo; selo de caixa insuficiente ou pressao de investimentos combinado com EVA negativo.

Para o Poder Concedente, o equilibrio quebra quando a concessionaria nao consegue investir, permanecer solvente e entregar o servico ate o Ano 12. Para o acionista, quando o capital nao e remunerado acima do WACC.

Onde isolar: CFO > Distribuicao (P5/P50/P95); CFO > Mapeamento (filtro de selo); Comparar da persona ativa.
