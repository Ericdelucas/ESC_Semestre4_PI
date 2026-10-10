# BAL — Ativo Circulante

Grupo de ativos realizaveis no curto prazo. Numerador da Liquidez Corrente e da Liquidez Geral.

## `BAL - Ativo Circulante`

Agrupador do disponivel, recebiveis, estoques, creditos tributarios e outros creditos de CP. Queda do AC com PC estavel aperta a solvencia de curto prazo.

Onde ver: auditoria; card/Faixa de Risco (LC); Solvencia (LG).

## `BAL - Disponível`

Caixa e equivalentes. Se `FLU - Saldo Final` for residualmente zero, vira caixa de encerramento.

Entra em Tesouraria (`Disponível - Empréstimos`), Liquidez Imediata (`Disponível / Passivo Circulante`) e ruina.

Onde ver: Capital de Giro; Distribuicao; Faixa de Risco.

## Recebiveis

- `BAL - Contas a Receber - Clientes`: tarifas/contraprestacoes. Peca principal do PMR e do ACO.
- `BAL - Contas a Receber - Partes Relacionadas`: creditos intra-grupo. Entra no ACO; pode inflar AC sem ser usuario final.
- `BAL - Contas a Receber - SWAP`: hedge. Oscila NCG sem ser demanda da concessao.

No ranking, o PMR usa a soma dos tres recebiveis. No catalogo analitico, o PMR usa so Clientes: `CR Clientes / DRE - Receita x 365`.

Onde ver: Prazos e Ciclo; composicao da NCG; auditoria.

## `BAL - Estoques Diversos`

Materiais e pecas. `PME = Estoques / abs(DRE - Custos) x 365`. Entra no ACO. A Liquidez Seca desconta esta conta.

## `BAL - Créditos Tributários`

Impostos a recuperar de CP. Peca do ACO. Nao e caixa.

## `BAL - Outros Créditos`

Residual de CP. Nao entra no ACO padrao. Pode distorcer LC.

ACO oficial: recebiveis + estoques + creditos tributarios.
