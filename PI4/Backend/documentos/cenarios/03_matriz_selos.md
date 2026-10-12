# Cenarios — Matriz e Seis Selos

Cada cenario recebe um unico selo. A classificacao usa quartis do ranking e ordem de prioridade. O primeiro criterio verdadeiro vence.

## Zona 1 — Encerramento com Caixa Insuficiente

`caixa_ano12 < 0`. Zona de ruina. Prioridade sobre todos os demais. Acao: magnitude do deficit, ano em que o envelope cruza zero, CAPEX residual e distribuicao a acionistas que possa ter antecipado a quebra.

## Zona 2 — Forte Pressao de Investimentos

CAPEX medio (`abs(FLU - Investimentos)`) >= Q75. Pode haver lucro com caixa pressionado. Acao: Plano de CAPEX, tesouraria e LG. Verificar se o investimento cria ROIC futuro ou so consome caixa.

## Zona 3 — Elevada Distribuicao & Baixa Disponibilidade

Distribuicao a acionistas >= Q75 e liquidez acumulada <= Q25. O projeto remunera o acionista acima do que o caixa comporta. Payout de 35% sobre lucro positivo pode ser excessivo. Acao: Lucro Liquido & Dividendos, tesouraria e ruina.

## Zona 4 — Alta Rentabilidade & Alta Liquidez

Rentabilidade >= Q75 e LC >= Q75. Melhor zona. Usar como referencia em A/B/C e confirmar ROIC > WACC e cumprimento de CAPEX — alta liquidez nao dispensa leitura regulatoria.

## Zona 5 — Alta Rentabilidade & Baixa Liquidez

Rentabilidade >= Q75 e LC <= Q25. Zona amarela. Resultado forte, caixa fragil. Classico com NCG alta, CAPEX pesado ou PMR longo. Nao celebrar a margem; abrir Capital de Giro e Faixa de Risco.

## Zona 6 — Retorno Moderado & Baixo Risco

Rentabilidade entre Q25 e Q75 e risco (Passivo/Ativo) <= Q25. Tambem e o default residual. Menos upside, menos alavancagem. Estabilidade patrimonial nao garante criacao de valor se o ROIC ficar abaixo de 10%.

## Matriz visual

- X: risco (Passivo/Ativo). Direita = mais alavancado.
- Y: rentabilidade (Resultado/Receita). Cima = mais retorno.
- Tamanho: liquidez. Ponto pequeno = aperto.
- Cor: selo/zona.

Poder Concedente prioriza zonas 1–2 e LG. CFO prioriza 1, 3 e 5. Acionista compara 4 vs 6 pelo spread ROIC − WACC. CEO mistura ruina e margem.

Ao analisar um cenario: citar id, ano, selo, numeros do recorte e graficos. Evitar veredito absoluto sem percentil, comparavel ou caixa do Ano 12.
