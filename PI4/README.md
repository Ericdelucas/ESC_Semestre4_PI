# ESC_Semestre4_PI · PI4

Painel financeiro CTI (Streamlit) com arquitetura modular.

## Executar

```bash
cd PI4
py -m pip install -r requirements_dashboard.txt
py -m streamlit run app.py
```

Compatível também com `py -m streamlit run dashboard_cti.py` ou `py dashboard_cti.py`.

## Estrutura

```
PI4/
  app.py                 # entrada (< 100 linhas): roteamento das abas
  dashboard_cti.py       # wrapper de compatibilidade
  Cti.csv                # base
  src/
    config.py            # constantes e caminhos
    data/                # loaders + analytics (pipeline dos notebooks)
    components/          # KPIs, sidebar, charts, resiliência
    views/               # uma view por aba
```
