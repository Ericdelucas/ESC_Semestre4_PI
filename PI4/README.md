# ESC_Semestre4_PI · PI4

Painel financeiro CTI (Streamlit) com arquitetura modular.

## Executar

```bash
cd PI4
py -m pip install -r requirements_dashboard.txt
py -m streamlit run app.py
```

## Assistente de IA (RAG)

1. Crie `PI4/.env` a partir de `.env.example` e preencha `GOOGLE_API_KEY` (Google AI Studio), **ou** cole a chave na aba do assistente.
2. Coloque PDFs/Markdown extras em `PI4/documentos/`.
3. No painel, abra **🤖 Assistente IA**.

## Estrutura

```
PI4/
  app.py                 # entrada (< 100 linhas): roteamento das abas
  Cti.csv                # base
  src/
    config.py            # constantes e caminhos
    data/                # loaders + analytics (pipeline dos notebooks)
    components/          # KPIs, sidebar, charts, resiliência
    views/               # uma view por aba
```

## Visões por perfil

- **CEO - Visão estratégica:** receita, resultado, EBITDA, custos e capacidade de investir.
- **CFO - Gestão financeira:** capital de giro, tesouraria, empréstimos e evolução de caixa.
- **Acionistas - Retorno e risco:** lucro, margem líquida, crescimento, distribuições e sustentação do caixa.
- **Poder concedente - Sustentabilidade da concessão:** liquidez, continuidade financeira, investimentos e anos críticos.

Cada perfil abre uma visão própria e oferece análises detalhadas relevantes ao cargo.
Os cartões mostram médias anuais quando o filtro está em Todos; gráficos e tabelas respeitam o período selecionado.
A variação anual usa o ano anterior do mesmo cenário, inclusive quando apenas um ano está selecionado.
A frequência de cenários com sinais financeiros considera caixa final negativo, liquidez abaixo de 1 ou geração de caixa negativa, com pesos iguais; não representa probabilidade de falência.
