"""Aba Como ler estes números."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from src.data.formatting import fmt_pct


def render(
    n_cenarios: int,
    cena_sel: str,
    k: pd.Series,
    ano_enc: int,
    p_ruina: float,
) -> None:
    st.markdown(
        f"""
### O que este painel responde

1. **A operação come ou gera caixa?** → olhe a **NCG**.  
2. **Dependemos de banco no curto prazo?** → olhe o **Saldo de Tesouraria**.  
3. **Por quantos dias financiamos a operação?** → olhe o **Ciclo Financeiro**.  
4. **Como os {n_cenarios:,} cenários se espalham em risco × retorno?** → aba **Mapeamento de Risco × Retorno**.  
5. **Qual a chance de caixa negativo no encerramento?** → aba **Distribuição & Probabilidades**.  
6. **Qual a faixa de caixa no horizonte?** → aba Faixa de risco.  
7. **Como dois ou três cenários se comparam no tempo?** → aba Comparar cenários.

Use o seletor de **Visão do stakeholder** para priorizar os KPIs do topo.

### Fórmulas

| Indicador | Fórmula |
|---|---|
| NCG | ACO − abs(PCO) |
| Saldo de Tesouraria | Disponível − Empréstimos CP |
| PMR | (Contas a Receber / Receita) × 365 |
| PME | (Estoques / abs(Custos)) × 365 |
| PMP | (Fornecedores / abs(Custos)) × 365 |
| Ciclo Financeiro | PMR + PME − PMP |

Cenário atual: **{cena_sel}** · Rentabilidade {fmt_pct(k["rentabilidade"])} · Risco {fmt_pct(k["risco"]) if pd.notna(k["risco"]) else "—"} · Prob. caixa negativo Ano {ano_enc}: **{p_ruina:.1f}%**.
"""
    )
