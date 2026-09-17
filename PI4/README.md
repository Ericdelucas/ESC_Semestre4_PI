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
