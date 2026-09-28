# Inventário Técnico do PI4

Documento atualizado para refletir a arquitetura modular atual do projeto `PI4`, incluindo Frontend Streamlit, Backend FastAPI, motor RAG, módulos financeiros, controllers, views, caches e artefatos gerados.

> Observação: arquivos `__pycache__/*.pyc` e `Backend/cache/*.parquet` são artefatos derivados. Eles aparecem neste inventário porque existem dentro de `PI4`, mas não são código-fonte primário.

---

## 1. Visão Geral do Sistema

O PI4 é um dashboard financeiro e operacional para leitura executiva de cenários simulados da CTI. A aplicação combina:

- **Frontend Streamlit** para navegação interativa, filtros, KPIs e gráficos Plotly.
- **Backend FastAPI** para chat RAG via endpoint HTTP.
- **Base financeira `Cti.csv`** com cenários anuais em formato longo: `ANO`, `CENA`, `CONTA`, `VALOR`.
- **Pipeline Pandas** para limpeza, pivot, indicadores, ranking, selos de risco e métricas financeiras.
- **Motor RAG local + Gemini** para responder perguntas usando cenários, glossário e documentos técnicos.

### Personas Atendidas

| Persona | Foco principal | Componentes relevantes |
|---|---|---|
| **CEO** | EBITDA, DRE, break-even, eficiência comercial, comparação estratégica | `controllers/kpis/ceo.py`, `views/persona_tabs/ceo.py`, comparador CEO |
| **CFO** | NCG, tesouraria, ciclo financeiro, liquidez corrente | `controllers/kpis/personas.py`, `views/capital_giro.py`, `views/prazos_ciclo.py`, comparador CFO |
| **Acionistas** | ROIC, EVA, dividendos, risco x retorno | `controllers/kpis/shareholders.py`, `views/persona_tabs/shareholders.py`, `comparison_shareholders.py` |
| **Poder Concedente** | CAPEX, liquidez geral, ativos reversíveis, conformidade financeira | `controllers/kpis/concession.py`, `views/persona_tabs/concession.py`, `comparison_concession.py` |
| **Teste** | Sandbox temporário para análises customizadas | `controllers/test_sandbox.py`, `views/persona_tabs/custom_analysis.py` |

### Integração IA/RAG

Existem dois modos de assistência:

- **Chat flutuante HTML**: `Frontend/chat_component.py` injeta `chat_widget.html`, que chama `Backend/main.py` via `POST /api/chat`.
- **Painel Streamlit nativo**: `views/ai_assistant/` renderiza chat com `st.chat_message`, usando o mesmo motor `src.models.rag_engine`.

O motor RAG principal foi modularizado em `Frontend/src/models/rag_engine/` e é reutilizado pelo Backend através de `Backend/rag_engine.py`.

---

## 2. Árvore de Diretórios Atualizada

```text
PI4/
├── .env.example
├── .gitignore
├── README.md
├── Backend/
│   ├── .env.example
│   ├── Cti.csv
│   ├── main.py
│   ├── rag_engine.py
│   ├── requirements.txt
│   ├── cache/
│   │   ├── cti_limpo.parquet
│   │   ├── indicadores.parquet
│   │   └── ranking.parquet
│   ├── documentos/
│   │   └── manual_executivo_cti.md
│   └── __pycache__/
│       ├── main.cpython-314.pyc
│       └── rag_engine.cpython-314.pyc
└── Frontend/
    ├── .streamlit/
    │   ├── config.toml
    │   └── credentials.toml
    ├── analise.ipynb
    ├── app.py
    ├── chat_component.py
    ├── chat_widget.html
    ├── organizando.ipynb
    ├── requirements_dashboard.txt
    ├── __pycache__/
    │   └── chat_component.cpython-314.pyc
    └── src/
        ├── __init__.py
        ├── config/
        │   ├── __init__.py
        │   ├── glossary.py
        │   └── i18n.py
        ├── controllers/
        │   ├── __init__.py
        │   ├── ai_sidebar_right.py
        │   ├── bootstrap.py
        │   ├── custom_analysis.py
        │   ├── data_input.py
        │   ├── headers.py
        │   ├── navigation.py
        │   ├── page_setup.py
        │   ├── resilience.py
        │   ├── sidebar.py
        │   ├── test_sandbox.py
        │   ├── charts/
        │   │   ├── __init__.py
        │   │   ├── histograms.py
        │   │   ├── risk_band.py
        │   │   └── time_series.py
        │   └── kpis/
        │       ├── __init__.py
        │       ├── ceo.py
        │       ├── concession.py
        │       ├── constants.py
        │       ├── helpers.py
        │       ├── personas.py
        │       ├── rendering.py
        │       └── shareholders.py
        ├── models/
        │   ├── __init__.py
        │   ├── classifiers.py
        │   ├── loaders.py
        │   ├── analytics/
        │   │   ├── __init__.py
        │   │   ├── indicators.py
        │   │   └── summaries.py
        │   ├── financial_metrics/
        │   │   ├── __init__.py
        │   │   ├── catalog.py
        │   │   ├── series.py
        │   │   ├── types.py
        │   │   └── utils.py
        │   ├── formatting/
        │   │   ├── __init__.py
        │   │   ├── base.py
        │   │   ├── comparisons.py
        │   │   ├── numbers.py
        │   │   ├── scenarios.py
        │   │   └── texts.py
        │   └── rag_engine/
        │       ├── __init__.py
        │       ├── answers.py
        │       ├── config.py
        │       ├── context.py
        │       ├── documents.py
        │       ├── embeddings.py
        │       ├── engine.py
        │       └── formatters.py
        └── views/
            ├── __init__.py
            ├── capital_giro.py
            ├── como_ler.py
            ├── comparar.py
            ├── distribuicao.py
            ├── faixa_risco.py
            ├── mapeamento_risco.py
            ├── prazos_ciclo.py
            ├── ai_assistant/
            │   ├── __init__.py
            │   ├── context.py
            │   └── panel.py
            └── persona_tabs/
                ├── __init__.py
                ├── ceo.py
                ├── common.py
                ├── comparison.py
                ├── comparison_ceo_cfo.py
                ├── comparison_concession.py
                ├── comparison_helpers.py
                ├── comparison_shareholders.py
                ├── concession.py
                ├── custom_analysis.py
                ├── shareholders.py
                └── styles.py
```

---

## 3. Raiz `PI4/`

| Arquivo | Responsabilidade | Funções/classes | Conexões |
|---|---|---|---|
| `PI4/.env.example` | Modelo de variáveis de ambiente do projeto. | Não contém funções. | Referência para `GOOGLE_API_KEY`/`GEMINI_API_KEY`. |
| `PI4/.gitignore` | Regras de exclusão de artefatos locais. | Não contém funções. | Ignora `.env`, caches, ambientes virtuais e bytecode. |
| `PI4/README.md` | Guia operacional do projeto. | Não contém funções. | Mostra comandos para Streamlit e Backend. |

---

## 4. Backend

### 4.1 Arquivos Principais

| Arquivo | Responsabilidade principal | Principais funções/classes | Dependências/conexões |
|---|---|---|---|
| `Backend/.env.example` | Modelo de `.env` específico do Backend. | Nenhuma. | Runtime lê `.env` real se existir. |
| `Backend/Cti.csv` | Base bruta financeira e operacional. | Não é código. | Lido por `src.models.loaders.load_cti_csv`; origem dos indicadores e ranking. |
| `Backend/requirements.txt` | Dependências da API e do RAG. | Nenhuma. | FastAPI, Uvicorn, Pandas, FAISS, LangChain, Gemini e dotenv. |
| `Backend/main.py` | API HTTP do chat CTI. | `ChatIn`, `ChatOut`, `_rag`, `health`, `chat`. | Importa `Backend.rag_engine.CTIRag`; expõe `/api/health` e `/api/chat`. |
| `Backend/rag_engine.py` | Adaptador Backend para o motor RAG do Frontend. | `CTIRag`, `_carregar_ranking`. | Coloca `Frontend` no `sys.path`; importa `RagEngine`, `resolve_api_key`, `load_cti_csv`, `montar_indicadores`. |

### 4.2 `Backend/main.py`

- **Propósito:** prover uma API FastAPI para o chat externo ao Streamlit.
- **Estado interno:** `_engine` guarda uma instância única de `CTIRag`; `_sessoes` mantém histórico por `session_id`.
- **Fluxo de chamada:** `POST /api/chat` recebe `ChatIn`, normaliza `session_id`, chama `_rag().responder`, salva as últimas 12 mensagens e devolve `ChatOut`.
- **CORS:** aberto para qualquer origem, permitindo que `chat_widget.html` chame `localhost:8000`.

### 4.3 `Backend/rag_engine.py`

- **Propósito:** carregar ranking e delegar perguntas ao `RagEngine`.
- **Classe `CTIRag`:**
  - `__init__`: chama `_carregar_ranking` e cria `RagEngine.from_ranking`.
  - `responder`: chama `engine.ask` em português com `resolve_api_key`.
- **Cache de ranking:** se `Backend/cache/ranking.parquet` existir e for mais novo que `Cti.csv`, é lido diretamente; senão, o CSV é processado novamente.

### 4.4 Dados, Cache e Documentos

| Arquivo | Tipo | Responsabilidade | Conexões |
|---|---|---|---|
| `Backend/cache/cti_limpo.parquet` | Cache Parquet | CSV já limpo, com `VALOR` numérico e `ano_num`. | Gerado/lido por `load_cti_csv`. |
| `Backend/cache/indicadores.parquet` | Cache Parquet | Indicadores anuais por cenário. | Usado por `bootstrap.carregar_pipeline`. |
| `Backend/cache/ranking.parquet` | Cache Parquet | Ranking consolidado por cenário. | Usado pelo dashboard e pelo RAG. |
| `Backend/documentos/manual_executivo_cti.md` | Markdown | Manual executivo indexado pelo RAG. | Lido por `rag_engine.documents.docs_manuais`. |

### 4.5 Bytecode Backend

| Arquivo | Propósito |
|---|---|
| `Backend/__pycache__/main.cpython-314.pyc` | Bytecode gerado a partir de `Backend/main.py`. |
| `Backend/__pycache__/rag_engine.cpython-314.pyc` | Bytecode gerado a partir de `Backend/rag_engine.py`. |

---

## 5. Frontend Raiz

| Arquivo | Responsabilidade | Funções/classes | Conexões |
|---|---|---|---|
| `Frontend/app.py` | Orquestrador Streamlit enxuto. | `main`. | Chama `configure_page`, `carregar_estado`, `render_data_input`, `montar_contexto`, `render_pagina`, `render_floating_chat`. |
| `Frontend/chat_component.py` | Injeta o chat flutuante HTML no Streamlit. | `render_floating_chat`. | Lê `chat_widget.html` e aplica CSS fixo para iframe. |
| `Frontend/chat_widget.html` | Widget HTML/JS do chat flutuante. | JavaScript interno de envio HTTP. | Chama `http://localhost:8000/api/chat`. |
| `Frontend/requirements_dashboard.txt` | Dependências do dashboard. | Nenhuma. | Streamlit, Plotly, Pandas, FAISS, Gemini, pypdf etc. |
| `Frontend/analise.ipynb` | Notebook exploratório. | Células Jupyter. | Referência analítica; não é importado pelo app. |
| `Frontend/organizando.ipynb` | Notebook de organização da base. | Células Jupyter. | Inspira funções de `loaders.py`; não é importado pelo app. |

### 5.1 `Frontend/app.py`

O arquivo foi modularizado e agora só coordena alto nível:

1. `configure_page()` aplica `st.set_page_config` e CSS global.
2. `render_language_selector()` inicializa idioma.
3. `carregar_estado()` busca dados e caches.
4. `render_data_input(df)` permite upload/edição/substituição de dados.
5. Se houver dados customizados, recalcula `ind` e `ranking` com `montar_indicadores`.
6. `render_sidebar` e `render_persona` coletam filtros.
7. `montar_contexto` cria `AppContext`.
8. `render_pagina(ctx)` renderiza cabeçalho, abas e análises.
9. `render_floating_chat()` injeta o chat HTML.

### 5.2 Streamlit Local

| Arquivo | Responsabilidade |
|---|---|
| `Frontend/.streamlit/config.toml` | Configuração de tema, servidor e estatísticas do Streamlit. |
| `Frontend/.streamlit/credentials.toml` | Arquivo local do Streamlit com e-mail vazio. |

### 5.3 Bytecode Frontend Raiz

| Arquivo | Propósito |
|---|---|
| `Frontend/__pycache__/chat_component.cpython-314.pyc` | Bytecode gerado de `chat_component.py`. |

---

## 6. Pacote `Frontend/src`

| Arquivo | Responsabilidade |
|---|---|
| `Frontend/src/__init__.py` | Marca `src` como pacote raiz do dashboard. |

---

## 7. Configuração (`src/config`)

| Arquivo | Responsabilidade | Funções/constantes | Conexões |
|---|---|---|---|
| `src/config/__init__.py` | Constantes globais de caminho, cor, personas, navegação e contas. | `PI4`, `ROOT`, `BACKEND`, `CSV_PATH`, `CACHE_DIR`, `DOCS_DIR`, `COR*`, `PERSONAS`, `NAV_KEYS`, `METRICAS_NUVEM`, `PECAS_CONTAS`. | Importado por loaders, analytics, charts, KPIs, RAG e views. |
| `src/config/i18n.py` | Internacionalização PT/EN da interface. | `DEFAULT_LANG`, `SUPPORTED_LANGS`, `LANG_OPTIONS`, `SELO_KEYS`, `TEXTS`, `get_lang`, `set_lang`, `t`, `get_text`, `translate_selo`. | Usado por sidebar, headers, formatting, views e controllers. |
| `src/config/glossary.py` | Glossário técnico e textos de ajuda. | `GLOSSARIO`, `NUVEM_HELP`, `PERCENTIL_HELP`, `glossary`, `help_text`, `help_join`. | Alimenta `help=` dos widgets e documentos do RAG. |

`i18n.py` e `glossary.py` continuam como catálogos centralizados. Eles são extensos, mas majoritariamente textuais; dividir por idioma/domínio exige validação em runtime para evitar quebra de chaves usadas em dezenas de widgets.

### Bytecode `config`

| Arquivo | Propósito |
|---|---|
| `src/config/__pycache__/__init__.cpython-314.pyc` | Bytecode de constantes globais. |
| `src/config/__pycache__/glossary.cpython-314.pyc` | Bytecode do glossário. |
| `src/config/__pycache__/i18n.cpython-314.pyc` | Bytecode de internacionalização. |

---

## 8. Controllers (`src/controllers`)

Controllers coordenam Streamlit, estado de UI, layout, KPIs, navegação e gráficos. A lógica financeira pesada fica em `models`.

| Arquivo | Responsabilidade | Funções/classes | Conexões |
|---|---|---|---|
| `src/controllers/__init__.py` | Fachada lazy-load dos controllers. | `__getattr__`, `__all__`. | Reexporta charts, headers, KPIs, sidebar, resilience e IA lateral. |
| `src/controllers/page_setup.py` | Configuração visual global. | `configure_page`. | Chamado por `app.py`; esconde Deploy/menu/header Streamlit e força contraste de `st.metric`. |
| `src/controllers/bootstrap.py` | Carregamento de dados, contexto e cabeçalho. | `AppContext`, `carregar_pipeline`, `carregar_estado`, `montar_contexto`, `render_cabecalho`. | Usa loaders, analytics, KPIs e headers. |
| `src/controllers/navigation.py` | Navegação de sub-abas e roteamento por persona. | `VIEW_RENDERERS`, `PERSONA_NAV_KEYS`, `PERSONA_NAV_LABELS`, `PERSONA_VIEW_RENDERERS`, `render_analises`, `render_pagina`. | Chamado por `app.py`; usa views e sandbox/custom analysis. |
| `src/controllers/sidebar.py` | Barra lateral e seletor de persona. | `render_language_selector`, `render_sidebar`, `render_persona`. | Usa `i18n`, `formatting.scenarios`, `st.session_state`. |
| `src/controllers/headers.py` | Banners, auditoria e títulos com ajuda. | `recorte_label`, `banner_auditoria_filtro`, `expander_auditoria_base`, `heading_with_help`. | Usado por navigation, bootstrap e views. |
| `src/controllers/resilience.py` | Tratamento de erro por componente. | `safe_render`, `resilient_view`. | Decora views e protege renderizações críticas. |
| `src/controllers/data_input.py` | Upload, edição manual e restauração de dados. | `DF_OVERRIDE_KEY`, `REQUIRED_LONG_COLUMNS`, `SCENARIO_ALIASES`, `COLUMN_ALIASES`, `has_custom_data`, `_clean_col_name`, `_rename_aliases`, `_to_number`, `_read_upload`, `_long_from_wide`, `normalizar_novos_dados`, `_manual_template`, `render_data_input`. | Chamado por `app.py`; atualiza `st.session_state["cti_df_override"]`. |
| `src/controllers/custom_analysis.py` | Estado e formulário de análises customizadas por persona. | `CUSTOM_ANALYSES_KEY`, `CHART_TYPES`, `custom_store`, `custom_analyses`, `custom_key`, `custom_label`, `insert_custom_tabs`, `_render_custom_analysis_form`, `render_custom_analysis_dialog`. | Usado por `navigation.py`; cria abas dinâmicas com `FINANCIAL_METRICS_DICT`. |
| `src/controllers/test_sandbox.py` | Persona temporária `Teste`. | `TEST_SANDBOX_KEY`, `TEST_CHART_LABELS`, `_test_sandbox_items`, `_render_test_sandbox_form`, `_render_test_sandbox_dialog`, `render_teste_sandbox`. | Usa `views.persona_tabs.render_custom_analysis`. |
| `src/controllers/ai_sidebar_right.py` | Painel de IA lateral alternativo. | `_CSS_FECHADA`, `_painel_aberto`, `_abrir`, `render_ai_layout`. | Usa `views.ai_assistant.render_chat_panel`; alternativa ao chat flutuante HTML. |

### 8.1 Charts (`src/controllers/charts`)

| Arquivo | Responsabilidade | Funções/classes | Conexões |
|---|---|---|---|
| `charts/__init__.py` | Fachada dos gráficos. | Reexporta funções de histograms, risk_band e time_series. | Mantém imports antigos `src.controllers.charts`. |
| `charts/time_series.py` | Helpers para séries temporais Plotly. | `recorte_label`, `titulo_filtro`, `serie_temporal_plotavel`, `ancorar_ano_temporal`. | Usado em views de capital de giro, prazos e comparar. |
| `charts/risk_band.py` | Gráfico de envelope/faixa de risco. | `figura_envelope`. | Usa `models.analytics.resumo_envelope`; destaca ano/cenário. |
| `charts/histograms.py` | Histogramas de risco e caixa final. | `figura_histograma_ano`, `figura_histograma_caixa_final`. | Usado por `faixa_risco.py` e `distribuicao.py`. |

### 8.2 KPIs (`src/controllers/kpis`)

| Arquivo | Responsabilidade | Funções/classes | Conexões |
|---|---|---|---|
| `kpis/__init__.py` | Fachada compatível do antigo `kpis.py`. | Reexporta constantes, helpers, renderers e funções por persona. | Mantém imports existentes `from src.controllers.kpis import ...`. |
| `kpis/constants.py` | Contas contábeis e parâmetros globais dos KPIs. | `KpiItem`, `CONTA_*`, `WACC_FALLBACK`, `ALIQUOTA_IR_FALLBACK`, `CEO_LTV_CAC_FALLBACK`. | Usado por KPIs CEO, acionistas e concedente. |
| `kpis/helpers.py` | Leitura segura de contas/premissas. | `_safe_div`, `_valor_conta_raw`, `_valor_premissa_comercial`. | Usado por cálculos de KPI. |
| `kpis/ceo.py` | Cards do CEO. | `_kpis_ceo`. | Calcula EBITDA, margem EBITDA, break-even e LTV/CAC. |
| `kpis/shareholders.py` | Cards dos acionistas. | `_kpis_acionistas`. | Calcula ROIC, EVA, lucro líquido e margem líquida. |
| `kpis/concession.py` | Cards do Poder Concedente. | `_kpis_poder_concedente`. | Calcula CAPEX, liquidez geral e ativo total/base reversível. |
| `kpis/personas.py` | Roteamento de KPIs por persona. | `kpis_por_persona`. | CFO usa `k` do contexto; demais usam funções específicas. |
| `kpis/rendering.py` | Renderização visual dos cards. | `_KPI_FORCE_CSS`, `_garantir_css_metricas`, `card_selo_html`, `render_metric_card`, `render_kpi_row`. | Usa `st.metric`, CSS de contraste e `translate_selo`. |

### 8.3 Bytecode Controllers

Arquivos `.pyc` existentes em `src/controllers/**/__pycache__` são bytecode gerado automaticamente para os módulos acima, incluindo `charts` e `kpis`. Eles não têm responsabilidade funcional própria e podem ser regenerados pelo Python.

---

## 9. Models (`src/models`)

`models` concentra carga, limpeza, cálculo, classificação, formatação e RAG.

| Arquivo | Responsabilidade | Funções/classes | Conexões |
|---|---|---|---|
| `src/models/__init__.py` | Fachada lazy-load de funções de models. | `__getattr__`, `__all__`. | Permite imports antigos como `from src.models import fmt_rs`. |
| `src/models/loaders.py` | Leitura e normalização da base CTI. | `parse_valor_br`, `normalizar_conta`, `magnitude`, `load_cti_csv`, `separar_demonstrativos`, `soma_contas`. | Usa `CSV_PATH`, `CACHE_DIR`; gera `cti_limpo.parquet`. |
| `src/models/classifiers.py` | Classificação de cenários por selos. | `classificar_cenarios`. | Usa `SELOS_NEGOCIO`; adiciona booleanos e `selo` ao ranking. |

### 9.1 Analytics (`src/models/analytics`)

| Arquivo | Responsabilidade | Funções/classes | Conexões |
|---|---|---|---|
| `analytics/__init__.py` | Fachada compatível do antigo `analytics.py`. | Reexporta `_mapa_contas`, `montar_indicadores`, `resumo_envelope`, `resumo_estatistico`, `cenas_por_percentil`, `probabilidade_caixa_negativo`. | Mantém imports existentes. |
| `analytics/indicators.py` | Pipeline principal de indicadores. | `_mapa_contas`, `montar_indicadores`. | Usa `PECAS_CONTAS`, `CONTAS_RECEBER`, `magnitude`, `classificar_cenarios`. |
| `analytics/summaries.py` | Estatísticas auxiliares. | `resumo_envelope`, `resumo_estatistico`, `cenas_por_percentil`, `probabilidade_caixa_negativo`. | Usado por faixa de risco, distribuição e bootstrap. |

### 9.2 Métricas Financeiras Dinâmicas (`src/models/financial_metrics`)

| Arquivo | Responsabilidade | Funções/classes | Conexões |
|---|---|---|---|
| `financial_metrics/__init__.py` | Fachada pública. | Reexporta `FINANCIAL_METRICS_DICT`, `FinancialMetric`, `metric_timeseries`, `format_metric_value`, helpers privados. | Usado por sandbox e análises customizadas. |
| `financial_metrics/types.py` | Tipagem das métricas. | `FinancialMetric`. | Define estrutura `categoria`, `nome`, `formula`, `format`. |
| `financial_metrics/utils.py` | Utilitários numéricos. | `_safe_div`, `_to_number`, `_normalizar_aliases`. | Usado por catálogo e séries. |
| `financial_metrics/catalog.py` | Catálogo de indicadores dinâmicos. | `FINANCIAL_METRICS_DICT`. | Inclui ROE, ROA, ROIC, margens, liquidez, estrutura de capital, prazos, NCG, FCFF, FCFE e cobertura de juros. |
| `financial_metrics/series.py` | Cálculo temporal de uma métrica. | `contas_necessarias`, `metric_timeseries`, `format_metric_value`. | Usado por `views/persona_tabs/custom_analysis.py`. |

### 9.3 Formatting (`src/models/formatting`)

| Arquivo | Responsabilidade | Funções/classes | Conexões |
|---|---|---|---|
| `formatting/__init__.py` | Fachada compatível do antigo `formatting.py`. | Reexporta formatos públicos e aliases privados antigos. | Mantém imports `src.models.formatting`. |
| `formatting/base.py` | Helpers básicos de formatação. | `is_na`, `fmt_number_pt`, `fmt_number_en`. | Usado por números e textos. |
| `formatting/numbers.py` | Formatação de valores. | `fmt_rs`, `fmt_dias`, `fmt_pct`. | Usa `get_lang` e `t`. |
| `formatting/scenarios.py` | Identificação e rótulo de cenários. | `_RE_CEN`, `cena_id`, `cena_rotulo`, `cena_sort_key`. | Usado em sidebar, charts e views. |
| `formatting/texts.py` | Frases interpretativas. | `texto_ncg`, `texto_tesouraria`, `texto_ciclo`. | Usado no cabeçalho CFO. |
| `formatting/comparisons.py` | Comparações simples entre cenários. | `melhor_entre`, `cenas_padrao_comparacao`. | Usado no mapeamento e comparador legado. |

### 9.4 RAG Engine (`src/models/rag_engine`)

| Arquivo | Responsabilidade | Funções/classes | Conexões |
|---|---|---|---|
| `rag_engine/__init__.py` | Fachada compatível do antigo `rag_engine.py`. | Reexporta `RagEngine`, `TfidfEmbeddings`, `build_focus_context`, `resolve_api_key` e aliases privados antigos. | Usado por Backend e assistente Streamlit. |
| `rag_engine/config.py` | Constantes e prompts do RAG. | `SYSTEM_PROMPT_PT`, `SYSTEM_PROMPT_EN`, `PLACEHOLDER_NAMES`, `TEXT_SUFFIXES`, `PDF_SUFFIXES`, `MAX_FILE_BYTES`, `GEMINI_MODELS`, regex e termos financeiros. | Usado por documentos e respostas. |
| `rag_engine/formatters.py` | Formatação simples para respostas RAG. | `rs`, `pct`, `dias`. | Usado na geração de documentos de cenário e contexto. |
| `rag_engine/embeddings.py` | Embeddings locais TF-IDF. | `TfidfEmbeddings`. | Implementa interface LangChain `Embeddings`; usado por `RagEngine`. |
| `rag_engine/documents.py` | Coleta e criação de documentos RAG. | `ler_pdf`, `parece_transcricao`, `iter_arquivos_doc`, `docs_manuais`, `docs_glossario`, `docs_cenarios`. | Lê `Backend/documentos`, PDFs/Markdown e ranking. |
| `rag_engine/context.py` | Contexto do filtro atual para o assistente. | `serie_val`, `build_focus_context`. | Usado por `views/ai_assistant/context.py`. |
| `rag_engine/answers.py` | API key, fallback extrativo e Gemini. | `resolve_api_key`, `paragrafos_financeiros`, `resposta_extrativa`, `gerar_llm`. | Usa `google.genai`; fallback sem chave. |
| `rag_engine/engine.py` | Núcleo de indexação e busca. | `faiss_index`, `prioridade_fonte`, `RagEngine`. | Usa FAISS se disponível; senão similaridade NumPy. |

### 9.5 Bytecode Models

Arquivos `.pyc` em `src/models/**/__pycache__` correspondem aos módulos acima (`analytics`, `financial_metrics`, `formatting`, `rag_engine`, `loaders`, `classifiers`). São artefatos derivados e podem ser removidos sem perda de código-fonte.

---

## 10. Views (`src/views`)

Views renderizam telas Streamlit. Elas recebem DataFrames/contexto já preparados pelos controllers.

| Arquivo | Responsabilidade | Funções/classes | Conexões |
|---|---|---|---|
| `src/views/__init__.py` | Importa os módulos de views. | `__all__`. | Permite `from src.views import persona_tabs`, etc. |
| `views/capital_giro.py` | Aba Capital de Giro. | `_grafico_evolucao`, `_grafico_composicao`, `render`. | Usa `charts.time_series`, `fmt_rs`, `help_text`; mostra NCG e Tesouraria. |
| `views/prazos_ciclo.py` | Aba Prazos e Ciclo. | `_grafico_prazos`, `render`. | Mostra PMR, PME, PMP e Ciclo Financeiro. |
| `views/mapeamento_risco.py` | Matriz risco x retorno. | `_scatter`, `render`. | Usa Plotly scatter, `CORES_SELO`, `translate_selo`, `cenas_por_percentil`, `card_selo_html`. |
| `views/distribuicao.py` | Distribuição e probabilidades. | `_boxplot`, `render`. | Usa percentis, boxplot e histograma de caixa final. |
| `views/faixa_risco.py` | Envelope de risco. | `render`. | Usa `METRICAS_NUVEM`, `figura_envelope`, `figura_histograma_ano`. |
| `views/comparar.py` | Comparador legado de 2 ou 3 cenários para métricas operacionais. | `render`. | Usa multiselect, `CORES_COMPARA`, `ancorar_ano_temporal`. |
| `views/como_ler.py` | Explicação textual dos números. | `render`. | Usa textos i18n e contexto do cenário. |

### 10.1 Assistente Streamlit (`views/ai_assistant`)

| Arquivo | Responsabilidade | Funções/classes | Conexões |
|---|---|---|---|
| `ai_assistant/__init__.py` | Fachada da view de IA. | Reexporta `render`, `render_chat`, `render_chat_panel`. | Mantém import `from src.views.ai_assistant import render_chat_panel`. |
| `ai_assistant/context.py` | Cache e contexto do RAG na tela. | `_fingerprint`, `_carregar_engine`, `_chave_api`, `_contexto_foco`. | Usa `RagEngine`, `build_focus_context`, `fmt_pct`, `cena_rotulo`. |
| `ai_assistant/panel.py` | UI do chat nativo Streamlit. | `_BOAS_VINDAS`, `_inicializar_historico`, `_render_mensagens`, `_render_formulario`, `render_chat_panel`, `render_chat`, `render`. | Usa `st.chat_message`, `st.form`, `engine.ask`, `st.session_state`. |

### 10.2 Sub-Abas por Persona (`views/persona_tabs`)

| Arquivo | Responsabilidade | Funções/classes | Conexões |
|---|---|---|---|
| `persona_tabs/__init__.py` | Fachada compatível da antiga `persona_tabs.py`. | Reexporta renders de CEO, acionistas, concedente, comparador e custom analysis. | Usado por `controllers/navigation.py` e `test_sandbox.py`. |
| `persona_tabs/common.py` | Cálculos comuns de DRE, balanço, financeiro e break-even. | `WACC`, `PAYOUT`, `ALIQUOTA_IR_FALLBACK`, `_safe_div`, `_wide`, `_conta`, `_dre`, `_balanco_fluxo`, `_financeiro`, `_break_even_df`. | Base para sub-abas e comparadores. |
| `persona_tabs/styles.py` | Estilos das séries A/B/C no comparador. | `SERIES_STYLES`. | Usado por comparadores. |
| `persona_tabs/ceo.py` | Sub-abas do CEO. | `render_ceo_visao_geral`, `render_ceo_dre_operacional`, `render_ceo_break_even`, `render_ceo_ltv_cac`. | Usa `_dre`, `_break_even_df`, Plotly Waterfall/Line/Bar/Area. |
| `persona_tabs/shareholders.py` | Sub-abas dos acionistas. | `render_acionistas_retorno`, `render_acionistas_eva`, `render_acionistas_dividendos`. | Usa `_financeiro`; EVA trata `NaN` com `EVA_limpo`/`eva_positivo`. |
| `persona_tabs/concession.py` | Sub-abas do Poder Concedente. | `_dre_balanco`, `render_concedente_capex`, `render_concedente_solvencia`, `render_concedente_ativos`. | Usa `_balanco_fluxo`, `_dre`, Plotly e limite de liquidez 1.0x. |
| `persona_tabs/comparison.py` | Roteador do comparador por persona. | `render_comparar_cenarios`. | Direciona para CEO/CFO, acionistas ou concedente. |
| `persona_tabs/comparison_helpers.py` | Helpers do comparador. | `_selecionar_cenarios`, `_delta`, `_cor_delta`, `_metric_base`, `_fmt_x`. | Usado pelos comparadores específicos. |
| `persona_tabs/comparison_ceo_cfo.py` | Comparadores CEO e CFO. | `_ceo_cmp`, `_render_cmp_ceo`, `_render_cmp_cfo`. | Usa `SERIES_STYLES`, `_metric_base`, linhas/áreas Plotly. |
| `persona_tabs/comparison_shareholders.py` | Comparador dos acionistas. | `_render_cmp_acionistas`. | Usa EVA, ROIC, dividendos e scatter risco x retorno. |
| `persona_tabs/comparison_concession.py` | Comparador do Poder Concedente. | `_concedente_cmp`, `_lg_referencia`, `_base_final_ativos`, `_render_cmp_concedente`. | Alerta vermelho somente quando LG de referência < 1.0x. |
| `persona_tabs/custom_analysis.py` | Renderização de análise customizada. | `render_custom_analysis`. | Usa `metric_timeseries`, `format_metric_value`, Plotly linha/barra/área/card. |

### 10.3 Correções Plotly Recentes

- **EVA da aba Acionistas:** `shareholders.py` cria `EVA_limpo = EVA.fillna(0)` e `eva_positivo = EVA_limpo >= 0` antes do `px.bar`, evitando `TypeError: boolean value of NA is ambiguous`.
- **EVA do comparador:** `comparison_shareholders.py` converte `ano_num` para eixo categórico:

```python
eva["Ano_Rotulo"] = "Ano " + eva["ano_num"].astype(str)
fig = px.bar(
    eva,
    x="Ano_Rotulo",
    y="EVA",
    color="Cenário",
    barmode="group",
    category_orders={"Ano_Rotulo": ordem_anos},
)
```

Esse ajuste evita eixo contínuo ilegível e mantém as barras agrupadas por cenário.

### 10.4 Bytecode Views

Arquivos `.pyc` em `src/views/**/__pycache__` são bytecode gerado a partir das views listadas. Eles refletem versões previamente executadas e não devem ser tratados como fonte.

---

## 11. Fluxo de Dados e Estado Global

### 11.1 Fluxo Principal do Dashboard

```text
Frontend/app.py
  ├─ configure_page()
  ├─ render_language_selector()
  ├─ carregar_estado()
  │    └─ carregar_pipeline()
  │         ├─ load_cti_csv(Cti.csv)
  │         ├─ montar_indicadores(df)
  │         └─ classificar_cenarios(ranking)
  ├─ render_data_input(df)
  │    └─ se houver override: recalcula indicadores/ranking
  ├─ render_sidebar(df, ind, n_cenarios)
  ├─ render_persona()
  ├─ montar_contexto(...)
  │    └─ cria AppContext
  ├─ render_pagina(ctx)
  │    ├─ render_cabecalho(ctx)
  │    └─ render_analises(ctx)
  └─ render_floating_chat()
```

### 11.2 DataFrames Principais

| Nome | Origem | Granularidade | Uso |
|---|---|---|---|
| `df` | `load_cti_csv` ou upload customizado | Base longa conta/ano/cenário | Auditoria, KPIs por conta, persona tabs, custom analysis. |
| `ind` | `montar_indicadores` | Uma linha por cenário/ano | Capital de giro, prazos, faixa, comparadores CFO. |
| `ranking` | `montar_indicadores` + `classificar_cenarios` | Uma linha por cenário | Mapeamento, distribuição, RAG, contexto, KPIs gerais. |
| `ctx.foco` | `montar_contexto` | `ind` filtrado por cenário | Gráficos temporais. |
| `ctx.foco_ano` | `montar_contexto` | `ctx.foco` filtrado por ano ou todo horizonte | Composição e KPIs. |
| `ctx.k` | `montar_contexto` | Série média do recorte | Cards do topo, textos CFO, contexto IA. |

### 11.3 `AppContext`

`AppContext` é o objeto de contexto global da tela. Campos principais:

- `df`, `ind`, `ranking`: dados base, indicadores e ranking.
- `mapa_rotulo`: ranking enriquecido com rótulos.
- `n_cenarios`, `ano_enc`, `p_ruina`: estatísticas globais.
- `ano_sel`, `cena_sel`, `anos`, `cenas`: filtros.
- `persona`: persona ativa (`ceo`, `cfo`, `acionistas`, `concedente`, `teste`).
- `foco`, `foco_ano`, `k`: recortes calculados para a tela.

### 11.4 `st.session_state`

| Chave | Local | Função |
|---|---|---|
| `lang` | `config/i18n.py`, `sidebar.py` | Idioma ativo. |
| `persona_id` | `sidebar.py` | Persona ativa. |
| `nav_key` | `navigation.py` | Sub-aba ativa por persona. |
| `show_custom_analysis_dialog_<persona>` | `custom_analysis.py`, `navigation.py` | Abre modal de análise customizada. |
| `custom_financial_analyses` | `custom_analysis.py` | Lista de análises customizadas por persona. |
| `test_sandbox_analyses` | `test_sandbox.py` | Lista de análises da persona Teste. |
| `teste_nav_key` | `test_sandbox.py` | Aba ativa no sandbox. |
| `show_test_sandbox_dialog` | `test_sandbox.py` | Abre modal do botão `+` no sandbox. |
| `cti_df_override` | `data_input.py` | DataFrame customizado carregado/editado pelo usuário. |
| `chat_history` | `ai_assistant/panel.py` | Histórico do chat Streamlit nativo. |
| `ai_chat_history` | `ai_assistant/panel.py` | Compatibilidade com histórico anterior. |
| `gemini_api_key_input` | `ai_assistant/context.py` | Chave colada em runtime. |
| `google_api_key` | `ai_assistant/context.py` | Chave mantida na sessão. |
| `_cti_kpi_css_ok` | `kpis/rendering.py` | Evita reinjetar CSS dos KPIs a cada card. |

---

## 12. Fluxo RAG/IA

### 12.1 Chat Flutuante HTML

```text
chat_component.py
  └─ injeta chat_widget.html
      └─ JS faz POST /api/chat
          └─ Backend/main.py
              └─ CTIRag.responder()
                  └─ RagEngine.ask()
```

### 12.2 Chat Streamlit Nativo

```text
views/ai_assistant/panel.py
  ├─ histórico em st.session_state
  ├─ context._carregar_engine(ranking, fingerprint)
  ├─ context._contexto_foco(...)
  └─ engine.ask(..., extra_context=foco atual)
```

### 12.3 Documentos Indexados

`rag_engine.documents` cria documentos a partir de:

- Resumo agregado dos cenários.
- Distribuição por selo.
- Um documento por cenário.
- Glossário PT/EN.
- Arquivos técnicos em `Backend/documentos/` e repositório `documentos/`, ignorando transcrições e arquivos grandes.

Se `GOOGLE_API_KEY`/`GEMINI_API_KEY` não existir, `RagEngine.ask` usa `resposta_extrativa`, retornando trechos selecionados e fontes.

---

## 13. Regras Visuais e CSS

| Local | Regra |
|---|---|
| `controllers/page_setup.py` | Esconde botão Deploy, menu superior e header padrão do Streamlit. |
| `controllers/page_setup.py` | Força `stMetricValue` e `stMetricLabel` em branco para dark mode. |
| `controllers/kpis/rendering.py` | Reaplica CSS específico em cards de KPI. |
| `chat_component.py` | Posiciona iframe do chat flutuante no canto inferior direito. |
| `chat_widget.html` | Controla aparência independente do widget HTML. |

---

## 14. Funcionalidades Recentes Documentadas

### 14.1 Modularização

Arquivos grandes convertidos em pacotes com `__init__.py` compatível:

- `models/formatting.py` -> `models/formatting/`
- `models/rag_engine.py` -> `models/rag_engine/`
- `models/analytics.py` -> `models/analytics/`
- `models/financial_metrics.py` -> `models/financial_metrics/`
- `controllers/kpis.py` -> `controllers/kpis/`
- `controllers/charts.py` -> `controllers/charts/`
- `views/persona_tabs.py` -> `views/persona_tabs/`
- `views/ai_assistant.py` -> `views/ai_assistant/`
- partes de `app.py` -> `controllers/page_setup.py`, `navigation.py`, `custom_analysis.py`, `test_sandbox.py`

### 14.2 Upload e Edição de Dados

`controllers/data_input.py` adiciona:

- Upload `.csv`/`.xlsx`.
- Edição manual via `st.data_editor`.
- Normalização de colunas e aliases.
- Conversão de strings numéricas brasileiras.
- Opção de aplicar dados customizados em `st.session_state`.
- Opção de restaurar base original.

### 14.3 Comparação de Cenários

O comparador em `views/persona_tabs/comparison*.py` suporta:

- Cenário A base.
- Cenário B comparativo.
- Cenário C opcional.
- Deltas visuais contra A.
- Gráficos distintos por persona.
- Validação de cenários duplicados.
- Alertas condicionais de caducidade apenas quando LG < 1.0x.

### 14.4 Sandbox de Teste

`controllers/test_sandbox.py` cria a persona `Teste`:

- Sem cards fixos de topo.
- Sub-aba inicial `Análise 1`.
- Botão `+` para criar gráfico temporário.
- Modal com indicador e tipo de visualização.
- Renderização por `views/persona_tabs/custom_analysis.py`.

---

## 15. Arquivos Gerados e Higiene

| Padrão | Natureza | Pode apagar? | Observação |
|---|---|---|---|
| `**/__pycache__/*.pyc` | Bytecode Python | Sim | Python recria automaticamente. |
| `Backend/cache/*.parquet` | Cache de dados processados | Sim, com custo | O app recalcula a partir de `Cti.csv`. |
| `.streamlit/credentials.toml` | Config local Streamlit | Sim | Pode ser recriado pelo Streamlit. |
| `.env` real | Segredo local | Não versionar | Não aparece no inventário se ausente. |

---

## 16. Pontos de Entrada

| Comando | Diretório esperado | Resultado |
|---|---|---|
| `py -m streamlit run Frontend/app.py` | `PI4/` | Sobe o dashboard Streamlit. |
| `py -m uvicorn Backend.main:app --host 127.0.0.1 --port 8000` | `PI4/` | Sobe API do chat. |
| `POST http://localhost:8000/api/chat` | API ativa | Responde perguntas do chat flutuante. |
| `GET http://localhost:8000/api/health` | API ativa | Retorna `{"status": "ok"}`. |

---

## 17. Dependências Entre Camadas

```text
app.py
  -> controllers/page_setup.py
  -> controllers/bootstrap.py
      -> models/loaders.py
      -> models/analytics/
      -> controllers/kpis/
  -> controllers/data_input.py
  -> controllers/sidebar.py
  -> controllers/navigation.py
      -> views/*
      -> views/persona_tabs/*
  -> chat_component.py

Backend/main.py
  -> Backend/rag_engine.py
      -> Frontend/src/models/rag_engine/
      -> Frontend/src/models/analytics/
      -> Frontend/src/models/loaders.py
```

Separação de responsabilidades:

- **`config`**: constantes, cores, textos e glossário.
- **`models`**: dados, cálculos, formatação e RAG.
- **`controllers`**: estado Streamlit, navegação, layout e coordenação.
- **`views`**: telas, gráficos e widgets finais.
- **`Backend`**: API HTTP e ponte para RAG.

---

## 18. Apêndice: Inventário Exato de Arquivos no Disco

Esta seção lista todos os arquivos observados dentro de `PI4` no momento da atualização. Arquivos `.pyc` são bytecode gerado e estão marcados como artefatos.

### 18.1 Raiz e Backend

| Caminho | Propósito |
|---|---|
| `PI4/.env.example` | Modelo de variáveis de ambiente da raiz. |
| `PI4/.gitignore` | Regras de arquivos ignorados pelo Git. |
| `PI4/README.md` | Guia de instalação e execução do projeto. |
| `PI4/Backend/.env.example` | Modelo de variáveis de ambiente do Backend. |
| `PI4/Backend/Cti.csv` | Base bruta dos cenários CTI. |
| `PI4/Backend/main.py` | API FastAPI do chat. |
| `PI4/Backend/rag_engine.py` | Adaptador Backend para o motor RAG modular do Frontend. |
| `PI4/Backend/requirements.txt` | Dependências Python do Backend. |
| `PI4/Backend/cache/cti_limpo.parquet` | Cache da base limpa. |
| `PI4/Backend/cache/indicadores.parquet` | Cache dos indicadores anuais. |
| `PI4/Backend/cache/ranking.parquet` | Cache do ranking consolidado. |
| `PI4/Backend/documentos/manual_executivo_cti.md` | Manual técnico indexado pelo RAG. |
| `PI4/Backend/__pycache__/main.cpython-314.pyc` | Artefato bytecode de `main.py`. |
| `PI4/Backend/__pycache__/rag_engine.cpython-314.pyc` | Artefato bytecode de `rag_engine.py`. |

### 18.2 Frontend Raiz

| Caminho | Propósito |
|---|---|
| `PI4/Frontend/.streamlit/config.toml` | Configuração de tema e servidor Streamlit. |
| `PI4/Frontend/.streamlit/credentials.toml` | Credenciais locais vazias do Streamlit. |
| `PI4/Frontend/analise.ipynb` | Notebook exploratório. |
| `PI4/Frontend/app.py` | Entrada principal Streamlit. |
| `PI4/Frontend/chat_component.py` | Injeção do chat flutuante HTML. |
| `PI4/Frontend/chat_widget.html` | Widget HTML/JS do chat flutuante. |
| `PI4/Frontend/organizando.ipynb` | Notebook auxiliar de organização da base. |
| `PI4/Frontend/requirements_dashboard.txt` | Dependências Python do dashboard. |
| `PI4/Frontend/__pycache__/chat_component.cpython-314.pyc` | Artefato bytecode de `chat_component.py`. |

### 18.3 `src/config`

| Caminho | Propósito |
|---|---|
| `PI4/Frontend/src/__init__.py` | Inicializador do pacote `src`. |
| `PI4/Frontend/src/__pycache__/__init__.cpython-314.pyc` | Artefato bytecode do pacote `src`. |
| `PI4/Frontend/src/config/__init__.py` | Constantes globais. |
| `PI4/Frontend/src/config/glossary.py` | Glossário e textos de ajuda. |
| `PI4/Frontend/src/config/i18n.py` | Traduções PT/EN e helper `t`. |
| `PI4/Frontend/src/config/__pycache__/__init__.cpython-314.pyc` | Artefato bytecode de `config/__init__.py`. |
| `PI4/Frontend/src/config/__pycache__/glossary.cpython-314.pyc` | Artefato bytecode de `glossary.py`. |
| `PI4/Frontend/src/config/__pycache__/i18n.cpython-314.pyc` | Artefato bytecode de `i18n.py`. |

### 18.4 `src/controllers`

| Caminho | Propósito |
|---|---|
| `PI4/Frontend/src/controllers/__init__.py` | Fachada lazy-load dos controllers. |
| `PI4/Frontend/src/controllers/ai_sidebar_right.py` | Layout alternativo do assistente em painel lateral. |
| `PI4/Frontend/src/controllers/bootstrap.py` | Cache, contexto e cabeçalho do dashboard. |
| `PI4/Frontend/src/controllers/custom_analysis.py` | Estado e modal de análises customizadas. |
| `PI4/Frontend/src/controllers/data_input.py` | Upload, editor e substituição de dados. |
| `PI4/Frontend/src/controllers/headers.py` | Cabeçalhos, auditoria e labels de filtro. |
| `PI4/Frontend/src/controllers/navigation.py` | Roteamento das abas e personas. |
| `PI4/Frontend/src/controllers/page_setup.py` | CSS global e configuração Streamlit. |
| `PI4/Frontend/src/controllers/resilience.py` | Tratamento de exceções em views. |
| `PI4/Frontend/src/controllers/sidebar.py` | Sidebar, idioma e persona. |
| `PI4/Frontend/src/controllers/test_sandbox.py` | Sandbox da persona Teste. |
| `PI4/Frontend/src/controllers/charts/__init__.py` | Fachada dos gráficos. |
| `PI4/Frontend/src/controllers/charts/histograms.py` | Histogramas Plotly. |
| `PI4/Frontend/src/controllers/charts/risk_band.py` | Envelope/faixa de risco. |
| `PI4/Frontend/src/controllers/charts/time_series.py` | Helpers de séries temporais. |
| `PI4/Frontend/src/controllers/kpis/__init__.py` | Fachada dos KPIs. |
| `PI4/Frontend/src/controllers/kpis/ceo.py` | KPIs do CEO. |
| `PI4/Frontend/src/controllers/kpis/concession.py` | KPIs do Poder Concedente. |
| `PI4/Frontend/src/controllers/kpis/constants.py` | Constantes contábeis dos KPIs. |
| `PI4/Frontend/src/controllers/kpis/helpers.py` | Helpers de divisão/leitura de contas. |
| `PI4/Frontend/src/controllers/kpis/personas.py` | Roteador de KPIs por persona. |
| `PI4/Frontend/src/controllers/kpis/rendering.py` | Renderização visual dos cards. |
| `PI4/Frontend/src/controllers/kpis/shareholders.py` | KPIs dos acionistas. |
| `PI4/Frontend/src/controllers/**/__pycache__/*.pyc` | Artefatos bytecode dos controllers e subpacotes. |

### 18.5 `src/models`

| Caminho | Propósito |
|---|---|
| `PI4/Frontend/src/models/__init__.py` | Fachada lazy-load dos models. |
| `PI4/Frontend/src/models/classifiers.py` | Classificação por selos. |
| `PI4/Frontend/src/models/loaders.py` | Leitura e limpeza de dados. |
| `PI4/Frontend/src/models/analytics/__init__.py` | Fachada de analytics. |
| `PI4/Frontend/src/models/analytics/indicators.py` | Cálculo de indicadores e ranking. |
| `PI4/Frontend/src/models/analytics/summaries.py` | Resumos estatísticos. |
| `PI4/Frontend/src/models/financial_metrics/__init__.py` | Fachada das métricas dinâmicas. |
| `PI4/Frontend/src/models/financial_metrics/catalog.py` | Catálogo `FINANCIAL_METRICS_DICT`. |
| `PI4/Frontend/src/models/financial_metrics/series.py` | Séries temporais de métricas. |
| `PI4/Frontend/src/models/financial_metrics/types.py` | Tipo `FinancialMetric`. |
| `PI4/Frontend/src/models/financial_metrics/utils.py` | Utilitários numéricos. |
| `PI4/Frontend/src/models/formatting/__init__.py` | Fachada de formatação. |
| `PI4/Frontend/src/models/formatting/base.py` | Helpers base de número/NA. |
| `PI4/Frontend/src/models/formatting/comparisons.py` | Comparações e cenários padrão. |
| `PI4/Frontend/src/models/formatting/numbers.py` | Formatação R$, dias e percentuais. |
| `PI4/Frontend/src/models/formatting/scenarios.py` | IDs e rótulos de cenários. |
| `PI4/Frontend/src/models/formatting/texts.py` | Textos interpretativos de NCG/tesouraria/ciclo. |
| `PI4/Frontend/src/models/rag_engine/__init__.py` | Fachada do RAG. |
| `PI4/Frontend/src/models/rag_engine/answers.py` | Geração Gemini e fallback extrativo. |
| `PI4/Frontend/src/models/rag_engine/config.py` | Prompts e constantes do RAG. |
| `PI4/Frontend/src/models/rag_engine/context.py` | Contexto da tela para o RAG. |
| `PI4/Frontend/src/models/rag_engine/documents.py` | Documentos de manuais, glossário e cenários. |
| `PI4/Frontend/src/models/rag_engine/embeddings.py` | Embeddings TF-IDF. |
| `PI4/Frontend/src/models/rag_engine/engine.py` | Classe `RagEngine` e busca. |
| `PI4/Frontend/src/models/rag_engine/formatters.py` | Formatadores simples do RAG. |
| `PI4/Frontend/src/models/**/__pycache__/*.pyc` | Artefatos bytecode dos models e subpacotes. |

### 18.6 `src/views`

| Caminho | Propósito |
|---|---|
| `PI4/Frontend/src/views/__init__.py` | Fachada das views. |
| `PI4/Frontend/src/views/capital_giro.py` | Aba Capital de Giro. |
| `PI4/Frontend/src/views/como_ler.py` | Aba explicativa. |
| `PI4/Frontend/src/views/comparar.py` | Comparador operacional legado. |
| `PI4/Frontend/src/views/distribuicao.py` | Distribuição e probabilidades. |
| `PI4/Frontend/src/views/faixa_risco.py` | Faixa de risco. |
| `PI4/Frontend/src/views/mapeamento_risco.py` | Matriz risco x retorno. |
| `PI4/Frontend/src/views/prazos_ciclo.py` | Prazos e ciclo financeiro. |
| `PI4/Frontend/src/views/ai_assistant/__init__.py` | Fachada do assistente nativo. |
| `PI4/Frontend/src/views/ai_assistant/context.py` | Contexto/cache do assistente. |
| `PI4/Frontend/src/views/ai_assistant/panel.py` | UI Streamlit do assistente. |
| `PI4/Frontend/src/views/persona_tabs/__init__.py` | Fachada das sub-abas por persona. |
| `PI4/Frontend/src/views/persona_tabs/ceo.py` | Sub-abas CEO. |
| `PI4/Frontend/src/views/persona_tabs/common.py` | Cálculos comuns de DRE/balanço/financeiro. |
| `PI4/Frontend/src/views/persona_tabs/comparison.py` | Roteador do comparador por persona. |
| `PI4/Frontend/src/views/persona_tabs/comparison_ceo_cfo.py` | Comparadores CEO e CFO. |
| `PI4/Frontend/src/views/persona_tabs/comparison_concession.py` | Comparador do Poder Concedente. |
| `PI4/Frontend/src/views/persona_tabs/comparison_helpers.py` | Helpers do comparador. |
| `PI4/Frontend/src/views/persona_tabs/comparison_shareholders.py` | Comparador dos acionistas e gráfico EVA categórico. |
| `PI4/Frontend/src/views/persona_tabs/concession.py` | Sub-abas do Poder Concedente. |
| `PI4/Frontend/src/views/persona_tabs/custom_analysis.py` | Renderização de análise customizada. |
| `PI4/Frontend/src/views/persona_tabs/shareholders.py` | Sub-abas dos acionistas. |
| `PI4/Frontend/src/views/persona_tabs/styles.py` | Estilos A/B/C do comparador. |
| `PI4/Frontend/src/views/**/__pycache__/*.pyc` | Artefatos bytecode das views e subpacotes. |

