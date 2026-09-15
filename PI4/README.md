# ESC_Semestre4_PI · PI4

Painel financeiro CTI (Streamlit) com arquitetura modular.

## Executar

```bash
cd PI4
py -m pip install -r requirements_dashboard.txt
py -m streamlit run app.py
```

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
