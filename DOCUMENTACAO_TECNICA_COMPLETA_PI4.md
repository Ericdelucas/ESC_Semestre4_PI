# Explicação técnica dos arquivos do projeto PI4

Este documento explica **para que serve cada arquivo do projeto, como funciona e com quais componentes se relaciona**. Não reproduz código-fonte, conteúdo integral de bases, notebooks ou bibliotecas. A pasta `engenharia` está excluída.

## Como o projeto funciona

O CTI transforma dados contábeis de cenários de concessão em indicadores, gráficos, relatórios e respostas de um assistente. O backend concentra regras financeiras, persistência, serviços e API FastAPI. O frontend usa Streamlit para apresentar os resultados e também importa funções do backend diretamente.

O fluxo financeiro principal é: **Cti.csv → leitores e normalização → métricas → cache Parquet → contexto do dashboard → telas e relatórios**. A autenticação segue outro fluxo: **tela de login → API → regras de autenticação → banco de usuários e logs**. O assistente combina documentos locais com o contexto financeiro e pode usar Gemini. Alertas de risco podem acionar o serviço SMTP.

Na configuração analisada, **USAR_SUPABASE = False**. O dashboard trabalha com Parquet/CSV e a autenticação usa SQLite local. A existência de arquivos e variáveis PostgreSQL não significa que a conexão remota esteja ativa.

## Localize a pasta e os arquivos

Cada seção abaixo contém uma explicação individual de **todos os arquivos diretamente dentro da pasta**, seguida das seções de suas subpastas. A lista é um menu: clique para ir às fichas dos arquivos.

- [./](#pasta-001): `.gitattributes`, `.python-version`, `Procfile`, `render.yaml`, `requirements.txt`, `runtime.txt`, `start.sh`
- [PI4/](#pasta-002): `.env.example`, `.gitignore`, `DOCUMENTATION.md`, `README.md`, `requirements.txt`
- [PI4/Backend/](#pasta-003): `.env`, `.env.example`, `.gitignore`, `.python-version`, `Cti.csv`, `Procfile`, `README.md`, `__init__.py`, `data_audit.py`, `diag.py`, `main.py`, `rag_engine.py`, `render.yaml`, `requirements.txt`, `runtime.py`
- [PI4/Backend/audit/](#pasta-004): `__init__.py`, `config.py`, `control_totals.py`, `duplicate_check.py`, `models.py`, `report_exporter.py`, `runner.py`, `structural_check.py`
- [PI4/Backend/cache/](#pasta-005): `cti_auth.db`, `cti_limpo.parquet`, `indicadores.parquet`, `ranking.parquet`
- [PI4/Backend/data_loader/](#pasta-006): `__init__.py`, `csv_reader.py`, `db.py`, `sql_reader.py`, `upload_normalizer.py`
- [PI4/Backend/db/](#pasta-007): `__init__.py`, `auth.py`, `database.py`, `models.py`, `seed.py`
- [PI4/Backend/documentos/](#pasta-008): `00_indice.md`
- [PI4/Backend/documentos/balanco/](#pasta-009): `01_ativo_circulante.md`, `02_realizavel_permanente.md`, `03_imobilizado_outorga_bar.md`, `04_passivo_circulante.md`, `05_exigivel_lp.md`, `06_patrimonio_liquido.md`, `07_totais_controle.md`
- [PI4/Backend/documentos/cenarios/](#pasta-010): `01_variaveis_estresse.md`, `02_cenarios_criticos.md`, `03_matriz_selos.md`
- [PI4/Backend/documentos/dre/](#pasta-011): `01_cascata_apuracao.md`, `02_receita_custos_ebitda.md`, `03_ebit_financeiro_ir_lucro.md`
- [PI4/Backend/documentos/fluxo_caixa/](#pasta-012): `01_fluxo_operacional.md`, `02_investimento_financeiro_saldos.md`
- [PI4/Backend/documentos/graficos/](#pasta-013): `01_ceo.md`, `02_cfo.md`, `03_acionistas.md`, `04_concedente.md`, `05_comparacao.md`
- [PI4/Backend/documentos/ia/](#pasta-014): `01_protocolo_resposta.md`, `02_mapa_navegacao.md`
- [PI4/Backend/documentos/indicadores/](#pasta-015): `01_margens.md`, `02_retorno_valor.md`, `03_break_even.md`, `04_ncg_tesouraria.md`, `05_prazos_ciclo.md`, `06_liquidez.md`, `07_capex_bar_dscr.md`, `08_ruina_percentis.md`, `09_ltv_cac.md`
- [PI4/Backend/documentos/visao_geral/](#pasta-016): `01_objeto_e_base.md`, `02_monte_carlo_percentis.md`, `03_constantes_e_leitura.md`, `04_stakeholders.md`, `manual_executivo_cti.md`
- [PI4/Backend/metrics/](#pasta-017): `__init__.py`, `column_resolver.py`, `commercial_kpis.py`, `financial_kpis.py`
- [PI4/Backend/relatorios/](#pasta-018): `Memorial_Calculo_Dashboard_Financeiro_CTI.docx`, `Relatorio_Riscos_Financeiros_CTI.pdf`, `verificacao_memorial_cti.json`
- [PI4/Backend/routers/](#pasta-019): `__init__.py`, `auth_router.py`, `chat_router.py`, `email.py`, `health_router.py`, `report_router.py`, `users.py`
- [PI4/Backend/scripts/](#pasta-020): `migrar_para_supabase.py`, `precompute_cache.py`, `seed_usuarios.py`
- [PI4/Backend/services/](#pasta-021): `__init__.py`, `chat_service.py`, `custom_report_service.py`, `dashboard_cache.py`, `dashboard_pipeline.py`, `email_service.py`, `memorial_report.py`, `metrics_calculator.py`, `rag_indexer.py`, `report_generator.py`, `report_insights.py`, `risk_alerts.py`, `risk_report.py`, `scenario_filter.py`
- [PI4/Backend/tests/](#pasta-022): `test_api_contracts.py`, `test_dashboard_pipeline.py`, `test_memorial_api.py`, `test_performance_regressions.py`, `test_report_notes.py`, `test_risk_report.py`
- [PI4/Frontend/](#pasta-023): `.env.example`, `Procfile`, `analise.ipynb`, `app.py`, `chat_component.py`, `chat_widget.html`, `organizando.ipynb`, `requirements.txt`, `requirements_dashboard.txt`
- [PI4/Frontend/.streamlit/](#pasta-024): `config.toml`, `credentials.toml`
- [PI4/Frontend/src/](#pasta-025): `__init__.py`
- [PI4/Frontend/src/components/](#pasta-026): `__init__.py`, `header_component.py`, `kpi_cards_component.py`, `sidebar_filters.py`
- [PI4/Frontend/src/config/](#pasta-027): `__init__.py`, `glossary.py`, `i18n.py`
- [PI4/Frontend/src/controllers/](#pasta-028): `__init__.py`, `ai_sidebar_right.py`, `auth.py`, `bootstrap.py`, `custom_analysis.py`, `data_input.py`, `headers.py`, `local_api.py`, `modals.py`, `navigation.py`, `ops_menu.py`, `page_setup.py`, `resilience.py`, `session_cookie.py`, `sidebar.py`, `stability.py`, `test_sandbox.py`
- [PI4/Frontend/src/controllers/charts/](#pasta-029): `__init__.py`, `histograms.py`, `risk_band.py`, `time_series.py`
- [PI4/Frontend/src/controllers/kpis/](#pasta-030): `__init__.py`, `ceo.py`, `concession.py`, `constants.py`, `helpers.py`, `personas.py`, `rendering.py`, `shareholders.py`
- [PI4/Frontend/src/models/](#pasta-031): `__init__.py`, `api_client.py`, `classifiers.py`, `loaders.py`
- [PI4/Frontend/src/models/analytics/](#pasta-032): `__init__.py`, `indicators.py`, `summaries.py`
- [PI4/Frontend/src/models/financial_metrics/](#pasta-033): `__init__.py`, `catalog.py`, `labels.py`, `series.py`, `types.py`, `utils.py`
- [PI4/Frontend/src/models/formatting/](#pasta-034): `__init__.py`, `base.py`, `comparisons.py`, `numbers.py`, `scenarios.py`, `tables.py`, `texts.py`
- [PI4/Frontend/src/models/rag_engine/](#pasta-035): `__init__.py`, `answers.py`, `config.py`, `context.py`, `documents.py`, `embeddings.py`, `engine.py`, `formatters.py`, `rbac.py`
- [PI4/Frontend/src/views/](#pasta-036): `__init__.py`, `capital_giro.py`, `como_ler.py`, `comparar.py`, `distribuicao.py`, `faixa_risco.py`, `mapeamento_risco.py`, `prazos_ciclo.py`, `report.py`
- [PI4/Frontend/src/views/ai_assistant/](#pasta-037): `__init__.py`, `context.py`, `panel.py`
- [PI4/Frontend/src/views/persona_tabs/](#pasta-038): `__init__.py`, `admin_users.py`, `audit.py`, `ceo.py`, `common.py`, `comparison.py`, `comparison_ceo_cfo.py`, `comparison_concession.py`, `comparison_helpers.py`, `comparison_shareholders.py`, `concession.py`, `custom_analysis.py`, `shareholders.py`, `styles.py`
- [PI4/scripts/](#pasta-039): `gerar_memorial_cti.py`, `precompute_cache.py`

## Explicação arquivo por arquivo

<a id="pasta-001"></a>

### Pasta `./`

Raiz do repositório: contém comandos de inicialização, configuração de publicação, dependências e este guia.

| Arquivo | O que faz |
|---|---|
| [.gitattributes](#arquivo-001) | Mantém as quebras de linha dos scripts de inicialização compatíveis com execução em Linux. |
| [.python-version](#arquivo-002) | Seleção local da versão Python |
| [Procfile](#arquivo-224) | Diz à plataforma de hospedagem como iniciar o processo web a partir da raiz. |
| [render.yaml](#arquivo-225) | Blueprint de publicação Render |
| [requirements.txt](#arquivo-226) | Manifesto de dependências Python |
| [runtime.txt](#arquivo-227) | Versão de runtime Python |
| [start.sh](#arquivo-228) | Inicialização conjunta API + dashboard |

<a id="arquivo-001"></a>

#### `.gitattributes`

**Para que serve:** Mantém as quebras de linha dos scripts de inicialização compatíveis com execução em Linux.

**Como funciona:** Define finais de linha LF para start.sh, Procfile e arquivos com extensão .sh. O Git usa essas regras ao tratar os arquivos.

**Como se relaciona com o restante:** Git aplica essas regras ao conteúdo versionado.

<a id="arquivo-002"></a>

#### `.python-version`

**Para que serve:** Seleção local da versão Python

**Como funciona:** Solicita Python 3.11.9 para ferramentas de seleção de versão, como pyenv.

**Como se relaciona com o restante:** Ferramentas como pyenv; comparar com runtime.txt, Render e pyvenv.cfg.

<a id="arquivo-224"></a>

#### `Procfile`

**Para que serve:** Diz à plataforma de hospedagem como iniciar o processo web a partir da raiz.

**Como funciona:** Aciona start.sh, que prepara o ambiente e inicia FastAPI e Streamlit no arranjo de serviço conjunto.

**Como se relaciona com o restante:** Process manager da plataforma executa o comando literal reproduzido abaixo.

<a id="arquivo-225"></a>

#### `render.yaml`

**Para que serve:** Blueprint de publicação Render

**Como funciona:** Define serviços, diretórios de build, comandos, health checks e nomes de variáveis do ambiente.

**Como se relaciona com o restante:** Render instala requirements e inicia Uvicorn/Streamlit conforme o blueprint; ver conteúdo integral para distinguir raiz e backend.

<a id="arquivo-226"></a>

#### `requirements.txt`

**Para que serve:** Manifesto de dependências Python

**Como funciona:** Cada requisito limita versões e/ou inclui outro manifesto; pip resolve e instala a árvore transitiva.

**Como se relaciona com o restante:** Consumido por comandos de build locais/Render; não representa necessariamente um lockfile do ambiente atual.

<a id="arquivo-227"></a>

#### `runtime.txt`

**Para que serve:** Versão de runtime Python

**Como funciona:** Declara python-3.11.9 para plataformas de hospedagem que reconhecem esse arquivo.

**Como se relaciona com o restante:** Buildpack/plataforma compatível interpreta o valor; não modifica o Python já instalado.

<a id="arquivo-228"></a>

#### `start.sh`

**Para que serve:** Inicialização conjunta API + dashboard

**Como funciona:** Configura PYTHONPATH e URLs locais, inicia Uvicorn em background e Streamlit na porta pública; tenta encerrar a API após a saída da interface.

**Como se relaciona com o restante:** Procfile da raiz chama este script; PI4/Backend/main.py e PI4/Frontend/app.py são os pontos de entrada.

<a id="pasta-002"></a>

### Pasta `PI4/`

Aplicação CTI: reúne backend, frontend, ferramentas e ambiente Python.

| Arquivo | O que faz |
|---|---|
| [.env.example](#arquivo-003) | Modelo ou configuração de variáveis de ambiente |
| [.gitignore](#arquivo-004) | Regras de arquivos ignorados |
| [DOCUMENTATION.md](#arquivo-116) | Documenta o tema “Documentação Técnica — Dashboard Financeiro CTI”. |
| [README.md](#arquivo-220) | Documenta o tema “ESC_Semestre4_PI · PI4”. |
| [requirements.txt](#arquivo-221) | Manifesto de dependências Python |

<a id="arquivo-003"></a>

#### `PI4/.env.example`

**Para que serve:** Modelo ou configuração de variáveis de ambiente

**Como funciona:** dotenv lê pares chave/valor; modelos .example documentam configuração e não são carregados automaticamente como .env.

**Como se relaciona com o restante:** Chaves conectam API, banco, SMTP, Gemini e frontend; os valores não são reproduzidos neste guia.

**Configurações declaradas, sem seus valores:** `GOOGLE_API_KEY`, `DATABASE_URL`, `BACKEND_URL`, `CTI_API_URL`, `API_HOST`, `API_PORT`, `SMTP_SERVER`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `EMAIL_REMETENTE`, `EMAIL_ALERTA_CEO`, `FORCE_EMAIL_ALERT_ON_LOGIN`.

<a id="arquivo-004"></a>

#### `PI4/.gitignore`

**Para que serve:** Regras de arquivos ignorados

**Como funciona:** Padrões delimitam arquivos que Git normalmente deixa de adicionar; arquivos já rastreados continuam rastreados.

**Como se relaciona com o restante:** Git e ferramentas de inventário podem aplicar esses padrões; este relatório percorre o disco e inclui os ignorados.

<a id="arquivo-116"></a>

#### `PI4/DOCUMENTATION.md`

**Para que serve:** Documenta o tema “Documentação Técnica — Dashboard Financeiro CTI”.

**Como funciona:** Texto interpretado por leitores; arquivos em documentos são candidatos à indexação e fragmentação pelo RAG.

**Como se relaciona com o restante:** Engenharia e/ou motor de recuperação documental; referências e conteúdo integral abaixo.

<a id="arquivo-220"></a>

#### `PI4/README.md`

**Para que serve:** Documenta o tema “ESC_Semestre4_PI · PI4”.

**Como funciona:** Texto interpretado por leitores; arquivos em documentos são candidatos à indexação e fragmentação pelo RAG.

**Como se relaciona com o restante:** Engenharia e/ou motor de recuperação documental; referências e conteúdo integral abaixo.

<a id="arquivo-221"></a>

#### `PI4/requirements.txt`

**Para que serve:** Manifesto de dependências Python

**Como funciona:** Cada requisito limita versões e/ou inclui outro manifesto; pip resolve e instala a árvore transitiva.

**Como se relaciona com o restante:** Consumido por comandos de build locais/Render; não representa necessariamente um lockfile do ambiente atual.

<a id="pasta-003"></a>

### Pasta `PI4/Backend/`

Camada FastAPI, domínio financeiro, persistência e serviços do ecossistema CTI.

| Arquivo | O que faz |
|---|---|
| [.env](#arquivo-005) | Modelo ou configuração de variáveis de ambiente |
| [.env.example](#arquivo-006) | Modelo ou configuração de variáveis de ambiente |
| [.gitignore](#arquivo-007) | Regras de arquivos ignorados |
| [.python-version](#arquivo-008) | Seleção local da versão Python |
| [Cti.csv](#arquivo-009) | É a base contábil de origem das análises CTI. |
| [Procfile](#arquivo-010) | Declara como iniciar somente a API a partir da pasta Backend. |
| [README.md](#arquivo-011) | Documenta o tema “Backend CTI”. |
| [__init__.py](#arquivo-012) | Servicos de backend do projeto CTI. |
| [data_audit.py](#arquivo-025) | Entrada CLI/importavel para auditoria da base CTI. |
| [diag.py](#arquivo-036) | Logs verbosos para o Live Tail da Render. Nunca imprime senhas. |
| [main.py](#arquivo-074) | É a entrada da API FastAPI do CTI. |
| [rag_engine.py](#arquivo-079) | RAG do Assistente CTI. Dados locais: ./Cti.csv, ./documentos/ e ./cache/. |
| [render.yaml](#arquivo-083) | Blueprint de publicação Render |
| [requirements.txt](#arquivo-084) | Manifesto de dependências Python |
| [runtime.py](#arquivo-092) | Ciclo de vida, CORS e logs da API CTI. |

<a id="arquivo-005"></a>

#### `PI4/Backend/.env`

**Para que serve:** Modelo ou configuração de variáveis de ambiente

**Como funciona:** dotenv lê pares chave/valor; modelos .example documentam configuração e não são carregados automaticamente como .env.

**Como se relaciona com o restante:** Chaves conectam API, banco, SMTP, Gemini e frontend; os valores não são reproduzidos neste guia.

**Configurações declaradas, sem seus valores:** `SMTP_SERVER`, `SMTP_PORT`, `SMTP_USER`, `EMAIL_SENDER`, `SMTP_PASSWORD`.

<a id="arquivo-006"></a>

#### `PI4/Backend/.env.example`

**Para que serve:** Modelo ou configuração de variáveis de ambiente

**Como funciona:** dotenv lê pares chave/valor; modelos .example documentam configuração e não são carregados automaticamente como .env.

**Como se relaciona com o restante:** Chaves conectam API, banco, SMTP, Gemini e frontend; os valores não são reproduzidos neste guia.

**Configurações declaradas, sem seus valores:** `GOOGLE_API_KEY`, `PORT`, `API_HOST`, `API_PORT`, `FRONTEND_URL`, `CORS_ORIGINS`, `CORS_ORIGIN_REGEX`, `DATABASE_URL`, `DATABASE_URL_POOLER`, `SUPABASE_POOLER_URL`, `SUPABASE_REGION`, `SMTP_SERVER`, `SMTP_PORT`, `SMTP_MODE`, `SMTP_TIMEOUT`, `SMTP_USER`, `SMTP_PASSWORD`, `EMAIL_REMETENTE`, `EMAIL_ALERTA_CEO`, `RISK_RUIN_THRESHOLD`, `RISK_LIQUIDEZ_MIN`, `FORCE_EMAIL_ALERT_ON_LOGIN`, `ALERT_DEBOUNCE_LOGIN_SECONDS`, `ALERT_DEBOUNCE_MANUAL_SECONDS`.

<a id="arquivo-007"></a>

#### `PI4/Backend/.gitignore`

**Para que serve:** Regras de arquivos ignorados

**Como funciona:** Padrões delimitam arquivos que Git normalmente deixa de adicionar; arquivos já rastreados continuam rastreados.

**Como se relaciona com o restante:** Git e ferramentas de inventário podem aplicar esses padrões; este relatório percorre o disco e inclui os ignorados.

<a id="arquivo-008"></a>

#### `PI4/Backend/.python-version`

**Para que serve:** Seleção local da versão Python

**Como funciona:** Arquivo textual usado por gerenciadores de versão para selecionar o interpretador.

**Como se relaciona com o restante:** Ferramentas como pyenv; comparar com runtime.txt, Render e pyvenv.cfg.

<a id="arquivo-009"></a>

#### `PI4/Backend/Cti.csv`

**Para que serve:** É a base contábil de origem das análises CTI.

**Como funciona:** Armazena registros em formato longo, com ano, cenário, conta e valor. Os leitores normalizam os registros antes de calcular métricas; o precompute converte o resultado em Parquet.

**Como se relaciona com o restante:** data_loader/csv_reader.py → métricas → cache Parquet → dashboard/relatórios; auditoria também lê por lotes.

<a id="arquivo-010"></a>

#### `PI4/Backend/Procfile`

**Para que serve:** Declara como iniciar somente a API a partir da pasta Backend.

**Como funciona:** Inicia Uvicorn carregando a aplicação main:app, escuta em todas as interfaces e usa a porta fornecida pela plataforma.

**Como se relaciona com o restante:** Process manager da plataforma executa o comando literal reproduzido abaixo.

<a id="arquivo-011"></a>

#### `PI4/Backend/README.md`

**Para que serve:** Documenta o tema “Backend CTI”.

**Como funciona:** Texto interpretado por leitores; arquivos em documentos são candidatos à indexação e fragmentação pelo RAG.

**Como se relaciona com o restante:** Engenharia e/ou motor de recuperação documental; referências e conteúdo integral abaixo.

<a id="arquivo-012"></a>

#### `PI4/Backend/__init__.py`

**Para que serve:** Servicos de backend do projeto CTI.

**Como funciona:** Reúne constantes, imports e exports para os consumidores do pacote.

**Como se relaciona com o restante:** Camada FastAPI, domínio financeiro, persistência e serviços do ecossistema CTI.

<a id="arquivo-025"></a>

#### `PI4/Backend/data_audit.py`

**Para que serve:** Entrada CLI/importavel para auditoria da base CTI.

**Como funciona:** Cria argumentos da auditoria CLI. Executa auditoria e imprime resumo no console.

**Como se relaciona com o restante:** Camada FastAPI, domínio financeiro, persistência e serviços do ecossistema CTI.

**Arquivos do projeto que utiliza:** `PI4/Backend/audit/__init__.py`, `PI4/Backend/audit/config.py`, `PI4/Backend/audit/report_exporter.py`.

**Outras dependências declaradas:** `argparse`, `pathlib`, `sys`.

**Responsabilidades internas:**

- `build_parser`: Cria argumentos da auditoria CLI.
- `main`: Executa auditoria e imprime resumo no console.

<a id="arquivo-036"></a>

#### `PI4/Backend/diag.py`

**Para que serve:** Logs verbosos para o Live Tail da Render. Nunca imprime senhas.

**Como funciona:** Log do gerador de PDF — stdout + stderr + logger (Render). Log exclusivo do Assistente de IA — stdout + stderr + logger (Render).

**Como se relaciona com o restante:** Camada FastAPI, domínio financeiro, persistência e serviços do ecossistema CTI.

**Arquivos que utilizam este módulo:** `PI4/Backend/data_loader/db.py`, `PI4/Backend/data_loader/sql_reader.py`, `PI4/Backend/db/database.py`, `PI4/Backend/rag_engine.py`, `PI4/Backend/runtime.py`, `PI4/Backend/services/chat_service.py`, `PI4/Backend/services/custom_report_service.py`, `PI4/Backend/services/dashboard_cache.py`, `PI4/Backend/services/dashboard_pipeline.py`, `PI4/Backend/services/metrics_calculator.py`, `PI4/Frontend/app.py`, `PI4/Frontend/src/controllers/bootstrap.py`, `PI4/Frontend/src/controllers/modals.py`, `PI4/Frontend/src/controllers/navigation.py`, `PI4/Frontend/src/controllers/sidebar.py`, `PI4/Frontend/src/controllers/stability.py`, `PI4/Frontend/src/models/rag_engine/answers.py`, `PI4/Frontend/src/models/rag_engine/documents.py`, `PI4/Frontend/src/models/rag_engine/engine.py`, `PI4/Frontend/src/views/ai_assistant/context.py`, `PI4/Frontend/src/views/ai_assistant/panel.py`, `PI4/Frontend/src/views/report.py`.

**Outras dependências declaradas:** `logging`, `os`, `sys`, `time`, `urllib`.

**Responsabilidades internas:**

- `log_relatorio`: Log do gerador de PDF — stdout + stderr + logger (Render).
- `log_ia`: Log exclusivo do Assistente de IA — stdout + stderr + logger (Render).

<a id="arquivo-074"></a>

#### `PI4/Backend/main.py`

**Para que serve:** É a entrada da API FastAPI do CTI.

**Como funciona:** Carrega as variáveis de ambiente, ajusta o caminho de imports, cria a aplicação, registra as rotas de usuários, e-mail, saúde, autenticação, chat e relatórios e aplica a configuração de execução.

**Como se relaciona com o restante:** Camada FastAPI, domínio financeiro, persistência e serviços do ecossistema CTI.

**Arquivos do projeto que utiliza:** `PI4/Backend/routers/auth_router.py`, `PI4/Backend/routers/chat_router.py`, `PI4/Backend/routers/email.py`, `PI4/Backend/routers/health_router.py`, `PI4/Backend/routers/report_router.py`, `PI4/Backend/routers/users.py`, `PI4/Backend/runtime.py`.

**Arquivos que utilizam este módulo:** `PI4/Backend/tests/test_api_contracts.py`, `PI4/Backend/tests/test_memorial_api.py`.

**Outras dependências declaradas:** `dotenv`, `fastapi`, `pathlib`, `sys`.

<a id="arquivo-079"></a>

#### `PI4/Backend/rag_engine.py`

**Para que serve:** RAG do Assistente CTI. Dados locais: ./Cti.csv, ./documentos/ e ./cache/.

**Como funciona:** Indexa a base CTI e devolve a resposta textual do consultor.

**Como se relaciona com o restante:** Camada FastAPI, domínio financeiro, persistência e serviços do ecossistema CTI.

**Arquivos do projeto que utiliza:** `PI4/Backend/data_loader/__init__.py`, `PI4/Backend/diag.py`, `PI4/Backend/metrics/__init__.py`, `PI4/Frontend/src/models/rag_engine/__init__.py`.

**Arquivos que utilizam este módulo:** `PI4/Backend/services/chat_service.py`.

**Outras dependências declaradas:** `dotenv`, `os`, `pandas`, `pathlib`, `sys`.

**Responsabilidades internas:**

- `CTIRag`: Indexa a base CTI e devolve a resposta textual do consultor.

**Operações concretas realizadas neste arquivo:**

- Carrega tabelas previamente persistidas em Parquet.

<a id="arquivo-083"></a>

#### `PI4/Backend/render.yaml`

**Para que serve:** Blueprint de publicação Render

**Como funciona:** Define serviços, diretórios de build, comandos, health checks e nomes de variáveis do ambiente.

**Como se relaciona com o restante:** Render instala requirements e inicia Uvicorn/Streamlit conforme o blueprint; ver conteúdo integral para distinguir raiz e backend.

<a id="arquivo-084"></a>

#### `PI4/Backend/requirements.txt`

**Para que serve:** Manifesto de dependências Python

**Como funciona:** Cada requisito limita versões e/ou inclui outro manifesto; pip resolve e instala a árvore transitiva.

**Como se relaciona com o restante:** Consumido por comandos de build locais/Render; não representa necessariamente um lockfile do ambiente atual.

<a id="arquivo-092"></a>

#### `PI4/Backend/runtime.py`

**Para que serve:** Ciclo de vida, CORS e logs da API CTI.

**Como funciona:** Regista os middlewares existentes sem alterar a politica CORS.

**Como se relaciona com o restante:** Camada FastAPI, domínio financeiro, persistência e serviços do ecossistema CTI.

**Arquivos do projeto que utiliza:** `PI4/Backend/db/__init__.py`, `PI4/Backend/diag.py`, `PI4/Backend/services/email_service.py`.

**Arquivos que utilizam este módulo:** `PI4/Backend/main.py`, `PI4/Backend/routers/auth_router.py`, `PI4/Backend/routers/health_router.py`.

**Outras dependências declaradas:** `contextlib`, `fastapi`, `logging`, `os`, `pathlib`, `sys`.

**Responsabilidades internas:**

- `configure_application`: Regista os middlewares existentes sem alterar a politica CORS.

<a id="pasta-004"></a>

### Pasta `PI4/Backend/audit/`

Auditoria incremental de estrutura, duplicidades e totais de controle; consome lotes normalizados e acumula o diagnóstico.

| Arquivo | O que faz |
|---|---|
| [__init__.py](#arquivo-013) | Auditoria, validacao e reconciliacao de bases CTI. |
| [config.py](#arquivo-014) | Centraliza as regras e os caminhos usados pela auditoria da base CTI. |
| [control_totals.py](#arquivo-015) | Confere a base por meio de totais de controle e perfis de qualidade por conta. |
| [duplicate_check.py](#arquivo-016) | Detecta tanto linhas totalmente repetidas quanto registros que repetem a mesma chave contábil, mesmo que os valores sejam diferentes. |
| [models.py](#arquivo-017) | Define as estruturas de memória que guardam os resultados parciais da auditoria enquanto os lotes da base são lidos. |
| [report_exporter.py](#arquivo-018) | Transforma o diagnóstico da auditoria em uma apresentação legível no terminal ou em arquivos JSON e Markdown. |
| [runner.py](#arquivo-019) | Coordena uma auditoria completa: escolhe a fonte, percorre os lotes e reúne os diagnósticos em um único resultado. |
| [structural_check.py](#arquivo-020) | Verificacao estrutural: leitura, colunas, tipos, nulos e anomalias. |

<a id="arquivo-013"></a>

#### `PI4/Backend/audit/__init__.py`

**Para que serve:** Auditoria, validacao e reconciliacao de bases CTI.

**Como funciona:** Reúne constantes, imports e exports para os consumidores do pacote.

**Como se relaciona com o restante:** Auditoria incremental de estrutura, duplicidades e totais de controle; consome lotes normalizados e acumula o diagnóstico.

**Arquivos do projeto que utiliza:** `PI4/Backend/audit/runner.py`.

**Arquivos que utilizam este módulo:** `PI4/Backend/data_audit.py`.

<a id="arquivo-014"></a>

#### `PI4/Backend/audit/config.py`

**Para que serve:** Centraliza as regras e os caminhos usados pela auditoria da base CTI.

**Como funciona:** Define colunas esperadas, chave de negócio, lotes de leitura, horizonte da concessão e contas críticas. Monta os grupos de contas a partir do catálogo de métricas para que as verificações usem as mesmas referências financeiras.

**Como se relaciona com o restante:** Auditoria incremental de estrutura, duplicidades e totais de controle; consome lotes normalizados e acumula o diagnóstico.

**Arquivos do projeto que utiliza:** `PI4/Backend/metrics/financial_kpis.py`.

**Arquivos que utilizam este módulo:** `PI4/Backend/audit/control_totals.py`, `PI4/Backend/audit/duplicate_check.py`, `PI4/Backend/audit/report_exporter.py`, `PI4/Backend/audit/runner.py`, `PI4/Backend/audit/structural_check.py`, `PI4/Backend/data_audit.py`.

**Outras dependências declaradas:** `pathlib`.

<a id="arquivo-015"></a>

#### `PI4/Backend/audit/control_totals.py`

**Para que serve:** Confere a base por meio de totais de controle e perfis de qualidade por conta.

**Como funciona:** Recebe cada lote normalizado, acumula contagens, valores, valores absolutos, ausências, cenários e anos. Depois resume somas, médias e percentuais de valores ausentes por conta e grupo contábil.

**Como se relaciona com o restante:** Auditoria incremental de estrutura, duplicidades e totais de controle; consome lotes normalizados e acumula o diagnóstico.

**Arquivos do projeto que utiliza:** `PI4/Backend/audit/config.py`, `PI4/Backend/audit/models.py`.

**Arquivos que utilizam este módulo:** `PI4/Backend/audit/runner.py`.

**Outras dependências declaradas:** `pandas`, `typing`.

**Responsabilidades internas:**

- `update_accounts`: Acumula totais, contagens e qualidade por conta.
- `control_totals`: Calcula somas, somas absolutas e medias por grupo de controle.
- `account_quality`: Resume qualidade e totais por conta individual.

**Operações concretas realizadas neste arquivo:**

- Agrupa registros para calcular resultados por conta, ano, cenário ou outra chave indicada no módulo.
- Converte entradas para números e trata conversões inválidas conforme as opções utilizadas.

<a id="arquivo-016"></a>

#### `PI4/Backend/audit/duplicate_check.py`

**Para que serve:** Detecta tanto linhas totalmente repetidas quanto registros que repetem a mesma chave contábil, mesmo que os valores sejam diferentes.

**Como funciona:** Para cada lote, substitui ausências por None e transforma os registros em tuplas. Um contador usa ANO, CENA, CONTA e VALOR; outro usa somente ANO, CENA e CONTA. Ao finalizar, seleciona chaves com contagem maior que um e calcula número de grupos, linhas envolvidas, linhas excedentes e exemplos. Assim, três ocorrências da mesma chave representam um grupo, três linhas envolvidas e duas excedentes.

**Como se relaciona com o restante:** Lê as colunas e a chave de negócio de config.py, guarda os contadores em AuditAccumulator de models.py e é acionado por runner.py em cada lote. Apenas identifica e resume duplicidades: não apaga registros da base.

**Arquivos do projeto que utiliza:** `PI4/Backend/audit/config.py`, `PI4/Backend/audit/models.py`.

**Arquivos que utilizam este módulo:** `PI4/Backend/audit/runner.py`.

**Outras dependências declaradas:** `collections`, `pandas`, `typing`.

**Responsabilidades internas:**

- `update_duplicates`: Acumula contadores de duplicidade em memoria compacta.
- `summarize_duplicates`: Resume grupos duplicados e exemplos.

<a id="arquivo-017"></a>

#### `PI4/Backend/audit/models.py`

**Para que serve:** Define as estruturas de memória que guardam os resultados parciais da auditoria enquanto os lotes da base são lidos.

**Como funciona:** ColumnProfile acompanha nulos, textos vazios, tipos encontrados, falhas de conversão e limites mínimo/máximo de uma coluna. AuditAccumulator reúne quantidade de linhas, contadores de duplicidade, totais por conta, cenários, anos e amostras de problemas. São dataclasses com valores iniciais próprios para cada execução; não são tabelas de banco de dados.

**Como se relaciona com o restante:** runner.py cria o acumulador. structural_check.py atualiza perfis e anomalias; duplicate_check.py atualiza as chaves repetidas; control_totals.py atualiza os totais. O runner converte esse estado em um relatório.

**Arquivos que utilizam este módulo:** `PI4/Backend/audit/control_totals.py`, `PI4/Backend/audit/duplicate_check.py`, `PI4/Backend/audit/runner.py`, `PI4/Backend/audit/structural_check.py`.

**Outras dependências declaradas:** `collections`, `dataclasses`, `typing`.

**Responsabilidades internas:**

- `ColumnProfile`: Perfil acumulado de uma coluna auditada.
- `AuditAccumulator`: Estado incremental da auditoria em chunks.

<a id="arquivo-018"></a>

#### `PI4/Backend/audit/report_exporter.py`

**Para que serve:** Transforma o diagnóstico da auditoria em uma apresentação legível no terminal ou em arquivos JSON e Markdown.

**Como funciona:** Recebe o dicionário produzido pelo runner, organiza estrutura, tipos, duplicidades, ausências, anomalias e totais para o terminal, formata dinheiro no padrão brasileiro e converte escalares NumPy/pandas para valores serializáveis. Para salvar, cria o diretório de saída, monta um nome com data/hora e valida o formato solicitado. O Markdown é um resumo; o JSON preserva o relatório estruturado.

**Como se relaciona com o restante:** Usa REPORT_DIR de config.py. runner.py chama a gravação quando save_report está habilitado; data_audit.py usa a formatação de terminal. Este módulo não lê nem altera a base contábil.

**Arquivos do projeto que utiliza:** `PI4/Backend/audit/config.py`.

**Arquivos que utilizam este módulo:** `PI4/Backend/audit/runner.py`, `PI4/Backend/data_audit.py`.

**Outras dependências declaradas:** `datetime`, `json`, `pathlib`, `typing`.

**Responsabilidades internas:**

- `_json_default`: Converte escalares pandas/numpy para JSON nativo.
- `format_money`: Formata numero no padrao brasileiro.
- `format_console_report`: Formata relatorio para terminal.
- `save_audit_report`: Salva relatorio JSON ou Markdown dentro do backend.
- `format_markdown_report`: Gera relatorio Markdown resumido.

<a id="arquivo-019"></a>

#### `PI4/Backend/audit/runner.py`

**Para que serve:** Coordena uma auditoria completa: escolhe a fonte, percorre os lotes e reúne os diagnósticos em um único resultado.

**Como funciona:** Escolhe CSV ou SQL; SQL exige um nome de tabela e o caminho relativo de CSV é resolvido a partir do backend. Cria AuditAccumulator, normaliza cada lote e atualiza perfis, duplicidades, contas e anomalias. No fim calcula duração, estrutura, qualidade por coluna, duplicidades, ausências, regras de tratamento e totais. Retorna um dicionário e, opcionalmente, grava JSON ou Markdown.

**Como se relaciona com o restante:** É disponibilizado por audit/__init__.py. Usa structural_check.py para leitura e validação, duplicate_check.py para repetições, control_totals.py para reconciliação, models.py para estado e report_exporter.py para exportação.

**Arquivos do projeto que utiliza:** `PI4/Backend/audit/config.py`, `PI4/Backend/audit/control_totals.py`, `PI4/Backend/audit/duplicate_check.py`, `PI4/Backend/audit/models.py`, `PI4/Backend/audit/report_exporter.py`, `PI4/Backend/audit/structural_check.py`.

**Arquivos que utilizam este módulo:** `PI4/Backend/audit/__init__.py`.

**Outras dependências declaradas:** `datetime`, `pathlib`, `typing`.

**Responsabilidades internas:**

- `run_audit`: Executa auditoria da base CTI e retorna relatorio estruturado.

<a id="arquivo-020"></a>

#### `PI4/Backend/audit/structural_check.py`

**Para que serve:** Verificacao estrutural: leitura, colunas, tipos, nulos e anomalias.

**Como funciona:** Serializa exemplos pequenos sem valores pandas nao JSON. Le CSV CTI em chunks com tratamento de erros claro. Le uma tabela SQL em chunks via SQLAlchemy. Normaliza nomes, datas de ano e valores monetarios. Acumula perfil de tipos, nulos e limites numericos. Registra exemplos de ausentes criticos, negativos e periodos invalidos. Gera resumo de qualidade por coluna. Regras metodologicas para ausentes.

**Como se relaciona com o restante:** Auditoria incremental de estrutura, duplicidades e totais de controle; consome lotes normalizados e acumula o diagnóstico.

**Arquivos do projeto que utiliza:** `PI4/Backend/audit/config.py`, `PI4/Backend/audit/models.py`, `PI4/Backend/data_loader/__init__.py`.

**Arquivos que utilizam este módulo:** `PI4/Backend/audit/runner.py`.

**Outras dependências declaradas:** `pandas`, `sqlalchemy`, `typing`.

**Responsabilidades internas:**

- `sample_records`: Serializa exemplos pequenos sem valores pandas nao JSON.
- `read_csv_chunks`: Le CSV CTI em chunks com tratamento de erros claro.
- `read_sql_chunks`: Le uma tabela SQL em chunks via SQLAlchemy.
- `prepare_cti_chunk`: Normaliza nomes, datas de ano e valores monetarios.
- `update_profiles`: Acumula perfil de tipos, nulos e limites numericos.
- `update_anomalies`: Registra exemplos de ausentes criticos, negativos e periodos invalidos.
- `summarize_columns`: Gera resumo de qualidade por coluna.
- `imputation_rules`: Regras metodologicas para ausentes.

**Operações concretas realizadas neste arquivo:**

- Lê tabelas CSV e as transforma em DataFrames.
- Converte entradas para números e trata conversões inválidas conforme as opções utilizadas.
- Aplica os valores de substituição definidos para dados ausentes.
- Configura uma conexão SQLAlchemy com o banco.

<a id="pasta-005"></a>

### Pasta `PI4/Backend/cache/`

Persistência local derivada: Parquet para dados/indicadores/ranking e SQLite para autenticação; consumida pelo dashboard e pelos serviços.

| Arquivo | O que faz |
|---|---|
| [cti_auth.db](#arquivo-021) | Persistência SQLite ou arquivo auxiliar |
| [cti_limpo.parquet](#arquivo-022) | Guarda a base contábil já normalizada para evitar reler e tratar o CSV a cada inicialização. |
| [indicadores.parquet](#arquivo-023) | Guarda os indicadores financeiros já calculados por cenário e ano. |
| [ranking.parquet](#arquivo-024) | Guarda o resumo e a classificação financeira dos cenários. |

<a id="arquivo-021"></a>

#### `PI4/Backend/cache/cti_auth.db`

**Para que serve:** Persistência SQLite ou arquivo auxiliar

**Como funciona:** Banco relacional local; WAL/SHM, quando presentes, apoiam transações e concorrência.

**Como se relaciona com o restante:** db/database.py, db/models.py, auth.py e rotas usam usuários/logs; não são copiados registros privados para o documento.

<a id="arquivo-022"></a>

#### `PI4/Backend/cache/cti_limpo.parquet`

**Para que serve:** Guarda a base contábil já normalizada para evitar reler e tratar o CSV a cada inicialização.

**Como funciona:** Preserva a tabela longa de contas por cenário e ano em formato colunar. Serve de base às consultas e demonstrativos que precisam das contas originais, não apenas dos indicadores derivados.

**Como se relaciona com o restante:** dashboard_cache.py e precompute_cache.py escrevem/leem; dados servem a métricas, filtros e relatórios.

<a id="arquivo-023"></a>

#### `PI4/Backend/cache/indicadores.parquet`

**Para que serve:** Guarda os indicadores financeiros já calculados por cenário e ano.

**Como funciona:** Persiste a tabela derivada das contas contábeis. O dashboard carrega seus valores para filtros, gráficos, séries e cartões, evitando recalcular toda a base.

**Como se relaciona com o restante:** dashboard_cache.py e precompute_cache.py escrevem/leem; dados servem a métricas, filtros e relatórios.

<a id="arquivo-024"></a>

#### `PI4/Backend/cache/ranking.parquet`

**Para que serve:** Guarda o resumo e a classificação financeira dos cenários.

**Como funciona:** Concentra resultados usados para comparar cenários, aplicar selos e analisar risco e retorno. É carregado junto com a base limpa e os indicadores; não substitui a tabela detalhada de contas.

**Como se relaciona com o restante:** dashboard_cache.py e precompute_cache.py escrevem/leem; dados servem a métricas, filtros e relatórios.

<a id="pasta-006"></a>

### Pasta `PI4/Backend/data_loader/`

Entrada de dados: CSV CTI, uploads CSV/XLSX e infraestrutura SQL; entrega DataFrames normalizados ao cálculo e à auditoria.

| Arquivo | O que faz |
|---|---|
| [__init__.py](#arquivo-026) | Leitura e normalizacao de bases de dados CTI. |
| [csv_reader.py](#arquivo-027) | Carregamento otimizado da base CTI em formato longo. |
| [db.py](#arquivo-028) | Reúne a infraestrutura de conexão PostgreSQL/Supabase usada pelos leitores SQL. |
| [sql_reader.py](#arquivo-029) | Leituras SQL da tabela cti_dados — filtros e agregacoes no PostgreSQL. |
| [upload_normalizer.py](#arquivo-030) | Leitura e normalizacao tolerante de uploads CSV/XLSX para o formato longo CTI. |

<a id="arquivo-026"></a>

#### `PI4/Backend/data_loader/__init__.py`

**Para que serve:** Leitura e normalizacao de bases de dados CTI.

**Como funciona:** Reúne constantes, imports e exports para os consumidores do pacote.

**Como se relaciona com o restante:** Entrada de dados: CSV CTI, uploads CSV/XLSX e infraestrutura SQL; entrega DataFrames normalizados ao cálculo e à auditoria.

**Arquivos do projeto que utiliza:** `PI4/Backend/data_loader/csv_reader.py`, `PI4/Backend/data_loader/upload_normalizer.py`.

**Arquivos que utilizam este módulo:** `PI4/Backend/audit/structural_check.py`, `PI4/Backend/metrics/financial_kpis.py`, `PI4/Backend/rag_engine.py`, `PI4/Backend/scripts/precompute_cache.py`, `PI4/Backend/services/dashboard_cache.py`, `PI4/Backend/services/metrics_calculator.py`, `PI4/Backend/tests/test_dashboard_pipeline.py`, `PI4/Frontend/src/models/loaders.py`.

<a id="arquivo-027"></a>

#### `PI4/Backend/data_loader/csv_reader.py`

**Para que serve:** Carregamento otimizado da base CTI em formato longo.

**Como funciona:** Converte numeros brasileiros, preservando series numericas. Remove espacos redundantes dos nomes de conta. Retorna modulo financeiro para saldos com sinais contabeis mistos. Compacta tipos para reduzir uso de memoria. Le Cti.csv em chunks (ou parquet se ja existir). Sem PostgreSQL. Separa BP, DRE e DFC por prefixo da conta. Soma uma lista de contas por ano e cenario.

**Como se relaciona com o restante:** Entrada de dados: CSV CTI, uploads CSV/XLSX e infraestrutura SQL; entrega DataFrames normalizados ao cálculo e à auditoria.

**Arquivos que utilizam este módulo:** `PI4/Backend/data_loader/__init__.py`, `PI4/Backend/data_loader/sql_reader.py`, `PI4/Backend/data_loader/upload_normalizer.py`, `PI4/Backend/scripts/migrar_para_supabase.py`, `PI4/Backend/tests/test_dashboard_pipeline.py`.

**Outras dependências declaradas:** `os`, `pandas`, `pathlib`.

**Responsabilidades internas:**

- `parse_valor_br`: Converte numeros brasileiros, preservando series numericas.
- `normalizar_conta`: Remove espacos redundantes dos nomes de conta.
- `magnitude`: Retorna modulo financeiro para saldos com sinais contabeis mistos.
- `otimizar_base_cti`: Compacta tipos para reduzir uso de memoria.
- `load_cti_csv`: Le Cti.csv em chunks (ou parquet se ja existir). Sem PostgreSQL.
- `separar_demonstrativos`: Separa BP, DRE e DFC por prefixo da conta.
- `soma_contas`: Soma uma lista de contas por ano e cenario.

**Operações concretas realizadas neste arquivo:**

- Lê tabelas CSV e as transforma em DataFrames.
- Carrega tabelas previamente persistidas em Parquet.
- Grava DataFrames no cache Parquet.
- Agrupa registros para calcular resultados por conta, ano, cenário ou outra chave indicada no módulo.
- Converte entradas para números e trata conversões inválidas conforme as opções utilizadas.
- Aplica os valores de substituição definidos para dados ausentes.

<a id="arquivo-028"></a>

#### `PI4/Backend/data_loader/db.py`

**Para que serve:** Reúne a infraestrutura de conexão PostgreSQL/Supabase usada pelos leitores SQL.

**Como funciona:** Trata URLs, SSL, resolução DNS/IPv4, escolha de conexão e reutilização da engine. Contudo, a constante USAR_SUPABASE está definida como falsa: esses caminhos não ativam o banco remoto na configuração atual.

**Como se relaciona com o restante:** Entrada de dados: CSV CTI, uploads CSV/XLSX e infraestrutura SQL; entrega DataFrames normalizados ao cálculo e à auditoria.

**Arquivos do projeto que utiliza:** `PI4/Backend/diag.py`.

**Arquivos que utilizam este módulo:** `PI4/Backend/data_loader/sql_reader.py`, `PI4/Backend/db/database.py`.

**Outras dependências declaradas:** `dotenv`, `os`, `pathlib`, `socket`, `sqlalchemy`, `urllib`.

**Responsabilidades internas:**

- `postgres_ipv4_disponivel`: True so se alguma URL configurada (pooler ou directa) tiver A/IPv4.
- `normalize_database_url`: psycopg2 + sslmode=require. Re-codifica a senha apos o parse.
- `candidate_urls`: So URLs do ambiente. Nao adivinhar dezenas de poolers (isso causava 429).
- `preferred_database_url`: Primeira URL com IPv4. Host so-IPv6 e inutil na Render.
- `get_cti_engine`: Tenta host directo em IPv4; se falhar, pooler. Nao imprime senha.

**Operações concretas realizadas neste arquivo:**

- Configura uma conexão SQLAlchemy com o banco.

<a id="arquivo-029"></a>

#### `PI4/Backend/data_loader/sql_reader.py`

**Para que serve:** Leituras SQL da tabela cti_dados — filtros e agregacoes no PostgreSQL.

**Como funciona:** Fatia filtrada no banco. 'Todos' os cenarios devolve media por ANO/CONTA. Pivota contas canonicas no PostgreSQL: ~cenarios x anos, sem o CSV de 1M.

**Como se relaciona com o restante:** Entrada de dados: CSV CTI, uploads CSV/XLSX e infraestrutura SQL; entrega DataFrames normalizados ao cálculo e à auditoria.

**Arquivos do projeto que utiliza:** `PI4/Backend/data_loader/csv_reader.py`, `PI4/Backend/data_loader/db.py`, `PI4/Backend/diag.py`, `PI4/Backend/metrics/column_resolver.py`, `PI4/Backend/metrics/financial_kpis.py`, `PI4/Backend/services/dashboard_pipeline.py`.

**Outras dependências declaradas:** `pandas`, `sqlalchemy`, `time`.

**Responsabilidades internas:**

- `fetch_recorte`: Fatia filtrada no banco. 'Todos' os cenarios devolve media por ANO/CONTA.
- `fetch_wide_indicadores`: Pivota contas canonicas no PostgreSQL: ~cenarios x anos, sem o CSV de 1M.

<a id="arquivo-030"></a>

#### `PI4/Backend/data_loader/upload_normalizer.py`

**Para que serve:** Leitura e normalizacao tolerante de uploads CSV/XLSX para o formato longo CTI.

**Como funciona:** Se a primeira linha for titulo, promove a linha com mais aliases a cabecalho. Le CSV/Excel e devolve o DataFrame cru mais avisos de leitura. Valores unicos sem passar lista crua a pd.unique (pandas 2.2+ recusa list). Normaliza qualquer grade enviada para ANO/CENA/CONTA/VALOR/ano_num. Le e normaliza um CSV/Excel enviado pelo painel.

**Como se relaciona com o restante:** Entrada de dados: CSV CTI, uploads CSV/XLSX e infraestrutura SQL; entrega DataFrames normalizados ao cálculo e à auditoria.

**Arquivos do projeto que utiliza:** `PI4/Backend/data_loader/csv_reader.py`, `PI4/Backend/metrics/column_resolver.py`.

**Arquivos que utilizam este módulo:** `PI4/Backend/data_loader/__init__.py`.

**Outras dependências declaradas:** `io`, `logging`, `pandas`, `pathlib`, `re`, `traceback`, `unicodedata`.

**Responsabilidades internas:**

- `_promover_cabecalho`: Se a primeira linha for titulo, promove a linha com mais aliases a cabecalho.
- `ler_upload`: Le CSV/Excel e devolve o DataFrame cru mais avisos de leitura.
- `_unicos`: Valores unicos sem passar lista crua a pd.unique (pandas 2.2+ recusa list).
- `normalizar_upload`: Normaliza qualquer grade enviada para ANO/CENA/CONTA/VALOR/ano_num.
- `importar_planilha`: Le e normaliza um CSV/Excel enviado pelo painel.

**Operações concretas realizadas neste arquivo:**

- Lê tabelas CSV e as transforma em DataFrames.
- Lê planilhas Excel para tabelas.
- Converte uma tabela larga em registros no formato longo.
- Converte entradas para números e trata conversões inválidas conforme as opções utilizadas.
- Aplica os valores de substituição definidos para dados ausentes.

<a id="pasta-007"></a>

### Pasta `PI4/Backend/db/`

Persistência de usuários e logs com SQLAlchemy, sessões transacionais e SQLite local; a integração PostgreSQL está desativada pela configuração atual.

| Arquivo | O que faz |
|---|---|
| [__init__.py](#arquivo-031) | Persistencia local de usuarios e logs de acesso. |
| [auth.py](#arquivo-032) | Hash de senha, seed, login e auditoria de acesso. |
| [database.py](#arquivo-033) | Gerencia a conexão e as transações do banco de usuários e logs. |
| [models.py](#arquivo-034) | Define a estrutura das tabelas de usuários e registros de acesso. |
| [seed.py](#arquivo-035) | Carga inicial da tabela usuarios. |

<a id="arquivo-031"></a>

#### `PI4/Backend/db/__init__.py`

**Para que serve:** Persistencia local de usuarios e logs de acesso.

**Como funciona:** Reúne constantes, imports e exports para os consumidores do pacote.

**Como se relaciona com o restante:** Persistência de usuários e logs com SQLAlchemy, sessões transacionais e SQLite local; a integração PostgreSQL está desativada pela configuração atual.

**Arquivos do projeto que utiliza:** `PI4/Backend/db/database.py`, `PI4/Backend/db/models.py`, `PI4/Backend/db/seed.py`.

**Arquivos que utilizam este módulo:** `PI4/Backend/db/database.py`, `PI4/Backend/routers/auth_router.py`, `PI4/Backend/routers/email.py`, `PI4/Backend/routers/health_router.py`, `PI4/Backend/routers/users.py`, `PI4/Backend/runtime.py`, `PI4/Backend/scripts/seed_usuarios.py`, `PI4/Backend/tests/test_api_contracts.py`, `PI4/Frontend/src/controllers/auth.py`.

<a id="arquivo-032"></a>

#### `PI4/Backend/db/auth.py`

**Para que serve:** Hash de senha, seed, login e auditoria de acesso.

**Como funciona:** Configura os valores e as integrações compartilhadas indicados por este módulo.

**Como se relaciona com o restante:** Persistência de usuários e logs com SQLAlchemy, sessões transacionais e SQLite local; a integração PostgreSQL está desativada pela configuração atual.

**Arquivos do projeto que utiliza:** `PI4/Backend/db/models.py`.

**Arquivos que utilizam este módulo:** `PI4/Backend/db/seed.py`, `PI4/Backend/routers/auth_router.py`, `PI4/Backend/routers/email.py`, `PI4/Backend/routers/users.py`, `PI4/Backend/tests/test_api_contracts.py`, `PI4/Frontend/src/controllers/auth.py`.

**Outras dependências declaradas:** `datetime`, `hashlib`, `hmac`, `os`, `sqlalchemy`.

**Operações concretas realizadas neste arquivo:**

- Monta consultas SQLAlchemy aos modelos de persistência.

<a id="arquivo-033"></a>

#### `PI4/Backend/db/database.py`

**Para que serve:** Gerencia a conexão e as transações do banco de usuários e logs.

**Como funciona:** Cria a engine e as sessões SQLAlchemy, inicializa tabelas e adapta uma coluna SQLite quando necessário. Confirma transações bem-sucedidas e desfaz transações com erro. Na configuração atual usa SQLite; mantém infraestrutura para PostgreSQL e fallback local.

**Como se relaciona com o restante:** Persistência de usuários e logs com SQLAlchemy, sessões transacionais e SQLite local; a integração PostgreSQL está desativada pela configuração atual.

**Arquivos do projeto que utiliza:** `PI4/Backend/data_loader/db.py`, `PI4/Backend/db/__init__.py`, `PI4/Backend/db/models.py`, `PI4/Backend/diag.py`.

**Arquivos que utilizam este módulo:** `PI4/Backend/db/__init__.py`, `PI4/Backend/db/models.py`, `PI4/Backend/db/seed.py`, `PI4/Backend/tests/test_api_contracts.py`.

**Outras dependências declaradas:** `contextlib`, `os`, `pathlib`, `sqlalchemy`, `urllib`.

**Responsabilidades internas:**

- `init_db`: Cria tabelas. Se o Postgres falhar (DNS), cai para SQLite e a API sobe.

**Operações concretas realizadas neste arquivo:**

- Configura uma conexão SQLAlchemy com o banco.
- Confirma as alterações da transação de banco.
- Desfaz a transação em caso de falha.

<a id="arquivo-034"></a>

#### `PI4/Backend/db/models.py`

**Para que serve:** Define a estrutura das tabelas de usuários e registros de acesso.

**Como funciona:** Declara os campos e restrições dos modelos SQLAlchemy Usuario e LogAcesso: identificação, e-mail, hash de senha, função, situação, administração e dados dos eventos de acesso.

**Como se relaciona com o restante:** Persistência de usuários e logs com SQLAlchemy, sessões transacionais e SQLite local; a integração PostgreSQL está desativada pela configuração atual.

**Arquivos do projeto que utiliza:** `PI4/Backend/db/database.py`.

**Arquivos que utilizam este módulo:** `PI4/Backend/db/__init__.py`, `PI4/Backend/db/auth.py`, `PI4/Backend/db/database.py`, `PI4/Backend/routers/auth_router.py`, `PI4/Backend/routers/email.py`, `PI4/Backend/routers/health_router.py`, `PI4/Backend/routers/users.py`, `PI4/Backend/tests/test_api_contracts.py`.

**Outras dependências declaradas:** `datetime`, `sqlalchemy`.

<a id="arquivo-035"></a>

#### `PI4/Backend/db/seed.py`

**Para que serve:** Carga inicial da tabela usuarios.

**Como funciona:** Configura os valores e as integrações compartilhadas indicados por este módulo.

**Como se relaciona com o restante:** Persistência de usuários e logs com SQLAlchemy, sessões transacionais e SQLite local; a integração PostgreSQL está desativada pela configuração atual.

**Arquivos do projeto que utiliza:** `PI4/Backend/db/auth.py`, `PI4/Backend/db/database.py`.

**Arquivos que utilizam este módulo:** `PI4/Backend/db/__init__.py`.

**Outras dependências declaradas:** `__future__`.

<a id="pasta-008"></a>

### Pasta `PI4/Backend/documentos/`

Base de conhecimento financeira em Markdown; usada pelo RAG e como explicação das contas, fórmulas e navegação.

| Arquivo | O que faz |
|---|---|
| [00_indice.md](#arquivo-037) | Documenta o tema “Indice da base de conhecimento CTI”. |

<a id="arquivo-037"></a>

#### `PI4/Backend/documentos/00_indice.md`

**Para que serve:** Documenta o tema “Indice da base de conhecimento CTI”.

**Como funciona:** Texto interpretado por leitores; arquivos em documentos são candidatos à indexação e fragmentação pelo RAG.

**Como se relaciona com o restante:** Engenharia e/ou motor de recuperação documental; referências e conteúdo integral abaixo.

<a id="pasta-009"></a>

### Pasta `PI4/Backend/documentos/balanco/`

Base de conhecimento financeira em Markdown; usada pelo RAG e como explicação das contas, fórmulas e navegação.

| Arquivo | O que faz |
|---|---|
| [01_ativo_circulante.md](#arquivo-038) | Documenta o tema “BAL — Ativo Circulante”. |
| [02_realizavel_permanente.md](#arquivo-039) | Documenta o tema “BAL — Realizavel a Longo Prazo e Permanente”. |
| [03_imobilizado_outorga_bar.md](#arquivo-040) | Documenta o tema “BAL — Imobilizado, Intangivel, Outorga e BAR”. |
| [04_passivo_circulante.md](#arquivo-041) | Documenta o tema “BAL — Passivo Circulante”. |
| [05_exigivel_lp.md](#arquivo-042) | Documenta o tema “BAL — Exigivel a Longo Prazo”. |
| [06_patrimonio_liquido.md](#arquivo-043) | Documenta o tema “BAL — Patrimonio Liquido”. |
| [07_totais_controle.md](#arquivo-044) | Documenta o tema “BAL — Totais de Controle”. |

<a id="arquivo-038"></a>

#### `PI4/Backend/documentos/balanco/01_ativo_circulante.md`

**Para que serve:** Documenta o tema “BAL — Ativo Circulante”.

**Como funciona:** Texto interpretado por leitores; arquivos em documentos são candidatos à indexação e fragmentação pelo RAG.

**Como se relaciona com o restante:** Engenharia e/ou motor de recuperação documental; referências e conteúdo integral abaixo.

**Assuntos explicados neste arquivo:** `BAL - Ativo Circulante`; `BAL - Disponível`; Recebiveis; `BAL - Estoques Diversos`; `BAL - Créditos Tributários`; `BAL - Outros Créditos`.

<a id="arquivo-039"></a>

#### `PI4/Backend/documentos/balanco/02_realizavel_permanente.md`

**Para que serve:** Documenta o tema “BAL — Realizavel a Longo Prazo e Permanente”.

**Como funciona:** Texto interpretado por leitores; arquivos em documentos são candidatos à indexação e fragmentação pelo RAG.

**Como se relaciona com o restante:** Engenharia e/ou motor de recuperação documental; referências e conteúdo integral abaixo.

**Assuntos explicados neste arquivo:** `BAL - Realizável a Longo Prazo`; `BAL - At Fiscal Diferido`; `BAL - Outros Créditos LP`; `BAL - Permanente`; `BAL - Diferido`.

<a id="arquivo-040"></a>

#### `PI4/Backend/documentos/balanco/03_imobilizado_outorga_bar.md`

**Para que serve:** Documenta o tema “BAL — Imobilizado, Intangivel, Outorga e BAR”.

**Como funciona:** Texto interpretado por leitores; arquivos em documentos são candidatos à indexação e fragmentação pelo RAG.

**Como se relaciona com o restante:** Engenharia e/ou motor de recuperação documental; referências e conteúdo integral abaixo.

**Assuntos explicados neste arquivo:** `BAL - Investimentos - Imobilizado`; `BAL - Investimentos - Intangível`; `BAL - Depreciação Acumulada`; `BAL - Amortização - Intangível`; `BAL - Amortização Acumulada`; `BAL - Outorga da Concessão`; Base de Ativos Reversiveis (BAR).

<a id="arquivo-041"></a>

#### `PI4/Backend/documentos/balanco/04_passivo_circulante.md`

**Para que serve:** Documenta o tema “BAL — Passivo Circulante”.

**Como funciona:** Texto interpretado por leitores; arquivos em documentos são candidatos à indexação e fragmentação pelo RAG.

**Como se relaciona com o restante:** Engenharia e/ou motor de recuperação documental; referências e conteúdo integral abaixo.

**Assuntos explicados neste arquivo:** `BAL - Passivo Circulante`; `BAL - Fornecedores`; `BAL - Empréstimos` e `BAL - Emprést`; `BAL - Encargos Sociais e Trabalhistas`; `BAL - Tributos a pagar` e `BAL - Impostos`; `BAL - Contas a Pagar - Parte Relacionada`; `BAL - Outros Débitos` e `BAL - Outros deb`.

<a id="arquivo-042"></a>

#### `PI4/Backend/documentos/balanco/05_exigivel_lp.md`

**Para que serve:** Documenta o tema “BAL — Exigivel a Longo Prazo”.

**Como funciona:** Texto interpretado por leitores; arquivos em documentos são candidatos à indexação e fragmentação pelo RAG.

**Como se relaciona com o restante:** Engenharia e/ou motor de recuperação documental; referências e conteúdo integral abaixo.

**Assuntos explicados neste arquivo:** `BAL - Exigível a Longo Prazo`; Emprestimos de longo prazo; `BAL - Prov para Contingências`; `BAL - Provisão Manutenção`; `BAL - Obrigações com o Poder Concedente`.

<a id="arquivo-043"></a>

#### `PI4/Backend/documentos/balanco/06_patrimonio_liquido.md`

**Para que serve:** Documenta o tema “BAL — Patrimonio Liquido”.

**Como funciona:** Texto interpretado por leitores; arquivos em documentos são candidatos à indexação e fragmentação pelo RAG.

**Como se relaciona com o restante:** Engenharia e/ou motor de recuperação documental; referências e conteúdo integral abaixo.

**Assuntos explicados neste arquivo:** `BAL - Patrimônio Líquido`; Pecas do PL.

<a id="arquivo-044"></a>

#### `PI4/Backend/documentos/balanco/07_totais_controle.md`

**Para que serve:** Documenta o tema “BAL — Totais de Controle”.

**Como funciona:** Texto interpretado por leitores; arquivos em documentos são candidatos à indexação e fragmentação pelo RAG.

**Como se relaciona com o restante:** Engenharia e/ou motor de recuperação documental; referências e conteúdo integral abaixo.

**Assuntos explicados neste arquivo:** `BAL - Total do Ativo`; `BAL - Total do Passivo`.

<a id="pasta-010"></a>

### Pasta `PI4/Backend/documentos/cenarios/`

Base de conhecimento financeira em Markdown; usada pelo RAG e como explicação das contas, fórmulas e navegação.

| Arquivo | O que faz |
|---|---|
| [01_variaveis_estresse.md](#arquivo-045) | Documenta o tema “Cenarios — Variaveis de Estresse”. |
| [02_cenarios_criticos.md](#arquivo-046) | Documenta o tema “Cenarios — Isolamento de Caminhos Criticos”. |
| [03_matriz_selos.md](#arquivo-047) | Documenta o tema “Cenarios — Matriz e Seis Selos”. |

<a id="arquivo-045"></a>

#### `PI4/Backend/documentos/cenarios/01_variaveis_estresse.md`

**Para que serve:** Documenta o tema “Cenarios — Variaveis de Estresse”.

**Como funciona:** Texto interpretado por leitores; arquivos em documentos são candidatos à indexação e fragmentação pelo RAG.

**Como se relaciona com o restante:** Engenharia e/ou motor de recuperação documental; referências e conteúdo integral abaixo.

**Assuntos explicados neste arquivo:** Demanda e receita; Custos de insumos e OPEX; Inflacao, juros e estrutura financeira; CAPEX e prazos operacionais.

<a id="arquivo-046"></a>

#### `PI4/Backend/documentos/cenarios/02_cenarios_criticos.md`

**Para que serve:** Documenta o tema “Cenarios — Isolamento de Caminhos Criticos”.

**Como funciona:** Texto interpretado por leitores; arquivos em documentos são candidatos à indexação e fragmentação pelo RAG.

**Como se relaciona com o restante:** Engenharia e/ou motor de recuperação documental; referências e conteúdo integral abaixo.

**Assuntos explicados neste arquivo:** Ruina de caixa; Inadimplencia operacional; Quebra do equilibrio economico-financeiro.

<a id="arquivo-047"></a>

#### `PI4/Backend/documentos/cenarios/03_matriz_selos.md`

**Para que serve:** Documenta o tema “Cenarios — Matriz e Seis Selos”.

**Como funciona:** Texto interpretado por leitores; arquivos em documentos são candidatos à indexação e fragmentação pelo RAG.

**Como se relaciona com o restante:** Engenharia e/ou motor de recuperação documental; referências e conteúdo integral abaixo.

**Assuntos explicados neste arquivo:** Zona 1 — Encerramento com Caixa Insuficiente; Zona 2 — Forte Pressao de Investimentos; Zona 3 — Elevada Distribuicao & Baixa Disponibilidade; Zona 4 — Alta Rentabilidade & Alta Liquidez; Zona 5 — Alta Rentabilidade & Baixa Liquidez; Zona 6 — Retorno Moderado & Baixo Risco; Matriz visual.

<a id="pasta-011"></a>

### Pasta `PI4/Backend/documentos/dre/`

Base de conhecimento financeira em Markdown; usada pelo RAG e como explicação das contas, fórmulas e navegação.

| Arquivo | O que faz |
|---|---|
| [01_cascata_apuracao.md](#arquivo-048) | Documenta o tema “DRE — Cascata de Apuracao”. |
| [02_receita_custos_ebitda.md](#arquivo-049) | Documenta o tema “DRE — Receita, Tributos, Custos e EBITDA”. |
| [03_ebit_financeiro_ir_lucro.md](#arquivo-050) | Documenta o tema “DRE — EBIT, Financeiro, IR e Lucro”. |

<a id="arquivo-048"></a>

#### `PI4/Backend/documentos/dre/01_cascata_apuracao.md`

**Para que serve:** Documenta o tema “DRE — Cascata de Apuracao”.

**Como funciona:** Texto interpretado por leitores; arquivos em documentos são candidatos à indexação e fragmentação pelo RAG.

**Como se relaciona com o restante:** Engenharia e/ou motor de recuperação documental; referências e conteúdo integral abaixo.

<a id="arquivo-049"></a>

#### `PI4/Backend/documentos/dre/02_receita_custos_ebitda.md`

**Para que serve:** Documenta o tema “DRE — Receita, Tributos, Custos e EBITDA”.

**Como funciona:** Texto interpretado por leitores; arquivos em documentos são candidatos à indexação e fragmentação pelo RAG.

**Como se relaciona com o restante:** Engenharia e/ou motor de recuperação documental; referências e conteúdo integral abaixo.

**Assuntos explicados neste arquivo:** `DRE - Receita`; `DRE - Tributos`; `DRE - Custos`; `DRE - EBITDA`.

<a id="arquivo-050"></a>

#### `PI4/Backend/documentos/dre/03_ebit_financeiro_ir_lucro.md`

**Para que serve:** Documenta o tema “DRE — EBIT, Financeiro, IR e Lucro”.

**Como funciona:** Texto interpretado por leitores; arquivos em documentos são candidatos à indexação e fragmentação pelo RAG.

**Como se relaciona com o restante:** Engenharia e/ou motor de recuperação documental; referências e conteúdo integral abaixo.

**Assuntos explicados neste arquivo:** `DRE - Depreciação e Amortização`; `DRE - Resultado Operacional`; `DRE - Outros Resultados Operacionais`; `DRE - Receitas Financeiras` e `DRE - Despesas Financeiras`; `DRE - Resultado Financeiro`; `DRE - Resultado Antes do Imposto de Renda`; `DRE - Imposto de Renda e Contribuição Social`; `DRE - Resultado Líquido`; `DRE - Resultado Líquido após Equivalência`.

<a id="pasta-012"></a>

### Pasta `PI4/Backend/documentos/fluxo_caixa/`

Base de conhecimento financeira em Markdown; usada pelo RAG e como explicação das contas, fórmulas e navegação.

| Arquivo | O que faz |
|---|---|
| [01_fluxo_operacional.md](#arquivo-051) | Documenta o tema “FLU — Fluxo Operacional”. |
| [02_investimento_financeiro_saldos.md](#arquivo-052) | Documenta o tema “FLU — Investimento, Financeiro e Saldos”. |

<a id="arquivo-051"></a>

#### `PI4/Backend/documentos/fluxo_caixa/01_fluxo_operacional.md`

**Para que serve:** Documenta o tema “FLU — Fluxo Operacional”.

**Como funciona:** Texto interpretado por leitores; arquivos em documentos são candidatos à indexação e fragmentação pelo RAG.

**Como se relaciona com o restante:** Engenharia e/ou motor de recuperação documental; referências e conteúdo integral abaixo.

**Assuntos explicados neste arquivo:** `FLU - Receita`; `FLU - Entradas`; `FLU - Custos`; `FLU - Tributos`; `FLU - Imposto de Renda e Contribuição Social`; `FLU - Geração de Caixa`.

<a id="arquivo-052"></a>

#### `PI4/Backend/documentos/fluxo_caixa/02_investimento_financeiro_saldos.md`

**Para que serve:** Documenta o tema “FLU — Investimento, Financeiro e Saldos”.

**Como funciona:** Texto interpretado por leitores; arquivos em documentos são candidatos à indexação e fragmentação pelo RAG.

**Como se relaciona com o restante:** Engenharia e/ou motor de recuperação documental; referências e conteúdo integral abaixo.

**Assuntos explicados neste arquivo:** `FLU - Investimentos`; `FLU - Despesas Financeiras`; `FLU - Resultado Financeiro`; `FLU - Distribuição para Acionista`; `FLU - Saldo Inicial`; `FLU - Saldo Final`.

<a id="pasta-013"></a>

### Pasta `PI4/Backend/documentos/graficos/`

Base de conhecimento financeira em Markdown; usada pelo RAG e como explicação das contas, fórmulas e navegação.

| Arquivo | O que faz |
|---|---|
| [01_ceo.md](#arquivo-053) | Documenta o tema “Graficos — Visao CEO”. |
| [02_cfo.md](#arquivo-054) | Documenta o tema “Graficos — Visao CFO”. |
| [03_acionistas.md](#arquivo-055) | Documenta o tema “Graficos — Visao Acionistas”. |
| [04_concedente.md](#arquivo-056) | Documenta o tema “Graficos — Visao Poder Concedente”. |
| [05_comparacao.md](#arquivo-057) | Documenta o tema “Graficos — Comparacao A/B/C”. |

<a id="arquivo-053"></a>

#### `PI4/Backend/documentos/graficos/01_ceo.md`

**Para que serve:** Documenta o tema “Graficos — Visao CEO”.

**Como funciona:** Texto interpretado por leitores; arquivos em documentos são candidatos à indexação e fragmentação pelo RAG.

**Como se relaciona com o restante:** Engenharia e/ou motor de recuperação documental; referências e conteúdo integral abaixo.

**Assuntos explicados neste arquivo:** Visao Geral & DRE; Cascata media da DRE; Receita Liquida vs EBITDA (12 anos); DRE Operacional; Break-Even & Margens; Eficiencia LTV/CAC.

<a id="arquivo-054"></a>

#### `PI4/Backend/documentos/graficos/02_cfo.md`

**Para que serve:** Documenta o tema “Graficos — Visao CFO”.

**Como funciona:** Texto interpretado por leitores; arquivos em documentos são candidatos à indexação e fragmentação pelo RAG.

**Como se relaciona com o restante:** Engenharia e/ou motor de recuperação documental; referências e conteúdo integral abaixo.

**Assuntos explicados neste arquivo:** Capital de Giro; NCG x Tesouraria (12 anos); Composicao da NCG; Prazos e Ciclo; Mapeamento de Risco x Retorno; Distribuicao & Probabilidades; Faixa de Risco; Como Ler.

<a id="arquivo-055"></a>

#### `PI4/Backend/documentos/graficos/03_acionistas.md`

**Para que serve:** Documenta o tema “Graficos — Visao Acionistas”.

**Como funciona:** Texto interpretado por leitores; arquivos em documentos são candidatos à indexação e fragmentação pelo RAG.

**Como se relaciona com o restante:** Engenharia e/ou motor de recuperação documental; referências e conteúdo integral abaixo.

**Assuntos explicados neste arquivo:** Retorno & ROIC; Geracao de EVA; Lucro Liquido & Dividendos.

<a id="arquivo-056"></a>

#### `PI4/Backend/documentos/graficos/04_concedente.md`

**Para que serve:** Documenta o tema “Graficos — Visao Poder Concedente”.

**Como funciona:** Texto interpretado por leitores; arquivos em documentos são candidatos à indexação e fragmentação pelo RAG.

**Como se relaciona com o restante:** Engenharia e/ou motor de recuperação documental; referências e conteúdo integral abaixo.

**Assuntos explicados neste arquivo:** Plano de CAPEX; Solvencia & Liquidez Geral; Ativos Reversiveis.

<a id="arquivo-057"></a>

#### `PI4/Backend/documentos/graficos/05_comparacao.md`

**Para que serve:** Documenta o tema “Graficos — Comparacao A/B/C”.

**Como funciona:** Texto interpretado por leitores; arquivos em documentos são candidatos à indexação e fragmentação pelo RAG.

**Como se relaciona com o restante:** Engenharia e/ou motor de recuperação documental; referências e conteúdo integral abaixo.

<a id="pasta-014"></a>

### Pasta `PI4/Backend/documentos/ia/`

Base de conhecimento financeira em Markdown; usada pelo RAG e como explicação das contas, fórmulas e navegação.

| Arquivo | O que faz |
|---|---|
| [01_protocolo_resposta.md](#arquivo-058) | Documenta o tema “IA — Protocolo de Resposta”. |
| [02_mapa_navegacao.md](#arquivo-059) | Documenta o tema “IA — Mapa de Navegacao”. |

<a id="arquivo-058"></a>

#### `PI4/Backend/documentos/ia/01_protocolo_resposta.md`

**Para que serve:** Documenta o tema “IA — Protocolo de Resposta”.

**Como funciona:** Texto interpretado por leitores; arquivos em documentos são candidatos à indexação e fragmentação pelo RAG.

**Como se relaciona com o restante:** Engenharia e/ou motor de recuperação documental; referências e conteúdo integral abaixo.

**Assuntos explicados neste arquivo:** Regra unificada; Tom e evidencia.

<a id="arquivo-059"></a>

#### `PI4/Backend/documentos/ia/02_mapa_navegacao.md`

**Para que serve:** Documenta o tema “IA — Mapa de Navegacao”.

**Como funciona:** Texto interpretado por leitores; arquivos em documentos são candidatos à indexação e fragmentação pelo RAG.

**Como se relaciona com o restante:** Engenharia e/ou motor de recuperação documental; referências e conteúdo integral abaixo.

<a id="pasta-015"></a>

### Pasta `PI4/Backend/documentos/indicadores/`

Base de conhecimento financeira em Markdown; usada pelo RAG e como explicação das contas, fórmulas e navegação.

| Arquivo | O que faz |
|---|---|
| [01_margens.md](#arquivo-060) | Documenta o tema “Indicadores — Margens Operacionais”. |
| [02_retorno_valor.md](#arquivo-061) | Documenta o tema “Indicadores — ROIC, ROE, WACC e EVA”. |
| [03_break_even.md](#arquivo-062) | Documenta o tema “Indicadores — Break-Even e Margem de Seguranca”. |
| [04_ncg_tesouraria.md](#arquivo-063) | Documenta o tema “Indicadores — NCG e Tesouraria”. |
| [05_prazos_ciclo.md](#arquivo-064) | Documenta o tema “Indicadores — Prazos e Ciclo”. |
| [06_liquidez.md](#arquivo-065) | Documenta o tema “Indicadores — Liquidez”. |
| [07_capex_bar_dscr.md](#arquivo-066) | Documenta o tema “Indicadores — CAPEX, BAR, DSCR e Divida”. |
| [08_ruina_percentis.md](#arquivo-067) | Documenta o tema “Indicadores — Ruina e Cauda P5/P95”. |
| [09_ltv_cac.md](#arquivo-068) | Documenta o tema “Indicadores — LTV / CAC”. |

<a id="arquivo-060"></a>

#### `PI4/Backend/documentos/indicadores/01_margens.md`

**Para que serve:** Documenta o tema “Indicadores — Margens Operacionais”.

**Como funciona:** Texto interpretado por leitores; arquivos em documentos são candidatos à indexação e fragmentação pelo RAG.

**Como se relaciona com o restante:** Engenharia e/ou motor de recuperação documental; referências e conteúdo integral abaixo.

**Assuntos explicados neste arquivo:** EBITDA e Margem EBITDA; EBIT e Margem EBIT; Lucro Liquido e Margem Liquida; ROA.

<a id="arquivo-061"></a>

#### `PI4/Backend/documentos/indicadores/02_retorno_valor.md`

**Para que serve:** Documenta o tema “Indicadores — ROIC, ROE, WACC e EVA”.

**Como funciona:** Texto interpretado por leitores; arquivos em documentos são candidatos à indexação e fragmentação pelo RAG.

**Como se relaciona com o restante:** Engenharia e/ou motor de recuperação documental; referências e conteúdo integral abaixo.

**Assuntos explicados neste arquivo:** ROIC; ROE; WACC; EVA.

<a id="arquivo-062"></a>

#### `PI4/Backend/documentos/indicadores/03_break_even.md`

**Para que serve:** Documenta o tema “Indicadores — Break-Even e Margem de Seguranca”.

**Como funciona:** Texto interpretado por leitores; arquivos em documentos são candidatos à indexação e fragmentação pelo RAG.

**Como se relaciona com o restante:** Engenharia e/ou motor de recuperação documental; referências e conteúdo integral abaixo.

<a id="arquivo-063"></a>

#### `PI4/Backend/documentos/indicadores/04_ncg_tesouraria.md`

**Para que serve:** Documenta o tema “Indicadores — NCG e Tesouraria”.

**Como funciona:** Texto interpretado por leitores; arquivos em documentos são candidatos à indexação e fragmentação pelo RAG.

**Como se relaciona com o restante:** Engenharia e/ou motor de recuperação documental; referências e conteúdo integral abaixo.

**Assuntos explicados neste arquivo:** NCG; Saldo de Tesouraria.

<a id="arquivo-064"></a>

#### `PI4/Backend/documentos/indicadores/05_prazos_ciclo.md`

**Para que serve:** Documenta o tema “Indicadores — Prazos e Ciclo”.

**Como funciona:** Texto interpretado por leitores; arquivos em documentos são candidatos à indexação e fragmentação pelo RAG.

**Como se relaciona com o restante:** Engenharia e/ou motor de recuperação documental; referências e conteúdo integral abaixo.

<a id="arquivo-065"></a>

#### `PI4/Backend/documentos/indicadores/06_liquidez.md`

**Para que serve:** Documenta o tema “Indicadores — Liquidez”.

**Como funciona:** Texto interpretado por leitores; arquivos em documentos são candidatos à indexação e fragmentação pelo RAG.

**Como se relaciona com o restante:** Engenharia e/ou motor de recuperação documental; referências e conteúdo integral abaixo.

<a id="arquivo-066"></a>

#### `PI4/Backend/documentos/indicadores/07_capex_bar_dscr.md`

**Para que serve:** Documenta o tema “Indicadores — CAPEX, BAR, DSCR e Divida”.

**Como funciona:** Texto interpretado por leitores; arquivos em documentos são candidatos à indexação e fragmentação pelo RAG.

**Como se relaciona com o restante:** Engenharia e/ou motor de recuperação documental; referências e conteúdo integral abaixo.

**Assuntos explicados neste arquivo:** CAPEX; BAR; DSCR / Cobertura de Juros; Endividamento, FCFF, FCFE.

<a id="arquivo-067"></a>

#### `PI4/Backend/documentos/indicadores/08_ruina_percentis.md`

**Para que serve:** Documenta o tema “Indicadores — Ruina e Cauda P5/P95”.

**Como funciona:** Texto interpretado por leitores; arquivos em documentos são candidatos à indexação e fragmentação pelo RAG.

**Como se relaciona com o restante:** Engenharia e/ou motor de recuperação documental; referências e conteúdo integral abaixo.

<a id="arquivo-068"></a>

#### `PI4/Backend/documentos/indicadores/09_ltv_cac.md`

**Para que serve:** Documenta o tema “Indicadores — LTV / CAC”.

**Como funciona:** Texto interpretado por leitores; arquivos em documentos são candidatos à indexação e fragmentação pelo RAG.

**Como se relaciona com o restante:** Engenharia e/ou motor de recuperação documental; referências e conteúdo integral abaixo.

<a id="pasta-016"></a>

### Pasta `PI4/Backend/documentos/visao_geral/`

Base de conhecimento financeira em Markdown; usada pelo RAG e como explicação das contas, fórmulas e navegação.

| Arquivo | O que faz |
|---|---|
| [01_objeto_e_base.md](#arquivo-069) | Documenta o tema “Objeto da Concessao e Base CTI”. |
| [02_monte_carlo_percentis.md](#arquivo-070) | Documenta o tema “Monte Carlo e Percentis”. |
| [03_constantes_e_leitura.md](#arquivo-071) | Documenta o tema “Constantes do Modelo e Leitura Integrada”. |
| [04_stakeholders.md](#arquivo-072) | Documenta o tema “Stakeholders e Lentes do Dashboard”. |
| [manual_executivo_cti.md](#arquivo-073) | Documenta o tema “Manual executivo CTI”. |

<a id="arquivo-069"></a>

#### `PI4/Backend/documentos/visao_geral/01_objeto_e_base.md`

**Para que serve:** Documenta o tema “Objeto da Concessao e Base CTI”.

**Como funciona:** Texto interpretado por leitores; arquivos em documentos são candidatos à indexação e fragmentação pelo RAG.

**Como se relaciona com o restante:** Engenharia e/ou motor de recuperação documental; referências e conteúdo integral abaixo.

<a id="arquivo-070"></a>

#### `PI4/Backend/documentos/visao_geral/02_monte_carlo_percentis.md`

**Para que serve:** Documenta o tema “Monte Carlo e Percentis”.

**Como funciona:** Texto interpretado por leitores; arquivos em documentos são candidatos à indexação e fragmentação pelo RAG.

**Como se relaciona com o restante:** Engenharia e/ou motor de recuperação documental; referências e conteúdo integral abaixo.

**Assuntos explicados neste arquivo:** Percentis.

<a id="arquivo-071"></a>

#### `PI4/Backend/documentos/visao_geral/03_constantes_e_leitura.md`

**Para que serve:** Documenta o tema “Constantes do Modelo e Leitura Integrada”.

**Como funciona:** Texto interpretado por leitores; arquivos em documentos são candidatos à indexação e fragmentação pelo RAG.

**Como se relaciona com o restante:** Engenharia e/ou motor de recuperação documental; referências e conteúdo integral abaixo.

**Assuntos explicados neste arquivo:** Formulas-base de giro e solvencia; Ordem executiva de leitura.

<a id="arquivo-072"></a>

#### `PI4/Backend/documentos/visao_geral/04_stakeholders.md`

**Para que serve:** Documenta o tema “Stakeholders e Lentes do Dashboard”.

**Como funciona:** Texto interpretado por leitores; arquivos em documentos são candidatos à indexação e fragmentação pelo RAG.

**Como se relaciona com o restante:** Engenharia e/ou motor de recuperação documental; referências e conteúdo integral abaixo.

**Assuntos explicados neste arquivo:** CEO; CFO; Acionistas; Poder Concedente.

<a id="arquivo-073"></a>

#### `PI4/Backend/documentos/visao_geral/manual_executivo_cti.md`

**Para que serve:** Documenta o tema “Manual executivo CTI”.

**Como funciona:** Texto interpretado por leitores; arquivos em documentos são candidatos à indexação e fragmentação pelo RAG.

**Como se relaciona com o restante:** Engenharia e/ou motor de recuperação documental; referências e conteúdo integral abaixo.

**Assuntos explicados neste arquivo:** O que o painel responde; Fórmulas-resumo; Selos.

<a id="pasta-017"></a>

### Pasta `PI4/Backend/metrics/`

Regras financeiras e comerciais compartilhadas; transforma contas contábeis em indicadores e classificações por cenário/ano.

| Arquivo | O que faz |
|---|---|
| [__init__.py](#arquivo-075) | Indicadores financeiros e comerciais calculados no backend. |
| [column_resolver.py](#arquivo-076) | Padroniza nomes de colunas e contas financeiras para que variações de escrita não interrompam os cálculos. |
| [commercial_kpis.py](#arquivo-077) | KPIs comerciais derivados da base financeira. |
| [financial_kpis.py](#arquivo-078) | Calculo de indicadores financeiros e regras de negocio CTI. |

<a id="arquivo-075"></a>

#### `PI4/Backend/metrics/__init__.py`

**Para que serve:** Indicadores financeiros e comerciais calculados no backend.

**Como funciona:** Reúne constantes, imports e exports para os consumidores do pacote.

**Como se relaciona com o restante:** Regras financeiras e comerciais compartilhadas; transforma contas contábeis em indicadores e classificações por cenário/ano.

**Arquivos do projeto que utiliza:** `PI4/Backend/metrics/commercial_kpis.py`, `PI4/Backend/metrics/financial_kpis.py`.

**Arquivos que utilizam este módulo:** `PI4/Backend/rag_engine.py`, `PI4/Backend/scripts/precompute_cache.py`, `PI4/Backend/services/custom_report_service.py`, `PI4/Backend/services/metrics_calculator.py`, `PI4/Backend/services/report_generator.py`, `PI4/Backend/services/report_insights.py`, `PI4/Backend/services/risk_alerts.py`, `PI4/Frontend/app.py`, `PI4/Frontend/src/controllers/kpis/ceo.py`, `PI4/Frontend/src/models/analytics/summaries.py`, `PI4/Frontend/src/views/persona_tabs/ceo.py`.

<a id="arquivo-076"></a>

#### `PI4/Backend/metrics/column_resolver.py`

**Para que serve:** Padroniza nomes de colunas e contas financeiras para que variações de escrita não interrompam os cálculos.

**Como funciona:** Tenta reparar texto com codificação incorreta, remove acentos e símbolos para comparar nomes, reconhece aliases como receita/EBITDA e recupera séries numéricas. Coluna obrigatória ausente gera erro; séries opcionais podem receber um valor padrão.

**Como se relaciona com o restante:** Regras financeiras e comerciais compartilhadas; transforma contas contábeis em indicadores e classificações por cenário/ano.

**Arquivos que utilizam este módulo:** `PI4/Backend/data_loader/sql_reader.py`, `PI4/Backend/data_loader/upload_normalizer.py`, `PI4/Backend/metrics/commercial_kpis.py`, `PI4/Backend/metrics/financial_kpis.py`, `PI4/Backend/services/report_generator.py`, `PI4/Backend/services/report_insights.py`, `PI4/Backend/tests/test_performance_regressions.py`, `PI4/Frontend/src/controllers/kpis/ceo.py`, `PI4/Frontend/src/views/persona_tabs/ceo.py`, `PI4/Frontend/src/views/persona_tabs/comparison_ceo_cfo.py`.

**Outras dependências declaradas:** `collections`, `functools`, `pandas`, `re`, `unicodedata`.

**Responsabilidades internas:**

- `repair_mojibake`: Tenta desfazer mojibake comum de UTF-8 lido como Latin-1.
- `resolve_account_name`: Traduz cabecalhos amigaveis (Receita Bruta, EBITDA) para contas oficiais CTI.
- `normalize_label`: Normaliza texto removendo acentos, simbolos e espacos redundantes.
- `_normalize_label_text`: Reutiliza nomes repetidos num cache limitado, sem reter DataFrames.
- `resolve_column`: Retorna a coluna que corresponde a qualquer alias normalizado.
- `series_by_alias`: Recupera serie numerica por aliases, com fallback constante.

**Operações concretas realizadas neste arquivo:**

- Converte entradas para números e trata conversões inválidas conforme as opções utilizadas.
- Aplica os valores de substituição definidos para dados ausentes.

<a id="arquivo-077"></a>

#### `PI4/Backend/metrics/commercial_kpis.py`

**Para que serve:** KPIs comerciais derivados da base financeira.

**Como funciona:** Busca premissa comercial na base longa ou retorna fallback. Calcula LTV, CAC e razao LTV/CAC por ano. Resume LTV/CAC para cards e views com uma unica regra.

**Como se relaciona com o restante:** Regras financeiras e comerciais compartilhadas; transforma contas contábeis em indicadores e classificações por cenário/ano.

**Arquivos do projeto que utiliza:** `PI4/Backend/metrics/column_resolver.py`, `PI4/Backend/metrics/financial_kpis.py`.

**Arquivos que utilizam este módulo:** `PI4/Backend/metrics/__init__.py`, `PI4/Backend/services/memorial_report.py`, `PI4/scripts/gerar_memorial_cti.py`.

**Outras dependências declaradas:** `pandas`.

**Responsabilidades internas:**

- `_assumption_series`: Busca premissa comercial na base longa ou retorna fallback.
- `calculate_ltv_cac`: Calcula LTV, CAC e razao LTV/CAC por ano.
- `summarize_ltv_cac`: Resume LTV/CAC para cards e views com uma unica regra.

**Operações concretas realizadas neste arquivo:**

- Agrupa registros para calcular resultados por conta, ano, cenário ou outra chave indicada no módulo.
- Converte entradas para números e trata conversões inválidas conforme as opções utilizadas.
- Aplica os valores de substituição definidos para dados ausentes.

<a id="arquivo-078"></a>

#### `PI4/Backend/metrics/financial_kpis.py`

**Para que serve:** Calculo de indicadores financeiros e regras de negocio CTI.

**Como funciona:** True quando o recorte pede a consolidação de todos os cenários. Divide evitando divisao por zero. Compacta DataFrames derivados para memoria reduzida. Mapeia conta original para coluna canonica. Classifica cenarios por risco, liquidez e retorno. Garante eixos ANO/CENA mesmo quando nenhuma conta oficial foi reconhecida. Calcula NCG, prazos, liquidez, risco e ranking de cenarios. Indicadores a partir de um frame ja pivotado no SQL (ANO, ano_num, CENA, campos). Calcula percentual de cenarios com caixa final negativo. Calcula medias de KPIs para o recorte ja filtrado no backend. Monta DRE derivada para um cenario. Calcula ROIC, EVA, dividendos e estrutura de capital. Calcula break-even e margem de seguranca por ano.

**Como se relaciona com o restante:** Regras financeiras e comerciais compartilhadas; transforma contas contábeis em indicadores e classificações por cenário/ano.

**Arquivos do projeto que utiliza:** `PI4/Backend/data_loader/__init__.py`, `PI4/Backend/metrics/column_resolver.py`.

**Arquivos que utilizam este módulo:** `PI4/Backend/audit/config.py`, `PI4/Backend/data_loader/sql_reader.py`, `PI4/Backend/metrics/__init__.py`, `PI4/Backend/metrics/commercial_kpis.py`, `PI4/Backend/services/custom_report_service.py`, `PI4/Backend/services/dashboard_cache.py`, `PI4/Backend/services/memorial_report.py`, `PI4/Backend/services/metrics_calculator.py`, `PI4/Backend/services/report_generator.py`, `PI4/Backend/services/report_insights.py`, `PI4/Backend/services/scenario_filter.py`, `PI4/Frontend/src/controllers/kpis/ceo.py`, `PI4/Frontend/src/models/analytics/indicators.py`, `PI4/Frontend/src/models/classifiers.py`, `PI4/Frontend/src/views/ai_assistant/context.py`, `PI4/Frontend/src/views/persona_tabs/common.py`, `PI4/scripts/gerar_memorial_cti.py`.

**Outras dependências declaradas:** `numpy`, `pandas`.

**Responsabilidades internas:**

- `is_all_scenarios`: True quando o recorte pede a consolidação de todos os cenários.
- `safe_div`: Divide evitando divisao por zero.
- `compactar_indicadores`: Compacta DataFrames derivados para memoria reduzida.
- `mapa_contas`: Mapeia conta original para coluna canonica.
- `classificar_cenarios`: Classifica cenarios por risco, liquidez e retorno.
- `_esqueleto_indicadores`: Garante eixos ANO/CENA mesmo quando nenhuma conta oficial foi reconhecida.
- `montar_indicadores`: Calcula NCG, prazos, liquidez, risco e ranking de cenarios.
- `montar_indicadores_from_wide`: Indicadores a partir de um frame ja pivotado no SQL (ANO, ano_num, CENA, campos).
- `probabilidade_caixa_negativo`: Calcula percentual de cenarios com caixa final negativo.
- `calcular_kpis_recorte`: Calcula medias de KPIs para o recorte ja filtrado no backend.
- `build_dre`: Monta DRE derivada para um cenario.
- `build_financial_statement`: Calcula ROIC, EVA, dividendos e estrutura de capital.
- `build_break_even`: Calcula break-even e margem de seguranca por ano.

**Operações concretas realizadas neste arquivo:**

- Agrupa registros para calcular resultados por conta, ano, cenário ou outra chave indicada no módulo.
- Combina tabelas usando suas chaves de relacionamento.
- Converte entradas para números e trata conversões inválidas conforme as opções utilizadas.
- Aplica os valores de substituição definidos para dados ausentes.
- Calcula percentis usados nas faixas, comparações ou classificações.
- Monta consultas SQLAlchemy aos modelos de persistência.

<a id="pasta-018"></a>

### Pasta `PI4/Backend/relatorios/`

Artefatos exportados de relatórios e verificação; saídas de geração, não módulos executáveis.

| Arquivo | O que faz |
|---|---|
| [Memorial_Calculo_Dashboard_Financeiro_CTI.docx](#arquivo-080) | Relatório financeiro exportado |
| [Relatorio_Riscos_Financeiros_CTI.pdf](#arquivo-081) | Relatório financeiro exportado |
| [verificacao_memorial_cti.json](#arquivo-082) | Dados estruturados JSON |

<a id="arquivo-080"></a>

#### `PI4/Backend/relatorios/Memorial_Calculo_Dashboard_Financeiro_CTI.docx`

**Para que serve:** Relatório financeiro exportado

**Como funciona:** Documento binário paginado; DOCX organiza XML em ZIP e PDF contém objetos gráficos/texto.

**Como se relaciona com o restante:** Produzido por ferramentas/serviços de relatórios; não é código executável. Extração estrutural/textual consta quando disponível.

<a id="arquivo-081"></a>

#### `PI4/Backend/relatorios/Relatorio_Riscos_Financeiros_CTI.pdf`

**Para que serve:** Relatório financeiro exportado

**Como funciona:** Documento binário paginado; DOCX organiza XML em ZIP e PDF contém objetos gráficos/texto.

**Como se relaciona com o restante:** Produzido por ferramentas/serviços de relatórios; não é código executável. Extração estrutural/textual consta quando disponível.

<a id="arquivo-082"></a>

#### `PI4/Backend/relatorios/verificacao_memorial_cti.json`

**Para que serve:** Dados estruturados JSON

**Como funciona:** Serializa resultados, parâmetros ou verificações; não executa código por si só.

**Como se relaciona com o restante:** Consumidores dependem das chaves e dos caminhos; conteúdo integral disponível abaixo.

<a id="pasta-019"></a>

### Pasta `PI4/Backend/routers/`

Contratos HTTP FastAPI; valida modelos de entrada, chama serviços e traduz resultados ou erros para respostas HTTP.

| Arquivo | O que faz |
|---|---|
| [__init__.py](#arquivo-085) | Routers HTTP do Backend CTI. |
| [auth_router.py](#arquivo-086) | Autenticacao e consulta dos logs de acesso. |
| [chat_router.py](#arquivo-087) | Endpoint de chat com o contrato original de entrada e resposta. |
| [email.py](#arquivo-088) | Endpoints de teste SMTP e varredura de risco. |
| [health_router.py](#arquivo-089) | Rotas de saude e versao, com os paths e contratos originais. |
| [report_router.py](#arquivo-090) | Download dinâmico do memorial financeiro com filtros validados. |
| [users.py](#arquivo-091) | Gestao de usuarios exclusiva do Super Admin. |

<a id="arquivo-085"></a>

#### `PI4/Backend/routers/__init__.py`

**Para que serve:** Routers HTTP do Backend CTI.

**Como funciona:** Reúne constantes, imports e exports para os consumidores do pacote.

**Como se relaciona com o restante:** Contratos HTTP FastAPI; valida modelos de entrada, chama serviços e traduz resultados ou erros para respostas HTTP.

<a id="arquivo-086"></a>

#### `PI4/Backend/routers/auth_router.py`

**Para que serve:** Autenticacao e consulta dos logs de acesso.

**Como funciona:** Configura os valores e as integrações compartilhadas indicados por este módulo.

**Como se relaciona com o restante:** Contratos HTTP FastAPI; valida modelos de entrada, chama serviços e traduz resultados ou erros para respostas HTTP.

**Arquivos do projeto que utiliza:** `PI4/Backend/db/__init__.py`, `PI4/Backend/db/auth.py`, `PI4/Backend/db/models.py`, `PI4/Backend/runtime.py`, `PI4/Backend/services/risk_alerts.py`.

**Arquivos que utilizam este módulo:** `PI4/Backend/main.py`.

**Outras dependências declaradas:** `fastapi`, `pydantic`, `sqlalchemy`.

**Operações concretas realizadas neste arquivo:**

- Monta consultas SQLAlchemy aos modelos de persistência.
- Converte uma condição inválida em erro HTTP com status e mensagem.

<a id="arquivo-087"></a>

#### `PI4/Backend/routers/chat_router.py`

**Para que serve:** Endpoint de chat com o contrato original de entrada e resposta.

**Como funciona:** Configura os valores e as integrações compartilhadas indicados por este módulo.

**Como se relaciona com o restante:** Contratos HTTP FastAPI; valida modelos de entrada, chama serviços e traduz resultados ou erros para respostas HTTP.

**Arquivos do projeto que utiliza:** `PI4/Backend/services/chat_service.py`.

**Arquivos que utilizam este módulo:** `PI4/Backend/main.py`.

**Outras dependências declaradas:** `fastapi`, `pydantic`.

<a id="arquivo-088"></a>

#### `PI4/Backend/routers/email.py`

**Para que serve:** Endpoints de teste SMTP e varredura de risco.

**Como funciona:** Configura os valores e as integrações compartilhadas indicados por este módulo.

**Como se relaciona com o restante:** Contratos HTTP FastAPI; valida modelos de entrada, chama serviços e traduz resultados ou erros para respostas HTTP.

**Arquivos do projeto que utiliza:** `PI4/Backend/db/__init__.py`, `PI4/Backend/db/auth.py`, `PI4/Backend/db/models.py`, `PI4/Backend/services/email_service.py`, `PI4/Backend/services/risk_alerts.py`.

**Arquivos que utilizam este módulo:** `PI4/Backend/main.py`.

**Outras dependências declaradas:** `fastapi`, `pydantic`, `sqlalchemy`.

**Operações concretas realizadas neste arquivo:**

- Monta consultas SQLAlchemy aos modelos de persistência.
- Converte uma condição inválida em erro HTTP com status e mensagem.

<a id="arquivo-089"></a>

#### `PI4/Backend/routers/health_router.py`

**Para que serve:** Rotas de saude e versao, com os paths e contratos originais.

**Como funciona:** Configura os valores e as integrações compartilhadas indicados por este módulo.

**Como se relaciona com o restante:** Contratos HTTP FastAPI; valida modelos de entrada, chama serviços e traduz resultados ou erros para respostas HTTP.

**Arquivos do projeto que utiliza:** `PI4/Backend/db/__init__.py`, `PI4/Backend/db/models.py`, `PI4/Backend/runtime.py`, `PI4/Backend/services/email_service.py`, `PI4/Backend/services/rag_indexer.py`, `PI4/Backend/services/risk_alerts.py`.

**Arquivos que utilizam este módulo:** `PI4/Backend/main.py`.

**Outras dependências declaradas:** `fastapi`, `sqlalchemy`.

**Operações concretas realizadas neste arquivo:**

- Monta consultas SQLAlchemy aos modelos de persistência.

<a id="arquivo-090"></a>

#### `PI4/Backend/routers/report_router.py`

**Para que serve:** Download dinâmico do memorial financeiro com filtros validados.

**Como funciona:** Configura os valores e as integrações compartilhadas indicados por este módulo.

**Como se relaciona com o restante:** Contratos HTTP FastAPI; valida modelos de entrada, chama serviços e traduz resultados ou erros para respostas HTTP.

**Arquivos do projeto que utiliza:** `PI4/Backend/services/dashboard_pipeline.py`, `PI4/Backend/services/memorial_report.py`.

**Arquivos que utilizam este módulo:** `PI4/Backend/main.py`.

**Outras dependências declaradas:** `fastapi`, `pydantic`.

**Operações concretas realizadas neste arquivo:**

- Converte uma condição inválida em erro HTTP com status e mensagem.

<a id="arquivo-091"></a>

#### `PI4/Backend/routers/users.py`

**Para que serve:** Gestao de usuarios exclusiva do Super Admin.

**Como funciona:** Configura os valores e as integrações compartilhadas indicados por este módulo.

**Como se relaciona com o restante:** Contratos HTTP FastAPI; valida modelos de entrada, chama serviços e traduz resultados ou erros para respostas HTTP.

**Arquivos do projeto que utiliza:** `PI4/Backend/db/__init__.py`, `PI4/Backend/db/auth.py`, `PI4/Backend/db/models.py`.

**Arquivos que utilizam este módulo:** `PI4/Backend/main.py`.

**Outras dependências declaradas:** `datetime`, `fastapi`, `pydantic`, `re`, `sqlalchemy`.

**Operações concretas realizadas neste arquivo:**

- Monta consultas SQLAlchemy aos modelos de persistência.
- Converte uma condição inválida em erro HTTP com status e mensagem.

<a id="pasta-020"></a>

### Pasta `PI4/Backend/scripts/`

Scripts operacionais do backend: precompute dos Parquets, seed de usuários e migração SQL.

| Arquivo | O que faz |
|---|---|
| [migrar_para_supabase.py](#arquivo-093) | Envia Cti.csv para a tabela cti_dados no PostgreSQL do Supabase, em lotes. |
| [precompute_cache.py](#arquivo-094) | Gera os parquets completos do dashboard CTI durante o build da Render. |
| [seed_usuarios.py](#arquivo-095) | Cria tabelas e insere os usuarios padrao de teste. |

<a id="arquivo-093"></a>

#### `PI4/Backend/scripts/migrar_para_supabase.py`

**Para que serve:** Envia Cti.csv para a tabela cti_dados no PostgreSQL do Supabase, em lotes.

**Como funciona:** Configura os valores e as integrações compartilhadas indicados por este módulo.

**Como se relaciona com o restante:** Scripts operacionais do backend: precompute dos Parquets, seed de usuários e migração SQL.

**Arquivos do projeto que utiliza:** `PI4/Backend/data_loader/csv_reader.py`.

**Outras dependências declaradas:** `os`, `pandas`, `pathlib`, `sqlalchemy`, `sys`, `urllib`.

**Operações concretas realizadas neste arquivo:**

- Lê tabelas CSV e as transforma em DataFrames.
- Converte entradas para números e trata conversões inválidas conforme as opções utilizadas.
- Grava registros em tabela SQL.
- Configura uma conexão SQLAlchemy com o banco.

<a id="arquivo-094"></a>

#### `PI4/Backend/scripts/precompute_cache.py`

**Para que serve:** Gera os parquets completos do dashboard CTI durante o build da Render.

**Como funciona:** Configura os valores e as integrações compartilhadas indicados por este módulo.

**Como se relaciona com o restante:** Scripts operacionais do backend: precompute dos Parquets, seed de usuários e migração SQL.

**Arquivos do projeto que utiliza:** `PI4/Backend/data_loader/__init__.py`, `PI4/Backend/metrics/__init__.py`.

**Outras dependências declaradas:** `pathlib`, `sys`.

**Operações concretas realizadas neste arquivo:**

- Grava DataFrames no cache Parquet.

<a id="arquivo-095"></a>

#### `PI4/Backend/scripts/seed_usuarios.py`

**Para que serve:** Cria tabelas e insere os usuarios padrao de teste.

**Como funciona:** Configura os valores e as integrações compartilhadas indicados por este módulo.

**Como se relaciona com o restante:** Scripts operacionais do backend: precompute dos Parquets, seed de usuários e migração SQL.

**Arquivos do projeto que utiliza:** `PI4/Backend/db/__init__.py`.

**Outras dependências declaradas:** `pathlib`, `sys`.

<a id="pasta-021"></a>

### Pasta `PI4/Backend/services/`

Serviços de aplicação: cache, contexto financeiro, relatórios PDF, RAG, SMTP e alertas; chamados por rotas e também diretamente pelo frontend.

| Arquivo | O que faz |
|---|---|
| [__init__.py](#arquivo-096) | Servicos de aplicacao do backend CTI. |
| [chat_service.py](#arquivo-097) | Motor RAG e historico de sessoes partilhado pelos pedidos de chat. |
| [custom_report_service.py](#arquivo-098) | Servico de relatorio executivo customizavel por blocos. |
| [dashboard_cache.py](#arquivo-099) | Lê e grava os arquivos Parquet que aceleram o dashboard. |
| [dashboard_pipeline.py](#arquivo-100) | Coordena a obtenção dos dados usados pelo dashboard. |
| [email_service.py](#arquivo-101) | Disparo de e-mails SMTP com diagnostico por fase (TCP, TLS, auth, envio). |
| [memorial_report.py](#arquivo-102) | Memorial CTI calculado por requisição; layout inspirado no modelo do professor. |
| [metrics_calculator.py](#arquivo-103) | Metricas de contexto e reconstrucao das contas financeiras do dashboard. |
| [rag_indexer.py](#arquivo-104) | Varredura recursiva da base documental usada pelo RAG. |
| [report_generator.py](#arquivo-105) | Geracao de relatorio executivo em PDF (padrao C-Level). |
| [report_insights.py](#arquivo-106) | Diagnostic & Insights do Assistente CTI para o relatorio executivo. |
| [risk_alerts.py](#arquivo-107) | Varredura de cauda de risco e disparo de um unico e-mail consolidado. |
| [risk_report.py](#arquivo-108) | Relatório PDF da varredura real, sem disparo SMTP nem alteração de métricas. |
| [scenario_filter.py](#arquivo-109) | Selecao de cenarios/anos e consolidacao anual do dashboard. |

<a id="arquivo-096"></a>

#### `PI4/Backend/services/__init__.py`

**Para que serve:** Servicos de aplicacao do backend CTI.

**Como funciona:** Reúne constantes, imports e exports para os consumidores do pacote.

**Como se relaciona com o restante:** Serviços de aplicação: cache, contexto financeiro, relatórios PDF, RAG, SMTP e alertas; chamados por rotas e também diretamente pelo frontend.

**Arquivos do projeto que utiliza:** `PI4/Backend/services/custom_report_service.py`, `PI4/Backend/services/dashboard_pipeline.py`, `PI4/Backend/services/rag_indexer.py`, `PI4/Backend/services/report_generator.py`.

**Arquivos que utilizam este módulo:** `PI4/Backend/services/dashboard_pipeline.py`, `PI4/Backend/tests/test_api_contracts.py`, `PI4/Backend/tests/test_dashboard_pipeline.py`, `PI4/Backend/tests/test_performance_regressions.py`, `PI4/Backend/tests/test_risk_report.py`, `PI4/Frontend/src/controllers/bootstrap.py`.

<a id="arquivo-097"></a>

#### `PI4/Backend/services/chat_service.py`

**Para que serve:** Motor RAG e historico de sessoes partilhado pelos pedidos de chat.

**Como funciona:** Mantem a inicializacao lazy do RAG e as ultimas 12 mensagens por sessao.

**Como se relaciona com o restante:** Serviços de aplicação: cache, contexto financeiro, relatórios PDF, RAG, SMTP e alertas; chamados por rotas e também diretamente pelo frontend.

**Arquivos do projeto que utiliza:** `PI4/Backend/diag.py`, `PI4/Backend/rag_engine.py`.

**Arquivos que utilizam este módulo:** `PI4/Backend/routers/chat_router.py`, `PI4/Backend/tests/test_api_contracts.py`, `PI4/Backend/tests/test_performance_regressions.py`.

**Outras dependências declaradas:** `threading`, `typing`.

**Responsabilidades internas:**

- `responder_chat`: Mantem a inicializacao lazy do RAG e as ultimas 12 mensagens por sessao.

<a id="arquivo-098"></a>

#### `PI4/Backend/services/custom_report_service.py`

**Para que serve:** Servico de relatorio executivo customizavel por blocos.

**Como funciona:** Retorna blocos disponiveis para o builder. Evita Lucro Liquido zerado quando a conta consolidada vem ausente. Aceita ids tecnicos ou labels visuais sem perder blocos selecionados. Monta callouts executivos da primeira pagina de conteudo. Parecer inicial por bloco. Nao varre a base de 1M ao abrir o modal. Gera PDF personalizado no padrao executivo C-Level.

**Como se relaciona com o restante:** Serviços de aplicação: cache, contexto financeiro, relatórios PDF, RAG, SMTP e alertas; chamados por rotas e também diretamente pelo frontend.

**Arquivos do projeto que utiliza:** `PI4/Backend/diag.py`, `PI4/Backend/metrics/__init__.py`, `PI4/Backend/metrics/financial_kpis.py`, `PI4/Backend/services/report_generator.py`, `PI4/Backend/services/report_insights.py`.

**Arquivos que utilizam este módulo:** `PI4/Backend/services/__init__.py`, `PI4/Backend/tests/test_report_notes.py`, `PI4/Frontend/src/views/report.py`.

**Outras dependências declaradas:** `datetime`, `io`, `pandas`, `plotly`, `reportlab`, `time`, `typing`.

**Responsabilidades internas:**

- `block_options`: Retorna blocos disponiveis para o builder.
- `_net_income_mean`: Evita Lucro Liquido zerado quando a conta consolidada vem ausente.
- `_normalize_selected_blocks`: Aceita ids tecnicos ou labels visuais sem perder blocos selecionados.
- `_kpi_callouts`: Monta callouts executivos da primeira pagina de conteudo.
- `default_block_notes`: Parecer inicial por bloco. Nao varre a base de 1M ao abrir o modal.
- `generate_custom_report_pdf`: Gera PDF personalizado no padrao executivo C-Level.

**Operações concretas realizadas neste arquivo:**

- Agrupa registros para calcular resultados por conta, ano, cenário ou outra chave indicada no módulo.
- Converte entradas para números e trata conversões inválidas conforme as opções utilizadas.
- Aplica os valores de substituição definidos para dados ausentes.
- Prepara um documento PDF com organização de páginas.

<a id="arquivo-099"></a>

#### `PI4/Backend/services/dashboard_cache.py`

**Para que serve:** Lê e grava os arquivos Parquet que aceleram o dashboard.

**Como funciona:** Verifica os arquivos esperados, carrega e compacta as tabelas e registra seus volumes. No fallback local lê o CSV, calcula indicadores e tenta persistir o resultado. Pode reconstruir parcialmente a base longa quando ela não está disponível.

**Como se relaciona com o restante:** Serviços de aplicação: cache, contexto financeiro, relatórios PDF, RAG, SMTP e alertas; chamados por rotas e também diretamente pelo frontend.

**Arquivos do projeto que utiliza:** `PI4/Backend/data_loader/__init__.py`, `PI4/Backend/diag.py`, `PI4/Backend/metrics/financial_kpis.py`, `PI4/Backend/services/metrics_calculator.py`.

**Arquivos que utilizam este módulo:** `PI4/Backend/services/dashboard_pipeline.py`, `PI4/Backend/tests/test_dashboard_pipeline.py`.

**Outras dependências declaradas:** `pandas`, `pathlib`.

**Responsabilidades internas:**

- `load_cached_dashboard`: Le os 3 parquets do precompute — mesma volumetria que o ambiente local.

**Operações concretas realizadas neste arquivo:**

- Carrega tabelas previamente persistidas em Parquet.
- Grava DataFrames no cache Parquet.

<a id="arquivo-100"></a>

#### `PI4/Backend/services/dashboard_pipeline.py`

**Para que serve:** Coordena a obtenção dos dados usados pelo dashboard.

**Como funciona:** Verifica o cache, delega a leitura dos três Parquets e entrega base, indicadores e ranking. Se o cache falhar, permite processar o CSV localmente; quando RENDER está definido, bloqueia essa leitura pesada em runtime.

**Como se relaciona com o restante:** Serviços de aplicação: cache, contexto financeiro, relatórios PDF, RAG, SMTP e alertas; chamados por rotas e também diretamente pelo frontend.

**Arquivos do projeto que utiliza:** `PI4/Backend/diag.py`, `PI4/Backend/services/__init__.py`, `PI4/Backend/services/dashboard_cache.py`, `PI4/Backend/services/metrics_calculator.py`.

**Arquivos que utilizam este módulo:** `PI4/Backend/data_loader/sql_reader.py`, `PI4/Backend/routers/report_router.py`, `PI4/Backend/services/__init__.py`, `PI4/Backend/services/risk_alerts.py`, `PI4/Backend/tests/test_dashboard_pipeline.py`, `PI4/Frontend/src/controllers/bootstrap.py`.

**Outras dependências declaradas:** `os`, `pandas`, `pathlib`.

**Responsabilidades internas:**

- `df_longo_de_indicadores`: Reconstroi CONTA/VALOR a partir dos indicadores — sem o CSV de 1M linhas.
- `load_cached_dashboard`: Le os 3 parquets do precompute — mesma volumetria que o ambiente local.
- `prepare_dashboard_data`: Parquet do precompute; CSV so em ambiente local se o cache faltar.
- `build_context_metrics`: Calcula dados derivados de contexto para filtros ativos.

<a id="arquivo-101"></a>

#### `PI4/Backend/services/email_service.py`

**Para que serve:** Disparo de e-mails SMTP com diagnostico por fase (TCP, TLS, auth, envio).

**Como funciona:** Preenche SMTP_* a partir do Backend/.env se o processo subiu com a variavel vazia. 465 = SSL direto; 587 (e demais) = STARTTLS. SMTP_MODE no .env sobrepoe. Envia HTML via SMTP, adaptando SSL (465) ou STARTTLS (587) a porta do .env.

**Como se relaciona com o restante:** Serviços de aplicação: cache, contexto financeiro, relatórios PDF, RAG, SMTP e alertas; chamados por rotas e também diretamente pelo frontend.

**Arquivos que utilizam este módulo:** `PI4/Backend/routers/email.py`, `PI4/Backend/routers/health_router.py`, `PI4/Backend/runtime.py`, `PI4/Backend/services/risk_alerts.py`, `PI4/Frontend/src/controllers/ops_menu.py`.

**Outras dependências declaradas:** `datetime`, `dotenv`, `email`, `html`, `logging`, `os`, `pathlib`, `re`, `smtplib`, `socket`, `ssl`, `traceback`.

**Responsabilidades internas:**

- `_aplicar_dotenv_smtp`: Preenche SMTP_* a partir do Backend/.env se o processo subiu com a variavel vazia.
- `_modo_smtp`: 465 = SSL direto; 587 (e demais) = STARTTLS. SMTP_MODE no .env sobrepoe.
- `enviar_alerta_email`: Envia HTML via SMTP, adaptando SSL (465) ou STARTTLS (587) a porta do .env.

**Operações concretas realizadas neste arquivo:**

- Abre conexão SMTP com TLS desde o início.
- Solicita proteção TLS na conexão SMTP.

<a id="arquivo-102"></a>

#### `PI4/Backend/services/memorial_report.py`

**Para que serve:** Memorial CTI calculado por requisição; layout inspirado no modelo do professor.

**Como funciona:** Calcula a partir da base recebida. Não grava arquivo nem dispara SMTP.

**Como se relaciona com o restante:** Serviços de aplicação: cache, contexto financeiro, relatórios PDF, RAG, SMTP e alertas; chamados por rotas e também diretamente pelo frontend.

**Arquivos do projeto que utiliza:** `PI4/Backend/metrics/commercial_kpis.py`, `PI4/Backend/metrics/financial_kpis.py`, `PI4/Backend/services/risk_alerts.py`.

**Arquivos que utilizam este módulo:** `PI4/Backend/routers/report_router.py`, `PI4/Backend/tests/test_memorial_api.py`.

**Outras dependências declaradas:** `datetime`, `io`, `pandas`, `pathlib`, `reportlab`, `xml`, `zoneinfo`.

**Responsabilidades internas:**

- `gerar_memorial_pdf`: Calcula a partir da base recebida. Não grava arquivo nem dispara SMTP.

**Operações concretas realizadas neste arquivo:**

- Converte entradas para números e trata conversões inválidas conforme as opções utilizadas.
- Prepara um documento PDF com organização de páginas.

<a id="arquivo-103"></a>

#### `PI4/Backend/services/metrics_calculator.py`

**Para que serve:** Metricas de contexto e reconstrucao das contas financeiras do dashboard.

As formulas de KPIs, EBITDA e margens permanecem em Backend.metrics.

**Como funciona:** Reconstroi CONTA/VALOR a partir dos indicadores — sem o CSV de 1M linhas. Reutiliza o calculo financeiro existente e devolve indicadores e ranking. Calcula dados derivados de contexto para filtros ativos.

**Como se relaciona com o restante:** Serviços de aplicação: cache, contexto financeiro, relatórios PDF, RAG, SMTP e alertas; chamados por rotas e também diretamente pelo frontend.

**Arquivos do projeto que utiliza:** `PI4/Backend/data_loader/__init__.py`, `PI4/Backend/diag.py`, `PI4/Backend/metrics/__init__.py`, `PI4/Backend/metrics/financial_kpis.py`, `PI4/Backend/services/scenario_filter.py`.

**Arquivos que utilizam este módulo:** `PI4/Backend/services/dashboard_cache.py`, `PI4/Backend/services/dashboard_pipeline.py`.

**Outras dependências declaradas:** `pandas`.

**Responsabilidades internas:**

- `df_longo_de_indicadores`: Reconstroi CONTA/VALOR a partir dos indicadores — sem o CSV de 1M linhas.
- `calcular_indicadores`: Reutiliza o calculo financeiro existente e devolve indicadores e ranking.
- `build_context_metrics`: Calcula dados derivados de contexto para filtros ativos.

**Operações concretas realizadas neste arquivo:**

- Converte entradas para números e trata conversões inválidas conforme as opções utilizadas.
- Aplica os valores de substituição definidos para dados ausentes.

<a id="arquivo-104"></a>

#### `PI4/Backend/services/rag_indexer.py`

**Para que serve:** Varredura recursiva da base documental usada pelo RAG.

**Como funciona:** Lista .md e .pdf em Backend/documentos, incluindo subpastas.

**Como se relaciona com o restante:** Serviços de aplicação: cache, contexto financeiro, relatórios PDF, RAG, SMTP e alertas; chamados por rotas e também diretamente pelo frontend.

**Arquivos que utilizam este módulo:** `PI4/Backend/routers/health_router.py`, `PI4/Backend/services/__init__.py`, `PI4/Frontend/src/models/rag_engine/documents.py`.

**Outras dependências declaradas:** `pathlib`.

**Responsabilidades internas:**

- `listar_documentos`: Lista .md e .pdf em Backend/documentos, incluindo subpastas.

<a id="arquivo-105"></a>

#### `PI4/Backend/services/report_generator.py`

**Para que serve:** Geracao de relatorio executivo em PDF (padrao C-Level).

**Como funciona:** Formata valores monetarios em mi/bi sem notacao cientifica. Cabecalho/rodape dinamicos com Pagina X de Y e selo de confidencialidade. Cabecalho em tabela (altura real). Nao e Flowable de pagina inteira. Duas secoes na mesma linha — evita saltar de pagina entre elas. Compatibilidade com o gerador legado; o canvas executivo assume o chrome. Parecer em paragrafo (parte de linha). Nao usa Table unsplittable. Fluxo continuo: sem PageBreak, sem KeepTogether, sem keepWithNext. Renderiza Plotly em PNG de alta resolucao (scale=2 ~ 300 DPI em 16,5 cm). Fallback local em 300 DPI quando Kaleido nao esta operacional. Graficos omitidos de proposito: uma imagem de 7 cm forca uma pagina quase vazia. Gera um relatorio executivo A4 em PDF.

**Como se relaciona com o restante:** Serviços de aplicação: cache, contexto financeiro, relatórios PDF, RAG, SMTP e alertas; chamados por rotas e também diretamente pelo frontend.

**Arquivos do projeto que utiliza:** `PI4/Backend/metrics/__init__.py`, `PI4/Backend/metrics/column_resolver.py`, `PI4/Backend/metrics/financial_kpis.py`, `PI4/Backend/services/report_insights.py`.

**Arquivos que utilizam este módulo:** `PI4/Backend/services/__init__.py`, `PI4/Backend/services/custom_report_service.py`, `PI4/Backend/services/report_insights.py`, `PI4/Backend/tests/test_report_notes.py`, `PI4/Frontend/src/views/report.py`.

**Outras dependências declaradas:** `datetime`, `io`, `matplotlib`, `os`, `pandas`, `pathlib`, `plotly`, `reportlab`, `subprocess`, `sys`, `tempfile`, `typing`, `xml`.

**Responsabilidades internas:**

- `format_exec_money`: Formata valores monetarios em mi/bi sem notacao cientifica.
- `ExecutiveCanvas`: Cabecalho/rodape dinamicos com Pagina X de Y e selo de confidencialidade.
- `masthead`: Cabecalho em tabela (altura real). Nao e Flowable de pagina inteira.
- `side_by_side`: Duas secoes na mesma linha — evita saltar de pagina entre elas.
- `_header_footer`: Compatibilidade com o gerador legado; o canvas executivo assume o chrome.
- `insight_card`: Parecer em paragrafo (parte de linha). Nao usa Table unsplittable.
- `section_block`: Fluxo continuo: sem PageBreak, sem KeepTogether, sem keepWithNext.
- `_fig_to_image`: Renderiza Plotly em PNG de alta resolucao (scale=2 ~ 300 DPI em 16,5 cm).
- `_fig_to_matplotlib_image`: Fallback local em 300 DPI quando Kaleido nao esta operacional.
- `_add_chart`: Graficos omitidos de proposito: uma imagem de 7 cm forca uma pagina quase vazia.
- `generate_executive_pdf`: Gera um relatorio executivo A4 em PDF.

**Operações concretas realizadas neste arquivo:**

- Converte entradas para números e trata conversões inválidas conforme as opções utilizadas.
- Aplica os valores de substituição definidos para dados ausentes.
- Prepara um documento PDF com organização de páginas.
- Carrega o conteúdo binário de um arquivo.

<a id="arquivo-106"></a>

#### `PI4/Backend/services/report_insights.py`

**Para que serve:** Diagnostic & Insights do Assistente CTI para o relatorio executivo.

**Como funciona:** KPIs a partir de DRE/BE/LTV ja calculados — sem varrer a base longa. Pareceres a partir de tabelas ja calculadas — sem varrer 1M de linhas e sem LLM. Gera pareceres qualitativos por bloco a partir dos KPIs reais do cenario. Texto customizado substitui integralmente o automático do mesmo bloco.

**Como se relaciona com o restante:** Serviços de aplicação: cache, contexto financeiro, relatórios PDF, RAG, SMTP e alertas; chamados por rotas e também diretamente pelo frontend.

**Arquivos do projeto que utiliza:** `PI4/Backend/metrics/__init__.py`, `PI4/Backend/metrics/column_resolver.py`, `PI4/Backend/metrics/financial_kpis.py`, `PI4/Backend/services/report_generator.py`.

**Arquivos que utilizam este módulo:** `PI4/Backend/services/custom_report_service.py`, `PI4/Backend/services/report_generator.py`, `PI4/Backend/tests/test_report_notes.py`.

**Outras dependências declaradas:** `concurrent`, `google`, `os`, `pandas`, `typing`.

**Responsabilidades internas:**

- `collect_table_metrics`: KPIs a partir de DRE/BE/LTV ja calculados — sem varrer a base longa.
- `insights_from_tables`: Pareceres a partir de tabelas ja calculadas — sem varrer 1M de linhas e sem LLM.
- `build_block_insights`: Gera pareceres qualitativos por bloco a partir dos KPIs reais do cenario.
- `merge_notes_with_insights`: Texto customizado substitui integralmente o automático do mesmo bloco.

**Operações concretas realizadas neste arquivo:**

- Converte entradas para números e trata conversões inválidas conforme as opções utilizadas.
- Solicita a geração de uma resposta ao modelo de linguagem.

<a id="arquivo-107"></a>

#### `PI4/Backend/services/risk_alerts.py`

**Para que serve:** Varredura de cauda de risco e disparo de um unico e-mail consolidado.

**Como funciona:** Avalia todas as metricas primeiro e devolve um payload unico. Varre o modelo inteiro e, no fim, envia no maximo um e-mail consolidado.

**Como se relaciona com o restante:** Serviços de aplicação: cache, contexto financeiro, relatórios PDF, RAG, SMTP e alertas; chamados por rotas e também diretamente pelo frontend.

**Arquivos do projeto que utiliza:** `PI4/Backend/metrics/__init__.py`, `PI4/Backend/services/dashboard_pipeline.py`, `PI4/Backend/services/email_service.py`.

**Arquivos que utilizam este módulo:** `PI4/Backend/routers/auth_router.py`, `PI4/Backend/routers/email.py`, `PI4/Backend/routers/health_router.py`, `PI4/Backend/services/memorial_report.py`, `PI4/Frontend/src/controllers/ops_menu.py`.

**Outras dependências declaradas:** `datetime`, `functools`, `os`, `pandas`, `time`.

**Responsabilidades internas:**

- `varrer_riscos`: Avalia todas as metricas primeiro e devolve um payload unico.
- `disparar_alerta_risco`: Varre o modelo inteiro e, no fim, envia no maximo um e-mail consolidado.

**Operações concretas realizadas neste arquivo:**

- Converte entradas para números e trata conversões inválidas conforme as opções utilizadas.
- Calcula percentis usados nas faixas, comparações ou classificações.

<a id="arquivo-108"></a>

#### `PI4/Backend/services/risk_report.py`

**Para que serve:** Relatório PDF da varredura real, sem disparo SMTP nem alteração de métricas.

**Como funciona:** Usa o snapshot recebido, inclusive seus limiares; não refaz a varredura.

**Como se relaciona com o restante:** Serviços de aplicação: cache, contexto financeiro, relatórios PDF, RAG, SMTP e alertas; chamados por rotas e também diretamente pelo frontend.

**Arquivos que utilizam este módulo:** `PI4/Backend/tests/test_risk_report.py`, `PI4/Frontend/src/controllers/ops_menu.py`.

**Outras dependências declaradas:** `datetime`, `io`, `pathlib`, `reportlab`, `xml`, `zoneinfo`.

**Responsabilidades internas:**

- `gerar_relatorio_riscos`: Usa o snapshot recebido, inclusive seus limiares; não refaz a varredura.

**Operações concretas realizadas neste arquivo:**

- Prepara um documento PDF com organização de páginas.
- Persiste um resultado binário em arquivo.

<a id="arquivo-109"></a>

#### `PI4/Backend/services/scenario_filter.py`

**Para que serve:** Selecao de cenarios/anos e consolidacao anual do dashboard.

**Como funciona:** Devolve recortes brutos; as medias de KPIs sao calculadas antes da consolidacao.

**Como se relaciona com o restante:** Serviços de aplicação: cache, contexto financeiro, relatórios PDF, RAG, SMTP e alertas; chamados por rotas e também diretamente pelo frontend.

**Arquivos do projeto que utiliza:** `PI4/Backend/metrics/financial_kpis.py`.

**Arquivos que utilizam este módulo:** `PI4/Backend/services/metrics_calculator.py`.

**Outras dependências declaradas:** `pandas`.

**Responsabilidades internas:**

- `filtrar_cenario_ano`: Devolve recortes brutos; as medias de KPIs sao calculadas antes da consolidacao.

**Operações concretas realizadas neste arquivo:**

- Agrupa registros para calcular resultados por conta, ano, cenário ou outra chave indicada no módulo.
- Converte entradas para números e trata conversões inválidas conforme as opções utilizadas.

<a id="pasta-022"></a>

### Pasta `PI4/Backend/tests/`

Regressões automatizadas com unittest e fixtures; verifica contratos, cálculos, geração de relatórios e comportamento de inicialização.

| Arquivo | O que faz |
|---|---|
| [test_api_contracts.py](#arquivo-110) | Regressoes dos contratos HTTP e do arranque, usando SQLite temporario. |
| [test_dashboard_pipeline.py](#arquivo-111) | Contratos do pipeline: filtros, KPIs e parquets com cache temporario. |
| [test_memorial_api.py](#arquivo-112) | Regressões do memorial dinâmico: filtros, PDF binário e botão do dashboard. |
| [test_performance_regressions.py](#arquivo-113) | Preserva resultados financeiros, filtros e inicializacao lazy do chat. |
| [test_report_notes.py](#arquivo-114) | Regressões: parecer customizado substitui o automático sem perder conteúdo. |
| [test_risk_report.py](#arquivo-115) | Verifica diagnóstico PDF e separação entre simulação de envio e risco real. |

<a id="arquivo-110"></a>

#### `PI4/Backend/tests/test_api_contracts.py`

**Para que serve:** Regressoes dos contratos HTTP e do arranque, usando SQLite temporario.

Executar: python -m unittest discover -s PI4/Backend/tests -v

**Como funciona:** Configura os valores e as integrações compartilhadas indicados por este módulo.

**Como se relaciona com o restante:** Regressões automatizadas com unittest e fixtures; verifica contratos, cálculos, geração de relatórios e comportamento de inicialização.

**Arquivos do projeto que utiliza:** `PI4/Backend/db/__init__.py`, `PI4/Backend/db/auth.py`, `PI4/Backend/db/database.py`, `PI4/Backend/db/models.py`, `PI4/Backend/main.py`, `PI4/Backend/services/__init__.py`, `PI4/Backend/services/chat_service.py`.

**Outras dependências declaradas:** `fastapi`, `pathlib`, `sys`, `tempfile`, `unittest`.

**Operações concretas realizadas neste arquivo:**

- Interrompe a execução corrente da página quando uma condição impede continuar.

**Casos de teste definidos:**

- existing paths and methods
- health and version
- login logout and logs
- auth errors and validation
- empty chat does not initialize rag
- chat sessions role and history limit
- cors preflight
- existing email and users routers

<a id="arquivo-111"></a>

#### `PI4/Backend/tests/test_dashboard_pipeline.py`

**Para que serve:** Contratos do pipeline: filtros, KPIs e parquets com cache temporario.

**Como funciona:** Configura os valores e as integrações compartilhadas indicados por este módulo.

**Como se relaciona com o restante:** Regressões automatizadas com unittest e fixtures; verifica contratos, cálculos, geração de relatórios e comportamento de inicialização.

**Arquivos do projeto que utiliza:** `PI4/Backend/data_loader/__init__.py`, `PI4/Backend/data_loader/csv_reader.py`, `PI4/Backend/services/__init__.py`, `PI4/Backend/services/dashboard_cache.py`, `PI4/Backend/services/dashboard_pipeline.py`.

**Outras dependências declaradas:** `os`, `pandas`, `pathlib`, `sys`, `tempfile`, `unittest`.

**Operações concretas realizadas neste arquivo:**

- Grava DataFrames no cache Parquet.
- Persiste um resultado binário em arquivo.

**Casos de teste definidos:**

- scenario and year selection without mutating input
- all scenarios kpis are calculated before annual average
- missing year uses scenario kpis
- empty indicators and missing scenario
- reconstructs dre accounts and values
- full cache reads on render without csv
- partial cache reconstructs raw when loaded directly
- missing cache on render does not read csv
- local csv fallback builds reusable parquets
- corrupt cache is blocked on render

<a id="arquivo-112"></a>

#### `PI4/Backend/tests/test_memorial_api.py`

**Para que serve:** Regressões do memorial dinâmico: filtros, PDF binário e botão do dashboard.

**Como funciona:** Configura os valores e as integrações compartilhadas indicados por este módulo.

**Como se relaciona com o restante:** Regressões automatizadas com unittest e fixtures; verifica contratos, cálculos, geração de relatórios e comportamento de inicialização.

**Arquivos do projeto que utiliza:** `PI4/Backend/main.py`, `PI4/Backend/services/memorial_report.py`, `PI4/Frontend/src/views/__init__.py`, `PI4/Frontend/src/views/report.py`.

**Outras dependências declaradas:** `fastapi`, `io`, `json`, `pandas`, `pathlib`, `pypdf`, `sys`, `unittest`.

**Operações concretas realizadas neste arquivo:**

- Abre um PDF para extrair seu conteúdo.

**Casos de teste definidos:**

- endpoint calcula e responde pdf
- todos media por conta e anos separados
- filtros invalidos e falha da fonte
- botao usa endpoint e entrega os mesmos bytes
- dados importados nao recebem pdf da base errada

<a id="arquivo-113"></a>

#### `PI4/Backend/tests/test_performance_regressions.py`

**Para que serve:** Preserva resultados financeiros, filtros e inicializacao lazy do chat.

**Como funciona:** Configura os valores e as integrações compartilhadas indicados por este módulo.

**Como se relaciona com o restante:** Regressões automatizadas com unittest e fixtures; verifica contratos, cálculos, geração de relatórios e comportamento de inicialização.

**Arquivos do projeto que utiliza:** `PI4/Backend/metrics/column_resolver.py`, `PI4/Backend/services/__init__.py`, `PI4/Backend/services/chat_service.py`, `PI4/Frontend/src/controllers/sidebar.py`.

**Outras dependências declaradas:** `concurrent`, `pandas`, `pathlib`, `subprocess`, `sys`, `time`, `types`, `unittest`.

**Casos de teste definidos:**

- normalization accepts non hashable values and mojibake
- official names keep precedence and iterator support
- sidebar options are unique and do not mutate data
- sidebar handles categorical values
- backend import does not load rag or streamlit
- concurrent first requests initialize only one rag
- failed initialization can be retried

<a id="arquivo-114"></a>

#### `PI4/Backend/tests/test_report_notes.py`

**Para que serve:** Regressões: parecer customizado substitui o automático sem perder conteúdo.

**Como funciona:** Configura os valores e as integrações compartilhadas indicados por este módulo.

**Como se relaciona com o restante:** Regressões automatizadas com unittest e fixtures; verifica contratos, cálculos, geração de relatórios e comportamento de inicialização.

**Arquivos do projeto que utiliza:** `PI4/Backend/services/custom_report_service.py`, `PI4/Backend/services/report_generator.py`, `PI4/Backend/services/report_insights.py`.

**Outras dependências declaradas:** `io`, `pandas`, `pathlib`, `pypdf`, `re`, `sys`, `unittest`.

**Operações concretas realizadas neste arquivo:**

- Abre um PDF para extrair seu conteúdo.

**Casos de teste definidos:**

- substituicao por bloco sem concatenar
- vazio ou padrao intacto usa automatico
- parecer longo preservado no flowable
- pdf substitui paragrafo e preserva kpis titulos

<a id="arquivo-115"></a>

#### `PI4/Backend/tests/test_risk_report.py`

**Para que serve:** Verifica diagnóstico PDF e separação entre simulação de envio e risco real.

**Como funciona:** Configura os valores e as integrações compartilhadas indicados por este módulo.

**Como se relaciona com o restante:** Regressões automatizadas com unittest e fixtures; verifica contratos, cálculos, geração de relatórios e comportamento de inicialização.

**Arquivos do projeto que utiliza:** `PI4/Backend/services/__init__.py`, `PI4/Backend/services/risk_report.py`.

**Outras dependências declaradas:** `copy`, `io`, `pathlib`, `pypdf`, `sys`, `tempfile`, `unittest`.

**Operações concretas realizadas neste arquivo:**

- Abre um PDF para extrair seu conteúdo.
- Carrega o conteúdo binário de um arquivo.

**Casos de teste definidos:**

- diagnosticos e snapshot preservado
- simulacao nao classifica modelo como critico
- cria diretorio ausente
- recusa base vazia

<a id="pasta-023"></a>

### Pasta `PI4/Frontend/`

Interface Streamlit e recursos associados; integra regras locais do backend, API HTTP e assistente.

| Arquivo | O que faz |
|---|---|
| [.env.example](#arquivo-117) | Modelo ou configuração de variáveis de ambiente |
| [Procfile](#arquivo-120) | Declara como iniciar somente o dashboard a partir da pasta Frontend. |
| [analise.ipynb](#arquivo-121) | Notebook exploratório |
| [app.py](#arquivo-122) | É a entrada do dashboard Streamlit. |
| [chat_component.py](#arquivo-123) | Injeta o chat flutuante por cima do dashboard, sem empurrar o layout. |
| [chat_widget.html](#arquivo-124) | Interface HTML/JavaScript do chat |
| [organizando.ipynb](#arquivo-125) | Notebook exploratório |
| [requirements.txt](#arquivo-126) | Manifesto de dependências Python |
| [requirements_dashboard.txt](#arquivo-127) | Manifesto de dependências Python |

<a id="arquivo-117"></a>

#### `PI4/Frontend/.env.example`

**Para que serve:** Modelo ou configuração de variáveis de ambiente

**Como funciona:** dotenv lê pares chave/valor; modelos .example documentam configuração e não são carregados automaticamente como .env.

**Como se relaciona com o restante:** Chaves conectam API, banco, SMTP, Gemini e frontend; os valores não são reproduzidos neste guia.

**Configurações declaradas, sem seus valores:** `BACKEND_URL`.

<a id="arquivo-120"></a>

#### `PI4/Frontend/Procfile`

**Para que serve:** Declara como iniciar somente o dashboard a partir da pasta Frontend.

**Como funciona:** Inicia o Streamlit usando app.py, a porta da plataforma e o endereço de escuta em todas as interfaces.

**Como se relaciona com o restante:** Process manager da plataforma executa o comando literal reproduzido abaixo.

<a id="arquivo-121"></a>

#### `PI4/Frontend/analise.ipynb`

**Para que serve:** Notebook exploratório

**Como funciona:** Organiza a exploração em 4 células, sendo 4 de código. Os resultados dependem da ordem em que as células são executadas no Jupyter.

**Como se relaciona com o restante:** Usa as bibliotecas pandas. Não é executado pelos comandos de publicação declarados.

<a id="arquivo-122"></a>

#### `PI4/Frontend/app.py`

**Para que serve:** É a entrada do dashboard Streamlit.

**Como funciona:** Prepara a página, verifica a sessão do usuário, carrega os dados, permite trocar a base por upload e aplica filtros de cenário, ano e perfil. Monta o contexto da tela, aciona as views e disponibiliza o assistente.

**Como se relaciona com o restante:** Interface Streamlit e recursos associados; integra regras locais do backend, API HTTP e assistente.

**Arquivos do projeto que utiliza:** `PI4/Backend/diag.py`, `PI4/Backend/metrics/__init__.py`, `PI4/Frontend/src/config/i18n.py`, `PI4/Frontend/src/controllers/auth.py`, `PI4/Frontend/src/controllers/bootstrap.py`, `PI4/Frontend/src/controllers/data_input.py`, `PI4/Frontend/src/controllers/modals.py`, `PI4/Frontend/src/controllers/navigation.py`, `PI4/Frontend/src/controllers/page_setup.py`, `PI4/Frontend/src/controllers/sidebar.py`, `PI4/Frontend/src/controllers/stability.py`, `PI4/Frontend/src/views/ai_assistant/panel.py`.

**Outras dependências declaradas:** `logging`, `pandas`, `pathlib`, `streamlit`, `sys`.

**Responsabilidades internas:**

- `montar_indicadores_customizados`: Evita recalcular indicadores de bases customizadas em todo rerun.

**Operações concretas realizadas neste arquivo:**

- Solicita uma nova execução da página Streamlit para refletir mudanças de estado.
- Interrompe a execução corrente da página quando uma condição impede continuar.

<a id="arquivo-123"></a>

#### `PI4/Frontend/chat_component.py`

**Para que serve:** Injeta o chat flutuante por cima do dashboard, sem empurrar o layout.

**Como funciona:** Lê chat_widget.html e sobrepõe a janela ao dashboard.

**Como se relaciona com o restante:** Interface Streamlit e recursos associados; integra regras locais do backend, API HTTP e assistente.

**Outras dependências declaradas:** `pathlib`, `streamlit`.

**Responsabilidades internas:**

- `render_floating_chat`: Lê chat_widget.html e sobrepõe a janela ao dashboard.

<a id="arquivo-124"></a>

#### `PI4/Frontend/chat_widget.html`

**Para que serve:** Interface HTML/JavaScript do chat

**Como funciona:** Markup, estilos e scripts de interação do widget; renderizado no navegador/iframe.

**Como se relaciona com o restante:** Integra componente Streamlit, estado de chat e chamadas/handlers declarados no código.

<a id="arquivo-125"></a>

#### `PI4/Frontend/organizando.ipynb`

**Para que serve:** Notebook exploratório

**Como funciona:** Organiza a exploração em 5 células, sendo 5 de código. Os resultados dependem da ordem em que as células são executadas no Jupyter.

**Como se relaciona com o restante:** Usa as bibliotecas pandas. Não é executado pelos comandos de publicação declarados.

<a id="arquivo-126"></a>

#### `PI4/Frontend/requirements.txt`

**Para que serve:** Manifesto de dependências Python

**Como funciona:** Cada requisito limita versões e/ou inclui outro manifesto; pip resolve e instala a árvore transitiva.

**Como se relaciona com o restante:** Consumido por comandos de build locais/Render; não representa necessariamente um lockfile do ambiente atual.

<a id="arquivo-127"></a>

#### `PI4/Frontend/requirements_dashboard.txt`

**Para que serve:** Manifesto de dependências Python

**Como funciona:** Cada requisito limita versões e/ou inclui outro manifesto; pip resolve e instala a árvore transitiva.

**Como se relaciona com o restante:** Consumido por comandos de build locais/Render; não representa necessariamente um lockfile do ambiente atual.

<a id="pasta-024"></a>

### Pasta `PI4/Frontend/.streamlit/`

Configuração do servidor e aparência do Streamlit; arquivos lidos pelo framework ao iniciar.

| Arquivo | O que faz |
|---|---|
| [config.toml](#arquivo-118) | Configuração TOML |
| [credentials.toml](#arquivo-119) | Configuração TOML |

<a id="arquivo-118"></a>

#### `PI4/Frontend/.streamlit/config.toml`

**Para que serve:** Configuração TOML

**Como funciona:** Pares e seções lidos pelo framework/ferramenta correspondente.

**Como se relaciona com o restante:** Streamlit quando em .streamlit; credenciais têm conteúdo protegido.

<a id="arquivo-119"></a>

#### `PI4/Frontend/.streamlit/credentials.toml`

**Para que serve:** Configuração TOML

**Como funciona:** Pares e seções lidos pelo framework/ferramenta correspondente.

**Como se relaciona com o restante:** Streamlit quando em .streamlit; credenciais têm conteúdo protegido.

<a id="pasta-025"></a>

### Pasta `PI4/Frontend/src/`

Interface Streamlit e recursos associados; integra regras locais do backend, API HTTP e assistente.

| Arquivo | O que faz |
|---|---|
| [__init__.py](#arquivo-128) | Pacote raiz do painel CTI. |

<a id="arquivo-128"></a>

#### `PI4/Frontend/src/__init__.py`

**Para que serve:** Pacote raiz do painel CTI.

**Como funciona:** Reúne constantes, imports e exports para os consumidores do pacote.

**Como se relaciona com o restante:** Interface Streamlit e recursos associados; integra regras locais do backend, API HTTP e assistente.

<a id="pasta-026"></a>

### Pasta `PI4/Frontend/src/components/`

Componentes Streamlit reutilizáveis para cabeçalhos, filtros e cartões.

| Arquivo | O que faz |
|---|---|
| [__init__.py](#arquivo-129) | Componentes visuais reutilizaveis do Streamlit. |
| [header_component.py](#arquivo-130) | Componentes visuais de cabecalho. |
| [kpi_cards_component.py](#arquivo-131) | Componentes visuais para cartoes de KPI. |
| [sidebar_filters.py](#arquivo-132) | Componentes visuais de filtros laterais. |

<a id="arquivo-129"></a>

#### `PI4/Frontend/src/components/__init__.py`

**Para que serve:** Componentes visuais reutilizaveis do Streamlit.

**Como funciona:** Reúne constantes, imports e exports para os consumidores do pacote.

**Como se relaciona com o restante:** Componentes Streamlit reutilizáveis para cabeçalhos, filtros e cartões.

**Arquivos do projeto que utiliza:** `PI4/Frontend/src/components/header_component.py`, `PI4/Frontend/src/components/kpi_cards_component.py`, `PI4/Frontend/src/components/sidebar_filters.py`.

<a id="arquivo-130"></a>

#### `PI4/Frontend/src/components/header_component.py`

**Para que serve:** Componentes visuais de cabecalho.

**Como funciona:** Renderiza o banner de auditoria do filtro ativo.

**Como se relaciona com o restante:** Componentes Streamlit reutilizáveis para cabeçalhos, filtros e cartões.

**Arquivos do projeto que utiliza:** `PI4/Frontend/src/controllers/headers.py`.

**Arquivos que utilizam este módulo:** `PI4/Frontend/src/components/__init__.py`.

**Outras dependências declaradas:** `__future__`.

**Responsabilidades internas:**

- `render_audit_banner`: Renderiza o banner de auditoria do filtro ativo.

<a id="arquivo-131"></a>

#### `PI4/Frontend/src/components/kpi_cards_component.py`

**Para que serve:** Componentes visuais para cartoes de KPI.

**Como funciona:** Renderiza uma linha de cards de KPI.

**Como se relaciona com o restante:** Componentes Streamlit reutilizáveis para cabeçalhos, filtros e cartões.

**Arquivos do projeto que utiliza:** `PI4/Frontend/src/controllers/kpis/rendering.py`.

**Arquivos que utilizam este módulo:** `PI4/Frontend/src/components/__init__.py`.

**Outras dependências declaradas:** `collections`.

**Responsabilidades internas:**

- `render_kpi_cards`: Renderiza uma linha de cards de KPI.

<a id="arquivo-132"></a>

#### `PI4/Frontend/src/components/sidebar_filters.py`

**Para que serve:** Componentes visuais de filtros laterais.

**Como funciona:** Renderiza seletor de idioma. Renderiza seletor de persona. Renderiza filtros principais da sidebar.

**Como se relaciona com o restante:** Componentes Streamlit reutilizáveis para cabeçalhos, filtros e cartões.

**Arquivos do projeto que utiliza:** `PI4/Frontend/src/controllers/sidebar.py`.

**Arquivos que utilizam este módulo:** `PI4/Frontend/src/components/__init__.py`.

**Outras dependências declaradas:** `pandas`.

**Responsabilidades internas:**

- `render_language`: Renderiza seletor de idioma.
- `render_persona_selector`: Renderiza seletor de persona.
- `render_filters`: Renderiza filtros principais da sidebar.

<a id="pasta-027"></a>

### Pasta `PI4/Frontend/src/config/`

Configuração de caminhos/API, tradução PT/EN e glossário dos indicadores.

| Arquivo | O que faz |
|---|---|
| [__init__.py](#arquivo-133) | Constantes e caminhos do painel CTI. |
| [glossary.py](#arquivo-134) | Glossário executivo dos indicadores — tooltips PT-BR / EN-US. |
| [i18n.py](#arquivo-135) | Internacionalização PT-BR / EN-US do dashboard CTI. |

<a id="arquivo-133"></a>

#### `PI4/Frontend/src/config/__init__.py`

**Para que serve:** Constantes e caminhos do painel CTI.

**Como funciona:** Converte enderecos de bind em enderecos locais acessiveis. Usa a API publica configurada, com fallback local na porta 8000.

**Como se relaciona com o restante:** Configuração de caminhos/API, tradução PT/EN e glossário dos indicadores.

**Arquivos que utilizam este módulo:** `PI4/Frontend/src/controllers/auth.py`, `PI4/Frontend/src/controllers/bootstrap.py`, `PI4/Frontend/src/controllers/charts/histograms.py`, `PI4/Frontend/src/controllers/charts/risk_band.py`, `PI4/Frontend/src/controllers/charts/time_series.py`, `PI4/Frontend/src/controllers/headers.py`, `PI4/Frontend/src/controllers/kpis/rendering.py`, `PI4/Frontend/src/controllers/local_api.py`, `PI4/Frontend/src/controllers/navigation.py`, `PI4/Frontend/src/controllers/sidebar.py`, `PI4/Frontend/src/models/api_client.py`, `PI4/Frontend/src/models/rag_engine/config.py`, `PI4/Frontend/src/models/rag_engine/documents.py`, `PI4/Frontend/src/views/capital_giro.py`, `PI4/Frontend/src/views/comparar.py`, `PI4/Frontend/src/views/distribuicao.py`, `PI4/Frontend/src/views/faixa_risco.py`, `PI4/Frontend/src/views/mapeamento_risco.py`, `PI4/Frontend/src/views/persona_tabs/ceo.py`, `PI4/Frontend/src/views/persona_tabs/comparison_ceo_cfo.py`, `PI4/Frontend/src/views/persona_tabs/comparison_concession.py`, `PI4/Frontend/src/views/persona_tabs/comparison_helpers.py`, `PI4/Frontend/src/views/persona_tabs/concession.py`, `PI4/Frontend/src/views/persona_tabs/shareholders.py`, `PI4/Frontend/src/views/persona_tabs/styles.py`.

**Outras dependências declaradas:** `dotenv`, `os`, `pathlib`, `urllib`.

**Responsabilidades internas:**

- `_rewrite_bind_all`: Converte enderecos de bind em enderecos locais acessiveis.
- `resolve_api_base_url`: Usa a API publica configurada, com fallback local na porta 8000.

<a id="arquivo-134"></a>

#### `PI4/Frontend/src/config/glossary.py`

**Para que serve:** Glossário executivo dos indicadores — tooltips PT-BR / EN-US.

**Como funciona:** Retorna a definição no idioma ativo; fallback PT se a chave não existir. Texto para o parâmetro ``help`` do Streamlit; ``None`` se a chave for desconhecida. Concatena definições (ex.: métrica + leitura do card).

**Como se relaciona com o restante:** Configuração de caminhos/API, tradução PT/EN e glossário dos indicadores.

**Arquivos do projeto que utiliza:** `PI4/Frontend/src/config/i18n.py`.

**Arquivos que utilizam este módulo:** `PI4/Frontend/src/controllers/headers.py`, `PI4/Frontend/src/controllers/kpis/personas.py`, `PI4/Frontend/src/controllers/sidebar.py`, `PI4/Frontend/src/models/rag_engine/documents.py`, `PI4/Frontend/src/views/comparar.py`, `PI4/Frontend/src/views/distribuicao.py`, `PI4/Frontend/src/views/faixa_risco.py`, `PI4/Frontend/src/views/mapeamento_risco.py`, `PI4/Frontend/src/views/prazos_ciclo.py`.

**Outras dependências declaradas:** `__future__`.

**Responsabilidades internas:**

- `glossary`: Retorna a definição no idioma ativo; fallback PT se a chave não existir.
- `help_text`: Texto para o parâmetro ``help`` do Streamlit; ``None`` se a chave for desconhecida.
- `help_join`: Concatena definições (ex.: métrica + leitura do card).

<a id="arquivo-135"></a>

#### `PI4/Frontend/src/config/i18n.py`

**Para que serve:** Internacionalização PT-BR / EN-US do dashboard CTI.

**Como funciona:** Retorna texto traduzido; fallback PT se a chave não existir no idioma ativo. Alias de ``t`` (API pedida no briefing).

**Como se relaciona com o restante:** Configuração de caminhos/API, tradução PT/EN e glossário dos indicadores.

**Arquivos que utilizam este módulo:** `PI4/Frontend/app.py`, `PI4/Frontend/src/config/glossary.py`, `PI4/Frontend/src/controllers/ai_sidebar_right.py`, `PI4/Frontend/src/controllers/auth.py`, `PI4/Frontend/src/controllers/bootstrap.py`, `PI4/Frontend/src/controllers/charts/histograms.py`, `PI4/Frontend/src/controllers/charts/risk_band.py`, `PI4/Frontend/src/controllers/charts/time_series.py`, `PI4/Frontend/src/controllers/custom_analysis.py`, `PI4/Frontend/src/controllers/data_input.py`, `PI4/Frontend/src/controllers/headers.py`, `PI4/Frontend/src/controllers/kpis/ceo.py`, `PI4/Frontend/src/controllers/kpis/concession.py`, `PI4/Frontend/src/controllers/kpis/personas.py`, `PI4/Frontend/src/controllers/kpis/rendering.py`, `PI4/Frontend/src/controllers/kpis/shareholders.py`, `PI4/Frontend/src/controllers/navigation.py`, `PI4/Frontend/src/controllers/ops_menu.py`, `PI4/Frontend/src/controllers/resilience.py`, `PI4/Frontend/src/controllers/sidebar.py`, `PI4/Frontend/src/controllers/test_sandbox.py`, `PI4/Frontend/src/models/financial_metrics/labels.py`, `PI4/Frontend/src/models/formatting/numbers.py`, `PI4/Frontend/src/models/formatting/scenarios.py`, `PI4/Frontend/src/models/formatting/tables.py`, `PI4/Frontend/src/models/formatting/texts.py`, `PI4/Frontend/src/views/ai_assistant/context.py`, `PI4/Frontend/src/views/ai_assistant/panel.py`, `PI4/Frontend/src/views/capital_giro.py`, `PI4/Frontend/src/views/como_ler.py`, `PI4/Frontend/src/views/comparar.py`, `PI4/Frontend/src/views/distribuicao.py`, `PI4/Frontend/src/views/faixa_risco.py`, `PI4/Frontend/src/views/mapeamento_risco.py`, `PI4/Frontend/src/views/persona_tabs/admin_users.py`, `PI4/Frontend/src/views/persona_tabs/audit.py`, `PI4/Frontend/src/views/persona_tabs/ceo.py`, `PI4/Frontend/src/views/persona_tabs/comparison.py`, `PI4/Frontend/src/views/persona_tabs/comparison_ceo_cfo.py`, `PI4/Frontend/src/views/persona_tabs/comparison_concession.py`, `PI4/Frontend/src/views/persona_tabs/comparison_helpers.py`, `PI4/Frontend/src/views/persona_tabs/comparison_shareholders.py`, `PI4/Frontend/src/views/persona_tabs/concession.py`, `PI4/Frontend/src/views/persona_tabs/custom_analysis.py`, `PI4/Frontend/src/views/persona_tabs/shareholders.py`, `PI4/Frontend/src/views/prazos_ciclo.py`, `PI4/Frontend/src/views/report.py`.

**Outras dependências declaradas:** `streamlit`, `typing`.

**Responsabilidades internas:**

- `t`: Retorna texto traduzido; fallback PT se a chave não existir no idioma ativo.
- `get_text`: Alias de ``t`` (API pedida no briefing).

<a id="pasta-028"></a>

### Pasta `PI4/Frontend/src/controllers/`

Controladores Streamlit: coordenam estado de sessão, filtros, autenticação, navegação e composição de componentes.

| Arquivo | O que faz |
|---|---|
| [__init__.py](#arquivo-136) | Componentes de UI do painel CTI — imports sob demanda (evita ciclo no hot-reload). |
| [ai_sidebar_right.py](#arquivo-137) | Abre o Assistente CTI numa coluna à direita do dashboard. |
| [auth.py](#arquivo-138) | Login e hierarquia de acesso (RBAC) do dashboard CTI via API. |
| [bootstrap.py](#arquivo-139) | Estado global e cabecalho do app Streamlit. |
| [custom_analysis.py](#arquivo-144) | Estado e formulario de analises financeiras customizadas. |
| [data_input.py](#arquivo-145) | Entrada temporaria de novos dados para o dashboard. |
| [headers.py](#arquivo-146) | Cabeçalhos, banners e auditoria. |
| [local_api.py](#arquivo-155) | Health check so sob pedido explicito. Nao corre no arranque da pagina. |
| [modals.py](#arquivo-156) | Estados independentes dos modais de Relatorio e Assistente IA. |
| [navigation.py](#arquivo-157) | Navegacao principal e renderizacao das abas analiticas. |
| [ops_menu.py](#arquivo-158) | Menu suspenso de tres pontinhos com acoes operacionais do dashboard. |
| [page_setup.py](#arquivo-159) | Configuracao visual global da aplicacao Streamlit. |
| [resilience.py](#arquivo-160) | Isolamento de falhas na renderização Streamlit. |
| [session_cookie.py](#arquivo-161) | Sessao persistente em cookie do navegador (TTL de inatividade). |
| [sidebar.py](#arquivo-162) | Filtros laterais, idioma e seletor de persona. |
| [stability.py](#arquivo-163) | Trocas rapidas de visao sem derrubar o websocket do Streamlit. |
| [test_sandbox.py](#arquivo-164) | Sandbox temporario da persona Teste. |

<a id="arquivo-136"></a>

#### `PI4/Frontend/src/controllers/__init__.py`

**Para que serve:** Componentes de UI do painel CTI — imports sob demanda (evita ciclo no hot-reload).

**Como funciona:** Reúne constantes, imports e exports para os consumidores do pacote.

**Como se relaciona com o restante:** Controladores Streamlit: coordenam estado de sessão, filtros, autenticação, navegação e composição de componentes.

**Arquivos do projeto que utiliza:** `PI4/Frontend/src/controllers/ai_sidebar_right.py`, `PI4/Frontend/src/controllers/charts/__init__.py`, `PI4/Frontend/src/controllers/headers.py`, `PI4/Frontend/src/controllers/kpis/__init__.py`, `PI4/Frontend/src/controllers/resilience.py`, `PI4/Frontend/src/controllers/sidebar.py`.

**Outras dependências declaradas:** `__future__`.

<a id="arquivo-137"></a>

#### `PI4/Frontend/src/controllers/ai_sidebar_right.py`

**Para que serve:** Abre o Assistente CTI numa coluna à direita do dashboard.

**Como funciona:** Fecha: só o `>>`. Abre: dashboard à esquerda e o chat à direita.

**Como se relaciona com o restante:** Controladores Streamlit: coordenam estado de sessão, filtros, autenticação, navegação e composição de componentes.

**Arquivos do projeto que utiliza:** `PI4/Frontend/src/config/i18n.py`, `PI4/Frontend/src/controllers/bootstrap.py`, `PI4/Frontend/src/controllers/resilience.py`, `PI4/Frontend/src/views/ai_assistant/__init__.py`.

**Arquivos que utilizam este módulo:** `PI4/Frontend/src/controllers/__init__.py`.

**Outras dependências declaradas:** `collections`, `streamlit`.

**Responsabilidades internas:**

- `render_ai_layout`: Fecha: só o `>>`. Abre: dashboard à esquerda e o chat à direita.

<a id="arquivo-138"></a>

#### `PI4/Frontend/src/controllers/auth.py`

**Para que serve:** Login e hierarquia de acesso (RBAC) do dashboard CTI via API.

**Como funciona:** Mostra o toast do login uma unica vez, sem bloco fixo na tela. Le o cookie antes do login; restaura a sessao se o TTL de 5 min ainda valer. Renova o cookie no maximo a cada 90s, para nao forcar reruns em cadeia. Mesma validacao da API, no SQLite do processo Streamlit, se o uvicorn estiver em baixo.

**Como se relaciona com o restante:** Controladores Streamlit: coordenam estado de sessão, filtros, autenticação, navegação e composição de componentes.

**Arquivos do projeto que utiliza:** `PI4/Backend/db/__init__.py`, `PI4/Backend/db/auth.py`, `PI4/Frontend/src/config/__init__.py`, `PI4/Frontend/src/config/i18n.py`, `PI4/Frontend/src/controllers/session_cookie.py`, `PI4/Frontend/src/models/api_client.py`.

**Arquivos que utilizam este módulo:** `PI4/Frontend/app.py`, `PI4/Frontend/src/controllers/navigation.py`, `PI4/Frontend/src/controllers/ops_menu.py`, `PI4/Frontend/src/controllers/sidebar.py`, `PI4/Frontend/src/views/ai_assistant/panel.py`, `PI4/Frontend/src/views/persona_tabs/admin_users.py`, `PI4/Frontend/src/views/persona_tabs/audit.py`.

**Outras dependências declaradas:** `logging`, `streamlit`, `sys`, `time`.

**Responsabilidades internas:**

- `flush_login_email_toast`: Mostra o toast do login uma unica vez, sem bloco fixo na tela.
- `restore_persistent_session`: Le o cookie antes do login; restaura a sessao se o TTL de 5 min ainda valer.
- `refresh_session_cookie`: Renova o cookie no maximo a cada 90s, para nao forcar reruns em cadeia.
- `_autenticar_local`: Mesma validacao da API, no SQLite do processo Streamlit, se o uvicorn estiver em baixo.

**Operações concretas realizadas neste arquivo:**

- Solicita uma nova execução da página Streamlit para refletir mudanças de estado.

<a id="arquivo-139"></a>

#### `PI4/Frontend/src/controllers/bootstrap.py`

**Para que serve:** Estado global e cabecalho do app Streamlit.

**Como funciona:** Estado derivado usado pelas views do Streamlit. Cacheia parquet/CSV local. Sem PostgreSQL. Mantido por compatibilidade — recorte SQL esta desligado. Carrega o dashboard pelos parquets (ou CSV local). Sem Supabase. Monta contexto visual usando metricas calculadas pelo backend. Renderiza titulo, banner e KPIs ja processados.

**Como se relaciona com o restante:** Controladores Streamlit: coordenam estado de sessão, filtros, autenticação, navegação e composição de componentes.

**Arquivos do projeto que utiliza:** `PI4/Backend/diag.py`, `PI4/Backend/services/__init__.py`, `PI4/Backend/services/dashboard_pipeline.py`, `PI4/Frontend/src/config/__init__.py`, `PI4/Frontend/src/config/i18n.py`, `PI4/Frontend/src/controllers/data_input.py`, `PI4/Frontend/src/controllers/headers.py`, `PI4/Frontend/src/controllers/kpis/__init__.py`, `PI4/Frontend/src/controllers/modals.py`, `PI4/Frontend/src/controllers/ops_menu.py`, `PI4/Frontend/src/controllers/resilience.py`, `PI4/Frontend/src/models/formatting/__init__.py`.

**Arquivos que utilizam este módulo:** `PI4/Frontend/app.py`, `PI4/Frontend/src/controllers/ai_sidebar_right.py`, `PI4/Frontend/src/controllers/navigation.py`, `PI4/Frontend/src/controllers/test_sandbox.py`, `PI4/Frontend/src/views/persona_tabs/common.py`, `PI4/Frontend/src/views/report.py`.

**Outras dependências declaradas:** `dataclasses`, `pandas`, `pathlib`, `streamlit`, `sys`.

**Responsabilidades internas:**

- `AppContext`: Estado derivado usado pelas views do Streamlit.
- `carregar_pipeline`: Cacheia parquet/CSV local. Sem PostgreSQL.
- `carregar_recorte`: Mantido por compatibilidade — recorte SQL esta desligado.
- `carregar_estado`: Carrega o dashboard pelos parquets (ou CSV local). Sem Supabase.
- `montar_contexto`: Monta contexto visual usando metricas calculadas pelo backend.
- `render_cabecalho`: Renderiza titulo, banner e KPIs ja processados.

<a id="arquivo-144"></a>

#### `PI4/Frontend/src/controllers/custom_analysis.py`

**Para que serve:** Estado e formulario de analises financeiras customizadas.

**Como funciona:** Chave unica do modal de analise customizada por persona. Abre/fecha o modal e limpa a chave legada.

**Como se relaciona com o restante:** Controladores Streamlit: coordenam estado de sessão, filtros, autenticação, navegação e composição de componentes.

**Arquivos do projeto que utiliza:** `PI4/Frontend/src/config/i18n.py`, `PI4/Frontend/src/models/financial_metrics/__init__.py`.

**Arquivos que utilizam este módulo:** `PI4/Frontend/src/controllers/navigation.py`.

**Outras dependências declaradas:** `streamlit`.

**Responsabilidades internas:**

- `custom_analysis_modal_key`: Chave unica do modal de analise customizada por persona.
- `set_custom_analysis_modal`: Abre/fecha o modal e limpa a chave legada.

**Operações concretas realizadas neste arquivo:**

- Recebe uma seleção do usuário na interface.
- Solicita uma nova execução da página Streamlit para refletir mudanças de estado.

<a id="arquivo-145"></a>

#### `PI4/Frontend/src/controllers/data_input.py`

**Para que serve:** Entrada temporaria de novos dados para o dashboard.

**Como funciona:** Nao guarda a base de 1M linhas no session_state — isso estourava RAM e gerava 429. Renderiza insercao de dados na sidebar e retorna o DataFrame ativo.

**Como se relaciona com o restante:** Controladores Streamlit: coordenam estado de sessão, filtros, autenticação, navegação e composição de componentes.

**Arquivos do projeto que utiliza:** `PI4/Frontend/src/config/i18n.py`, `PI4/Frontend/src/models/formatting/tables.py`, `PI4/Frontend/src/models/loaders.py`.

**Arquivos que utilizam este módulo:** `PI4/Frontend/app.py`, `PI4/Frontend/src/controllers/bootstrap.py`, `PI4/Frontend/src/views/persona_tabs/common.py`, `PI4/Frontend/src/views/report.py`.

**Outras dependências declaradas:** `io`, `pandas`, `streamlit`, `traceback`.

**Responsabilidades internas:**

- `_init_datasets`: Nao guarda a base de 1M linhas no session_state — isso estourava RAM e gerava 429.
- `render_data_input`: Renderiza insercao de dados na sidebar e retorna o DataFrame ativo.

**Operações concretas realizadas neste arquivo:**

- Converte entradas para números e trata conversões inválidas conforme as opções utilizadas.
- Aplica os valores de substituição definidos para dados ausentes.
- Disponibiliza um arquivo para download na interface.
- Recebe arquivos enviados pelo usuário.
- Recebe uma seleção do usuário na interface.
- Solicita uma nova execução da página Streamlit para refletir mudanças de estado.

<a id="arquivo-146"></a>

#### `PI4/Frontend/src/controllers/headers.py`

**Para que serve:** Cabeçalhos, banners e auditoria.

**Como funciona:** Nao materializa o recorte completo em todo rerun — isso derrubava o websocket. Título de seção com tooltip nativo (ⓘ) a partir do glossário.

**Como se relaciona com o restante:** Controladores Streamlit: coordenam estado de sessão, filtros, autenticação, navegação e composição de componentes.

**Arquivos do projeto que utiliza:** `PI4/Frontend/src/config/__init__.py`, `PI4/Frontend/src/config/glossary.py`, `PI4/Frontend/src/config/i18n.py`, `PI4/Frontend/src/models/formatting/__init__.py`, `PI4/Frontend/src/models/formatting/tables.py`.

**Arquivos que utilizam este módulo:** `PI4/Frontend/src/components/header_component.py`, `PI4/Frontend/src/controllers/__init__.py`, `PI4/Frontend/src/controllers/bootstrap.py`, `PI4/Frontend/src/controllers/navigation.py`, `PI4/Frontend/src/views/capital_giro.py`, `PI4/Frontend/src/views/comparar.py`, `PI4/Frontend/src/views/distribuicao.py`, `PI4/Frontend/src/views/faixa_risco.py`, `PI4/Frontend/src/views/mapeamento_risco.py`, `PI4/Frontend/src/views/prazos_ciclo.py`.

**Outras dependências declaradas:** `pandas`, `streamlit`.

**Responsabilidades internas:**

- `expander_auditoria_base`: Nao materializa o recorte completo em todo rerun — isso derrubava o websocket.
- `heading_with_help`: Título de seção com tooltip nativo (ⓘ) a partir do glossário.

**Operações concretas realizadas neste arquivo:**

- Converte entradas para números e trata conversões inválidas conforme as opções utilizadas.

<a id="arquivo-155"></a>

#### `PI4/Frontend/src/controllers/local_api.py`

**Para que serve:** Health check so sob pedido explicito. Nao corre no arranque da pagina.

**Como funciona:** Intencionalmente inerte no arranque. Login e que fala com a API.

**Como se relaciona com o restante:** Controladores Streamlit: coordenam estado de sessão, filtros, autenticação, navegação e composição de componentes.

**Arquivos do projeto que utiliza:** `PI4/Frontend/src/config/__init__.py`.

**Outras dependências declaradas:** `__future__`.

**Responsabilidades internas:**

- `probe_api`: Intencionalmente inerte no arranque. Login e que fala com a API.

<a id="arquivo-156"></a>

#### `PI4/Frontend/src/controllers/modals.py`

**Para que serve:** Estados independentes dos modais de Relatorio e Assistente IA.

**Como funciona:** Configura os valores e as integrações compartilhadas indicados por este módulo.

**Como se relaciona com o restante:** Controladores Streamlit: coordenam estado de sessão, filtros, autenticação, navegação e composição de componentes.

**Arquivos do projeto que utiliza:** `PI4/Backend/diag.py`.

**Arquivos que utilizam este módulo:** `PI4/Frontend/app.py`, `PI4/Frontend/src/controllers/bootstrap.py`, `PI4/Frontend/src/controllers/navigation.py`, `PI4/Frontend/src/controllers/stability.py`, `PI4/Frontend/src/views/ai_assistant/panel.py`, `PI4/Frontend/src/views/report.py`.

**Outras dependências declaradas:** `inspect`, `streamlit`.

<a id="arquivo-157"></a>

#### `PI4/Frontend/src/controllers/navigation.py`

**Para que serve:** Navegacao principal e renderizacao das abas analiticas.

**Como funciona:** Configura os valores e as integrações compartilhadas indicados por este módulo.

**Como se relaciona com o restante:** Controladores Streamlit: coordenam estado de sessão, filtros, autenticação, navegação e composição de componentes.

**Arquivos do projeto que utiliza:** `PI4/Backend/diag.py`, `PI4/Frontend/src/config/__init__.py`, `PI4/Frontend/src/config/i18n.py`, `PI4/Frontend/src/controllers/auth.py`, `PI4/Frontend/src/controllers/bootstrap.py`, `PI4/Frontend/src/controllers/custom_analysis.py`, `PI4/Frontend/src/controllers/headers.py`, `PI4/Frontend/src/controllers/modals.py`, `PI4/Frontend/src/controllers/resilience.py`, `PI4/Frontend/src/controllers/test_sandbox.py`, `PI4/Frontend/src/views/__init__.py`, `PI4/Frontend/src/views/capital_giro.py`, `PI4/Frontend/src/views/como_ler.py`, `PI4/Frontend/src/views/comparar.py`, `PI4/Frontend/src/views/distribuicao.py`, `PI4/Frontend/src/views/faixa_risco.py`, `PI4/Frontend/src/views/mapeamento_risco.py`, `PI4/Frontend/src/views/persona_tabs/__init__.py`, `PI4/Frontend/src/views/prazos_ciclo.py`, `PI4/Frontend/src/views/report.py`.

**Arquivos que utilizam este módulo:** `PI4/Frontend/app.py`.

**Outras dependências declaradas:** `streamlit`.

<a id="arquivo-158"></a>

#### `PI4/Frontend/src/controllers/ops_menu.py`

**Para que serve:** Menu suspenso de tres pontinhos com acoes operacionais do dashboard.

**Como funciona:** Nao dispara e-mail nem aviso. So marca a sessao para nao repetir o login.

**Como se relaciona com o restante:** Controladores Streamlit: coordenam estado de sessão, filtros, autenticação, navegação e composição de componentes.

**Arquivos do projeto que utiliza:** `PI4/Backend/services/email_service.py`, `PI4/Backend/services/risk_alerts.py`, `PI4/Backend/services/risk_report.py`, `PI4/Frontend/src/config/i18n.py`, `PI4/Frontend/src/controllers/auth.py`, `PI4/Frontend/src/models/api_client.py`.

**Arquivos que utilizam este módulo:** `PI4/Frontend/src/controllers/bootstrap.py`.

**Outras dependências declaradas:** `streamlit`.

**Responsabilidades internas:**

- `garantir_varredura_silenciosa`: Nao dispara e-mail nem aviso. So marca a sessao para nao repetir o login.

**Operações concretas realizadas neste arquivo:**

- Disponibiliza um arquivo para download na interface.
- Apresenta uma tabela interativa na interface.
- Solicita uma nova execução da página Streamlit para refletir mudanças de estado.

<a id="arquivo-159"></a>

#### `PI4/Frontend/src/controllers/page_setup.py`

**Para que serve:** Configuracao visual global da aplicacao Streamlit.

**Como funciona:** Configura os valores e as integrações compartilhadas indicados por este módulo.

**Como se relaciona com o restante:** Controladores Streamlit: coordenam estado de sessão, filtros, autenticação, navegação e composição de componentes.

**Arquivos que utilizam este módulo:** `PI4/Frontend/app.py`.

**Outras dependências declaradas:** `streamlit`.

<a id="arquivo-160"></a>

#### `PI4/Frontend/src/controllers/resilience.py`

**Para que serve:** Isolamento de falhas na renderização Streamlit.

**Como funciona:** Executa um bloco de UI sem derrubar o restante do painel. Decorator para isolar falhas de uma aba inteira.

**Como se relaciona com o restante:** Controladores Streamlit: coordenam estado de sessão, filtros, autenticação, navegação e composição de componentes.

**Arquivos do projeto que utiliza:** `PI4/Frontend/src/config/i18n.py`.

**Arquivos que utilizam este módulo:** `PI4/Frontend/src/controllers/__init__.py`, `PI4/Frontend/src/controllers/ai_sidebar_right.py`, `PI4/Frontend/src/controllers/bootstrap.py`, `PI4/Frontend/src/controllers/navigation.py`, `PI4/Frontend/src/views/ai_assistant/panel.py`, `PI4/Frontend/src/views/capital_giro.py`, `PI4/Frontend/src/views/como_ler.py`, `PI4/Frontend/src/views/comparar.py`, `PI4/Frontend/src/views/distribuicao.py`, `PI4/Frontend/src/views/faixa_risco.py`, `PI4/Frontend/src/views/mapeamento_risco.py`, `PI4/Frontend/src/views/prazos_ciclo.py`.

**Outras dependências declaradas:** `collections`, `functools`, `streamlit`, `traceback`, `typing`.

**Responsabilidades internas:**

- `safe_render`: Executa um bloco de UI sem derrubar o restante do painel.
- `resilient_view`: Decorator para isolar falhas de uma aba inteira.

<a id="arquivo-161"></a>

#### `PI4/Frontend/src/controllers/session_cookie.py`

**Para que serve:** Sessao persistente em cookie do navegador (TTL de inatividade).

**Como funciona:** CookieManager real gerava 429 no proxy da Render. Sessao fica so no session_state. Le cookies sem st.rerun — o rerun automatico gerava 429 no proxy da Render.

**Como se relaciona com o restante:** Controladores Streamlit: coordenam estado de sessão, filtros, autenticação, navegação e composição de componentes.

**Arquivos que utilizam este módulo:** `PI4/Frontend/src/controllers/auth.py`.

**Outras dependências declaradas:** `base64`, `datetime`, `hashlib`, `hmac`, `json`, `os`, `pathlib`, `streamlit`, `time`, `typing`.

**Responsabilidades internas:**

- `_CookieMorto`: CookieManager real gerava 429 no proxy da Render. Sessao fica so no session_state.
- `bootstrap_cookies`: Le cookies sem st.rerun — o rerun automatico gerava 429 no proxy da Render.

<a id="arquivo-162"></a>

#### `PI4/Frontend/src/controllers/sidebar.py`

**Para que serve:** Filtros laterais, idioma e seletor de persona.

**Como funciona:** Seletor no topo da sidebar; persiste em ``st.session_state['lang']``.

**Como se relaciona com o restante:** Controladores Streamlit: coordenam estado de sessão, filtros, autenticação, navegação e composição de componentes.

**Arquivos do projeto que utiliza:** `PI4/Backend/diag.py`, `PI4/Frontend/src/config/__init__.py`, `PI4/Frontend/src/config/glossary.py`, `PI4/Frontend/src/config/i18n.py`, `PI4/Frontend/src/controllers/auth.py`, `PI4/Frontend/src/models/formatting/__init__.py`.

**Arquivos que utilizam este módulo:** `PI4/Backend/tests/test_performance_regressions.py`, `PI4/Frontend/app.py`, `PI4/Frontend/src/components/sidebar_filters.py`, `PI4/Frontend/src/controllers/__init__.py`.

**Outras dependências declaradas:** `pandas`, `pathlib`, `streamlit`.

**Responsabilidades internas:**

- `render_language_selector`: Seletor no topo da sidebar; persiste em ``st.session_state['lang']``.

**Operações concretas realizadas neste arquivo:**

- Recebe uma seleção do usuário na interface.
- Solicita uma nova execução da página Streamlit para refletir mudanças de estado.

<a id="arquivo-163"></a>

#### `PI4/Frontend/src/controllers/stability.py`

**Para que serve:** Trocas rapidas de visao sem derrubar o websocket do Streamlit.

**Como funciona:** Abandona a resposta a meio para a troca de ecran nao competir com a IA. True no primeiro rerun depois de mudar persona/filtro — so mostra um placeholder.

**Como se relaciona com o restante:** Controladores Streamlit: coordenam estado de sessão, filtros, autenticação, navegação e composição de componentes.

**Arquivos do projeto que utiliza:** `PI4/Backend/diag.py`, `PI4/Frontend/src/controllers/modals.py`.

**Arquivos que utilizam este módulo:** `PI4/Frontend/app.py`, `PI4/Frontend/src/views/ai_assistant/panel.py`.

**Outras dependências declaradas:** `streamlit`.

**Responsabilidades internas:**

- `cancelar_assistente_em_curso`: Abandona a resposta a meio para a troca de ecran nao competir com a IA.
- `preparar_troca_vista`: True no primeiro rerun depois de mudar persona/filtro — so mostra um placeholder.

<a id="arquivo-164"></a>

#### `PI4/Frontend/src/controllers/test_sandbox.py`

**Para que serve:** Sandbox temporario da persona Teste.

**Como funciona:** Configura os valores e as integrações compartilhadas indicados por este módulo.

**Como se relaciona com o restante:** Controladores Streamlit: coordenam estado de sessão, filtros, autenticação, navegação e composição de componentes.

**Arquivos do projeto que utiliza:** `PI4/Frontend/src/config/i18n.py`, `PI4/Frontend/src/controllers/bootstrap.py`, `PI4/Frontend/src/models/financial_metrics/__init__.py`, `PI4/Frontend/src/views/__init__.py`, `PI4/Frontend/src/views/persona_tabs/__init__.py`.

**Arquivos que utilizam este módulo:** `PI4/Frontend/src/controllers/navigation.py`.

**Outras dependências declaradas:** `streamlit`.

**Operações concretas realizadas neste arquivo:**

- Recebe uma seleção do usuário na interface.
- Solicita uma nova execução da página Streamlit para refletir mudanças de estado.

<a id="pasta-029"></a>

### Pasta `PI4/Frontend/src/controllers/charts/`

Controladores Streamlit: coordenam estado de sessão, filtros, autenticação, navegação e composição de componentes.

| Arquivo | O que faz |
|---|---|
| [__init__.py](#arquivo-140) | Compatibilidade publica dos componentes de grafico. |
| [histograms.py](#arquivo-141) | Graficos de histograma usados no dashboard. |
| [risk_band.py](#arquivo-142) | Graficos de envelope/faixa de risco. |
| [time_series.py](#arquivo-143) | Helpers de series temporais para Plotly. |

<a id="arquivo-140"></a>

#### `PI4/Frontend/src/controllers/charts/__init__.py`

**Para que serve:** Compatibilidade publica dos componentes de grafico.

**Como funciona:** Reúne constantes, imports e exports para os consumidores do pacote.

**Como se relaciona com o restante:** Controladores Streamlit: coordenam estado de sessão, filtros, autenticação, navegação e composição de componentes.

**Arquivos do projeto que utiliza:** `PI4/Frontend/src/controllers/charts/histograms.py`, `PI4/Frontend/src/controllers/charts/risk_band.py`, `PI4/Frontend/src/controllers/charts/time_series.py`.

**Arquivos que utilizam este módulo:** `PI4/Frontend/src/controllers/__init__.py`, `PI4/Frontend/src/views/capital_giro.py`, `PI4/Frontend/src/views/comparar.py`, `PI4/Frontend/src/views/distribuicao.py`, `PI4/Frontend/src/views/faixa_risco.py`, `PI4/Frontend/src/views/prazos_ciclo.py`.

<a id="arquivo-141"></a>

#### `PI4/Frontend/src/controllers/charts/histograms.py`

**Para que serve:** Graficos de histograma usados no dashboard.

**Como funciona:** Configura os valores e as integrações compartilhadas indicados por este módulo.

**Como se relaciona com o restante:** Controladores Streamlit: coordenam estado de sessão, filtros, autenticação, navegação e composição de componentes.

**Arquivos do projeto que utiliza:** `PI4/Frontend/src/config/__init__.py`, `PI4/Frontend/src/config/i18n.py`, `PI4/Frontend/src/models/formatting/__init__.py`.

**Arquivos que utilizam este módulo:** `PI4/Frontend/src/controllers/charts/__init__.py`.

**Outras dependências declaradas:** `numpy`, `pandas`, `plotly`.

<a id="arquivo-142"></a>

#### `PI4/Frontend/src/controllers/charts/risk_band.py`

**Para que serve:** Graficos de envelope/faixa de risco.

**Como funciona:** Configura os valores e as integrações compartilhadas indicados por este módulo.

**Como se relaciona com o restante:** Controladores Streamlit: coordenam estado de sessão, filtros, autenticação, navegação e composição de componentes.

**Arquivos do projeto que utiliza:** `PI4/Frontend/src/config/__init__.py`, `PI4/Frontend/src/config/i18n.py`, `PI4/Frontend/src/models/analytics/__init__.py`.

**Arquivos que utilizam este módulo:** `PI4/Frontend/src/controllers/charts/__init__.py`.

**Outras dependências declaradas:** `pandas`, `plotly`.

<a id="arquivo-143"></a>

#### `PI4/Frontend/src/controllers/charts/time_series.py`

**Para que serve:** Helpers de series temporais para Plotly.

**Como funciona:** Normaliza ano_num (Int64/NA) e remove linhas invalidas antes do Plotly.

**Como se relaciona com o restante:** Controladores Streamlit: coordenam estado de sessão, filtros, autenticação, navegação e composição de componentes.

**Arquivos do projeto que utiliza:** `PI4/Frontend/src/config/__init__.py`, `PI4/Frontend/src/config/i18n.py`, `PI4/Frontend/src/models/formatting/__init__.py`.

**Arquivos que utilizam este módulo:** `PI4/Frontend/src/controllers/charts/__init__.py`.

**Outras dependências declaradas:** `pandas`, `plotly`.

**Responsabilidades internas:**

- `serie_temporal_plotavel`: Normaliza ano_num (Int64/NA) e remove linhas invalidas antes do Plotly.

**Operações concretas realizadas neste arquivo:**

- Converte entradas para números e trata conversões inválidas conforme as opções utilizadas.

<a id="pasta-030"></a>

### Pasta `PI4/Frontend/src/controllers/kpis/`

Controladores Streamlit: coordenam estado de sessão, filtros, autenticação, navegação e composição de componentes.

| Arquivo | O que faz |
|---|---|
| [__init__.py](#arquivo-147) | Compatibilidade publica dos KPIs e cards do dashboard. |
| [ceo.py](#arquivo-148) | KPIs da visao do CEO. |
| [concession.py](#arquivo-149) | KPIs da visao do poder concedente. |
| [constants.py](#arquivo-150) | Constantes usadas nos KPIs executivos. |
| [helpers.py](#arquivo-151) | Helpers de leitura e calculo para KPIs. |
| [personas.py](#arquivo-152) | Roteador dos KPIs por persona. |
| [rendering.py](#arquivo-153) | Renderizacao visual dos cards de KPI. |
| [shareholders.py](#arquivo-154) | KPIs da visao de acionistas. |

<a id="arquivo-147"></a>

#### `PI4/Frontend/src/controllers/kpis/__init__.py`

**Para que serve:** Compatibilidade publica dos KPIs e cards do dashboard.

**Como funciona:** Reúne constantes, imports e exports para os consumidores do pacote.

**Como se relaciona com o restante:** Controladores Streamlit: coordenam estado de sessão, filtros, autenticação, navegação e composição de componentes.

**Arquivos do projeto que utiliza:** `PI4/Frontend/src/controllers/kpis/ceo.py`, `PI4/Frontend/src/controllers/kpis/concession.py`, `PI4/Frontend/src/controllers/kpis/constants.py`, `PI4/Frontend/src/controllers/kpis/helpers.py`, `PI4/Frontend/src/controllers/kpis/personas.py`, `PI4/Frontend/src/controllers/kpis/rendering.py`, `PI4/Frontend/src/controllers/kpis/shareholders.py`.

**Arquivos que utilizam este módulo:** `PI4/Frontend/src/controllers/__init__.py`, `PI4/Frontend/src/controllers/bootstrap.py`, `PI4/Frontend/src/views/ai_assistant/context.py`, `PI4/Frontend/src/views/comparar.py`, `PI4/Frontend/src/views/distribuicao.py`, `PI4/Frontend/src/views/faixa_risco.py`, `PI4/Frontend/src/views/mapeamento_risco.py`, `PI4/Frontend/src/views/prazos_ciclo.py`.

<a id="arquivo-148"></a>

#### `PI4/Frontend/src/controllers/kpis/ceo.py`

**Para que serve:** KPIs da visao do CEO.

**Como funciona:** Configura os valores e as integrações compartilhadas indicados por este módulo.

**Como se relaciona com o restante:** Controladores Streamlit: coordenam estado de sessão, filtros, autenticação, navegação e composição de componentes.

**Arquivos do projeto que utiliza:** `PI4/Backend/metrics/__init__.py`, `PI4/Backend/metrics/column_resolver.py`, `PI4/Backend/metrics/financial_kpis.py`, `PI4/Frontend/src/config/i18n.py`, `PI4/Frontend/src/controllers/kpis/constants.py`, `PI4/Frontend/src/controllers/kpis/helpers.py`, `PI4/Frontend/src/models/formatting/__init__.py`.

**Arquivos que utilizam este módulo:** `PI4/Frontend/src/controllers/kpis/__init__.py`, `PI4/Frontend/src/controllers/kpis/personas.py`.

**Outras dependências declaradas:** `pandas`.

**Operações concretas realizadas neste arquivo:**

- Converte entradas para números e trata conversões inválidas conforme as opções utilizadas.

<a id="arquivo-149"></a>

#### `PI4/Frontend/src/controllers/kpis/concession.py`

**Para que serve:** KPIs da visao do poder concedente.

**Como funciona:** Configura os valores e as integrações compartilhadas indicados por este módulo.

**Como se relaciona com o restante:** Controladores Streamlit: coordenam estado de sessão, filtros, autenticação, navegação e composição de componentes.

**Arquivos do projeto que utiliza:** `PI4/Frontend/src/config/i18n.py`, `PI4/Frontend/src/controllers/kpis/constants.py`, `PI4/Frontend/src/controllers/kpis/helpers.py`, `PI4/Frontend/src/models/formatting/__init__.py`.

**Arquivos que utilizam este módulo:** `PI4/Frontend/src/controllers/kpis/__init__.py`, `PI4/Frontend/src/controllers/kpis/personas.py`.

**Outras dependências declaradas:** `pandas`.

<a id="arquivo-150"></a>

#### `PI4/Frontend/src/controllers/kpis/constants.py`

**Para que serve:** Constantes usadas nos KPIs executivos.

**Como funciona:** Configura os valores e as integrações compartilhadas indicados por este módulo.

**Como se relaciona com o restante:** Controladores Streamlit: coordenam estado de sessão, filtros, autenticação, navegação e composição de componentes.

**Arquivos que utilizam este módulo:** `PI4/Frontend/src/controllers/kpis/__init__.py`, `PI4/Frontend/src/controllers/kpis/ceo.py`, `PI4/Frontend/src/controllers/kpis/concession.py`, `PI4/Frontend/src/controllers/kpis/personas.py`, `PI4/Frontend/src/controllers/kpis/rendering.py`, `PI4/Frontend/src/controllers/kpis/shareholders.py`, `PI4/Frontend/src/views/ai_assistant/context.py`.

**Outras dependências declaradas:** `typing`.

<a id="arquivo-151"></a>

#### `PI4/Frontend/src/controllers/kpis/helpers.py`

**Para que serve:** Helpers de leitura e calculo para KPIs.

**Como funciona:** Configura os valores e as integrações compartilhadas indicados por este módulo.

**Como se relaciona com o restante:** Controladores Streamlit: coordenam estado de sessão, filtros, autenticação, navegação e composição de componentes.

**Arquivos do projeto que utiliza:** `PI4/Frontend/src/models/formatting/__init__.py`.

**Arquivos que utilizam este módulo:** `PI4/Frontend/src/controllers/kpis/__init__.py`, `PI4/Frontend/src/controllers/kpis/ceo.py`, `PI4/Frontend/src/controllers/kpis/concession.py`, `PI4/Frontend/src/controllers/kpis/shareholders.py`, `PI4/Frontend/src/views/ai_assistant/context.py`.

**Outras dependências declaradas:** `pandas`.

**Operações concretas realizadas neste arquivo:**

- Converte entradas para números e trata conversões inválidas conforme as opções utilizadas.

<a id="arquivo-152"></a>

#### `PI4/Frontend/src/controllers/kpis/personas.py`

**Para que serve:** Roteador dos KPIs por persona.

**Como funciona:** Configura os valores e as integrações compartilhadas indicados por este módulo.

**Como se relaciona com o restante:** Controladores Streamlit: coordenam estado de sessão, filtros, autenticação, navegação e composição de componentes.

**Arquivos do projeto que utiliza:** `PI4/Frontend/src/config/glossary.py`, `PI4/Frontend/src/config/i18n.py`, `PI4/Frontend/src/controllers/kpis/ceo.py`, `PI4/Frontend/src/controllers/kpis/concession.py`, `PI4/Frontend/src/controllers/kpis/constants.py`, `PI4/Frontend/src/controllers/kpis/shareholders.py`, `PI4/Frontend/src/models/formatting/__init__.py`.

**Arquivos que utilizam este módulo:** `PI4/Frontend/src/controllers/kpis/__init__.py`.

**Outras dependências declaradas:** `pandas`.

<a id="arquivo-153"></a>

#### `PI4/Frontend/src/controllers/kpis/rendering.py`

**Para que serve:** Renderizacao visual dos cards de KPI.

**Como funciona:** Uma metrica nativa + CSS de contraste; tooltip unico via ``help``. Linha de KPIs com ``st.metric`` e contraste forcado no Dark Mode.

**Como se relaciona com o restante:** Controladores Streamlit: coordenam estado de sessão, filtros, autenticação, navegação e composição de componentes.

**Arquivos do projeto que utiliza:** `PI4/Frontend/src/config/__init__.py`, `PI4/Frontend/src/config/i18n.py`, `PI4/Frontend/src/controllers/kpis/constants.py`.

**Arquivos que utilizam este módulo:** `PI4/Frontend/src/components/kpi_cards_component.py`, `PI4/Frontend/src/controllers/kpis/__init__.py`.

**Outras dependências declaradas:** `html`, `streamlit`.

**Responsabilidades internas:**

- `render_metric_card`: Uma metrica nativa + CSS de contraste; tooltip unico via ``help``.
- `render_kpi_row`: Linha de KPIs com ``st.metric`` e contraste forcado no Dark Mode.

<a id="arquivo-154"></a>

#### `PI4/Frontend/src/controllers/kpis/shareholders.py`

**Para que serve:** KPIs da visao de acionistas.

**Como funciona:** Configura os valores e as integrações compartilhadas indicados por este módulo.

**Como se relaciona com o restante:** Controladores Streamlit: coordenam estado de sessão, filtros, autenticação, navegação e composição de componentes.

**Arquivos do projeto que utiliza:** `PI4/Frontend/src/config/i18n.py`, `PI4/Frontend/src/controllers/kpis/constants.py`, `PI4/Frontend/src/controllers/kpis/helpers.py`, `PI4/Frontend/src/models/formatting/__init__.py`.

**Arquivos que utilizam este módulo:** `PI4/Frontend/src/controllers/kpis/__init__.py`, `PI4/Frontend/src/controllers/kpis/personas.py`.

**Outras dependências declaradas:** `pandas`.

<a id="pasta-031"></a>

### Pasta `PI4/Frontend/src/models/`

Dados e apresentação de valores: API HTTP, compatibilidade com regras do backend, séries financeiras e formatação.

| Arquivo | O que faz |
|---|---|
| [__init__.py](#arquivo-165) | Pacote de dados CTI — imports sob demanda (evita ciclo na inicialização). |
| [api_client.py](#arquivo-169) | Cliente HTTP do Frontend. Um pedido por acao do utilizador, sem retentativas. |
| [classifiers.py](#arquivo-170) | Compatibilidade: classificacao de cenarios agora vive no Backend. |
| [loaders.py](#arquivo-184) | Compatibilidade: carregamento de dados agora vive no Backend. |

<a id="arquivo-165"></a>

#### `PI4/Frontend/src/models/__init__.py`

**Para que serve:** Pacote de dados CTI — imports sob demanda (evita ciclo na inicialização).

**Como funciona:** Reúne constantes, imports e exports para os consumidores do pacote.

**Como se relaciona com o restante:** Dados e apresentação de valores: API HTTP, compatibilidade com regras do backend, séries financeiras e formatação.

**Arquivos do projeto que utiliza:** `PI4/Frontend/src/models/analytics/__init__.py`, `PI4/Frontend/src/models/classifiers.py`, `PI4/Frontend/src/models/formatting/__init__.py`, `PI4/Frontend/src/models/loaders.py`.

**Outras dependências declaradas:** `__future__`.

<a id="arquivo-169"></a>

#### `PI4/Frontend/src/models/api_client.py`

**Para que serve:** Cliente HTTP do Frontend. Um pedido por acao do utilizador, sem retentativas.

**Como funciona:** Recebe um arquivo binário da API e propaga o diagnóstico de falha ao painel.

**Como se relaciona com o restante:** Dados e apresentação de valores: API HTTP, compatibilidade com regras do backend, séries financeiras e formatação.

**Arquivos do projeto que utiliza:** `PI4/Frontend/src/config/__init__.py`.

**Arquivos que utilizam este módulo:** `PI4/Frontend/src/controllers/auth.py`, `PI4/Frontend/src/controllers/ops_menu.py`, `PI4/Frontend/src/views/persona_tabs/admin_users.py`, `PI4/Frontend/src/views/report.py`.

**Outras dependências declaradas:** `json`, `logging`, `sys`, `urllib`.

**Responsabilidades internas:**

- `post_pdf`: Recebe um arquivo binário da API e propaga o diagnóstico de falha ao painel.

<a id="arquivo-170"></a>

#### `PI4/Frontend/src/models/classifiers.py`

**Para que serve:** Compatibilidade: classificacao de cenarios agora vive no Backend.

**Como funciona:** Configura os valores e as integrações compartilhadas indicados por este módulo.

**Como se relaciona com o restante:** Dados e apresentação de valores: API HTTP, compatibilidade com regras do backend, séries financeiras e formatação.

**Arquivos do projeto que utiliza:** `PI4/Backend/metrics/financial_kpis.py`.

**Arquivos que utilizam este módulo:** `PI4/Frontend/src/models/__init__.py`.

**Outras dependências declaradas:** `pathlib`, `sys`.

<a id="arquivo-184"></a>

#### `PI4/Frontend/src/models/loaders.py`

**Para que serve:** Compatibilidade: carregamento de dados agora vive no Backend.

**Como funciona:** Configura os valores e as integrações compartilhadas indicados por este módulo.

**Como se relaciona com o restante:** Dados e apresentação de valores: API HTTP, compatibilidade com regras do backend, séries financeiras e formatação.

**Arquivos do projeto que utiliza:** `PI4/Backend/data_loader/__init__.py`.

**Arquivos que utilizam este módulo:** `PI4/Frontend/src/controllers/data_input.py`, `PI4/Frontend/src/models/__init__.py`.

**Outras dependências declaradas:** `pathlib`, `sys`.

<a id="pasta-032"></a>

### Pasta `PI4/Frontend/src/models/analytics/`

Dados e apresentação de valores: API HTTP, compatibilidade com regras do backend, séries financeiras e formatação.

| Arquivo | O que faz |
|---|---|
| [__init__.py](#arquivo-166) | Compatibilidade publica do pipeline analitico. |
| [indicators.py](#arquivo-167) | Compatibilidade: indicadores financeiros agora vivem no Backend. |
| [summaries.py](#arquivo-168) | Resumos estatisticos e selecao de cenarios. |

<a id="arquivo-166"></a>

#### `PI4/Frontend/src/models/analytics/__init__.py`

**Para que serve:** Compatibilidade publica do pipeline analitico.

**Como funciona:** Reúne constantes, imports e exports para os consumidores do pacote.

**Como se relaciona com o restante:** Dados e apresentação de valores: API HTTP, compatibilidade com regras do backend, séries financeiras e formatação.

**Arquivos do projeto que utiliza:** `PI4/Frontend/src/models/analytics/indicators.py`, `PI4/Frontend/src/models/analytics/summaries.py`.

**Arquivos que utilizam este módulo:** `PI4/Frontend/src/controllers/charts/risk_band.py`, `PI4/Frontend/src/models/__init__.py`, `PI4/Frontend/src/views/faixa_risco.py`, `PI4/Frontend/src/views/mapeamento_risco.py`.

<a id="arquivo-167"></a>

#### `PI4/Frontend/src/models/analytics/indicators.py`

**Para que serve:** Compatibilidade: indicadores financeiros agora vivem no Backend.

**Como funciona:** Configura os valores e as integrações compartilhadas indicados por este módulo.

**Como se relaciona com o restante:** Dados e apresentação de valores: API HTTP, compatibilidade com regras do backend, séries financeiras e formatação.

**Arquivos do projeto que utiliza:** `PI4/Backend/metrics/financial_kpis.py`.

**Arquivos que utilizam este módulo:** `PI4/Frontend/src/models/analytics/__init__.py`.

**Outras dependências declaradas:** `pathlib`, `sys`.

<a id="arquivo-168"></a>

#### `PI4/Frontend/src/models/analytics/summaries.py`

**Para que serve:** Resumos estatisticos e selecao de cenarios.

**Como funciona:** Resumo descritivo alinhado a EDA do analise.ipynb.

**Como se relaciona com o restante:** Dados e apresentação de valores: API HTTP, compatibilidade com regras do backend, séries financeiras e formatação.

**Arquivos do projeto que utiliza:** `PI4/Backend/metrics/__init__.py`.

**Arquivos que utilizam este módulo:** `PI4/Frontend/src/models/analytics/__init__.py`.

**Outras dependências declaradas:** `pandas`, `pathlib`, `sys`.

**Responsabilidades internas:**

- `resumo_estatistico`: Resumo descritivo alinhado a EDA do analise.ipynb.

**Operações concretas realizadas neste arquivo:**

- Agrupa registros para calcular resultados por conta, ano, cenário ou outra chave indicada no módulo.
- Converte entradas para números e trata conversões inválidas conforme as opções utilizadas.
- Calcula percentis usados nas faixas, comparações ou classificações.

<a id="pasta-033"></a>

### Pasta `PI4/Frontend/src/models/financial_metrics/`

Dados e apresentação de valores: API HTTP, compatibilidade com regras do backend, séries financeiras e formatação.

| Arquivo | O que faz |
|---|---|
| [__init__.py](#arquivo-171) | Compatibilidade publica das metricas financeiras dinamicas. |
| [catalog.py](#arquivo-172) | Catalogo de metricas financeiras disponiveis no sandbox. |
| [labels.py](#arquivo-173) | Rótulos traduzidos das métricas financeiras do sandbox. |
| [series.py](#arquivo-174) | Calculo de series temporais para metricas financeiras dinamicas. |
| [types.py](#arquivo-175) | Tipos compartilhados das metricas financeiras. |
| [utils.py](#arquivo-176) | Utilitarios numericos das metricas financeiras. |

<a id="arquivo-171"></a>

#### `PI4/Frontend/src/models/financial_metrics/__init__.py`

**Para que serve:** Compatibilidade publica das metricas financeiras dinamicas.

**Como funciona:** Reúne constantes, imports e exports para os consumidores do pacote.

**Como se relaciona com o restante:** Dados e apresentação de valores: API HTTP, compatibilidade com regras do backend, séries financeiras e formatação.

**Arquivos do projeto que utiliza:** `PI4/Frontend/src/models/financial_metrics/catalog.py`, `PI4/Frontend/src/models/financial_metrics/labels.py`, `PI4/Frontend/src/models/financial_metrics/series.py`, `PI4/Frontend/src/models/financial_metrics/types.py`, `PI4/Frontend/src/models/financial_metrics/utils.py`.

**Arquivos que utilizam este módulo:** `PI4/Frontend/src/controllers/custom_analysis.py`, `PI4/Frontend/src/controllers/test_sandbox.py`, `PI4/Frontend/src/views/persona_tabs/custom_analysis.py`.

<a id="arquivo-172"></a>

#### `PI4/Frontend/src/models/financial_metrics/catalog.py`

**Para que serve:** Catalogo de metricas financeiras disponiveis no sandbox.

**Como funciona:** Configura os valores e as integrações compartilhadas indicados por este módulo.

**Como se relaciona com o restante:** Dados e apresentação de valores: API HTTP, compatibilidade com regras do backend, séries financeiras e formatação.

**Arquivos do projeto que utiliza:** `PI4/Frontend/src/models/financial_metrics/types.py`, `PI4/Frontend/src/models/financial_metrics/utils.py`.

**Arquivos que utilizam este módulo:** `PI4/Frontend/src/models/financial_metrics/__init__.py`, `PI4/Frontend/src/models/financial_metrics/series.py`.

**Outras dependências declaradas:** `__future__`.

<a id="arquivo-173"></a>

#### `PI4/Frontend/src/models/financial_metrics/labels.py`

**Para que serve:** Rótulos traduzidos das métricas financeiras do sandbox.

**Como funciona:** Configura os valores e as integrações compartilhadas indicados por este módulo.

**Como se relaciona com o restante:** Dados e apresentação de valores: API HTTP, compatibilidade com regras do backend, séries financeiras e formatação.

**Arquivos do projeto que utiliza:** `PI4/Frontend/src/config/i18n.py`.

**Arquivos que utilizam este módulo:** `PI4/Frontend/src/models/financial_metrics/__init__.py`.

**Outras dependências declaradas:** `__future__`.

<a id="arquivo-174"></a>

#### `PI4/Frontend/src/models/financial_metrics/series.py`

**Para que serve:** Calculo de series temporais para metricas financeiras dinamicas.

**Como funciona:** Configura os valores e as integrações compartilhadas indicados por este módulo.

**Como se relaciona com o restante:** Dados e apresentação de valores: API HTTP, compatibilidade com regras do backend, séries financeiras e formatação.

**Arquivos do projeto que utiliza:** `PI4/Frontend/src/models/financial_metrics/catalog.py`, `PI4/Frontend/src/models/financial_metrics/utils.py`, `PI4/Frontend/src/models/formatting/scenarios.py`.

**Arquivos que utilizam este módulo:** `PI4/Frontend/src/models/financial_metrics/__init__.py`.

**Outras dependências declaradas:** `pandas`.

**Operações concretas realizadas neste arquivo:**

- Agrupa registros para calcular resultados por conta, ano, cenário ou outra chave indicada no módulo.
- Converte entradas para números e trata conversões inválidas conforme as opções utilizadas.

<a id="arquivo-175"></a>

#### `PI4/Frontend/src/models/financial_metrics/types.py`

**Para que serve:** Tipos compartilhados das metricas financeiras.

**Como funciona:** Configura os valores e as integrações compartilhadas indicados por este módulo.

**Como se relaciona com o restante:** Dados e apresentação de valores: API HTTP, compatibilidade com regras do backend, séries financeiras e formatação.

**Arquivos que utilizam este módulo:** `PI4/Frontend/src/models/financial_metrics/__init__.py`, `PI4/Frontend/src/models/financial_metrics/catalog.py`.

**Outras dependências declaradas:** `collections`, `pandas`, `typing`.

<a id="arquivo-176"></a>

#### `PI4/Frontend/src/models/financial_metrics/utils.py`

**Para que serve:** Utilitarios numericos das metricas financeiras.

**Como funciona:** Configura os valores e as integrações compartilhadas indicados por este módulo.

**Como se relaciona com o restante:** Dados e apresentação de valores: API HTTP, compatibilidade com regras do backend, séries financeiras e formatação.

**Arquivos que utilizam este módulo:** `PI4/Frontend/src/models/financial_metrics/__init__.py`, `PI4/Frontend/src/models/financial_metrics/catalog.py`, `PI4/Frontend/src/models/financial_metrics/series.py`.

**Outras dependências declaradas:** `pandas`.

**Operações concretas realizadas neste arquivo:**

- Converte entradas para números e trata conversões inválidas conforme as opções utilizadas.
- Aplica os valores de substituição definidos para dados ausentes.

<a id="pasta-034"></a>

### Pasta `PI4/Frontend/src/models/formatting/`

Dados e apresentação de valores: API HTTP, compatibilidade com regras do backend, séries financeiras e formatação.

| Arquivo | O que faz |
|---|---|
| [__init__.py](#arquivo-177) | Compatibilidade para utilitarios de formatacao. |
| [base.py](#arquivo-178) | Primitivas compartilhadas de formatacao. |
| [comparisons.py](#arquivo-179) | Helpers de comparacao visual e defaults. |
| [numbers.py](#arquivo-180) | Formatadores numericos dependentes de idioma. |
| [scenarios.py](#arquivo-181) | Formatacao e ordenacao de cenarios. |
| [tables.py](#arquivo-182) | Renderizacao de tabelas nativas com formato numerico PT/EN. |
| [texts.py](#arquivo-183) | Textos explicativos para indicadores financeiros. |

<a id="arquivo-177"></a>

#### `PI4/Frontend/src/models/formatting/__init__.py`

**Para que serve:** Compatibilidade para utilitarios de formatacao.

**Como funciona:** Reúne constantes, imports e exports para os consumidores do pacote.

**Como se relaciona com o restante:** Dados e apresentação de valores: API HTTP, compatibilidade com regras do backend, séries financeiras e formatação.

**Arquivos do projeto que utiliza:** `PI4/Frontend/src/models/formatting/base.py`, `PI4/Frontend/src/models/formatting/comparisons.py`, `PI4/Frontend/src/models/formatting/numbers.py`, `PI4/Frontend/src/models/formatting/scenarios.py`, `PI4/Frontend/src/models/formatting/tables.py`, `PI4/Frontend/src/models/formatting/texts.py`.

**Arquivos que utilizam este módulo:** `PI4/Frontend/src/controllers/bootstrap.py`, `PI4/Frontend/src/controllers/charts/histograms.py`, `PI4/Frontend/src/controllers/charts/time_series.py`, `PI4/Frontend/src/controllers/headers.py`, `PI4/Frontend/src/controllers/kpis/ceo.py`, `PI4/Frontend/src/controllers/kpis/concession.py`, `PI4/Frontend/src/controllers/kpis/helpers.py`, `PI4/Frontend/src/controllers/kpis/personas.py`, `PI4/Frontend/src/controllers/kpis/shareholders.py`, `PI4/Frontend/src/controllers/sidebar.py`, `PI4/Frontend/src/models/__init__.py`, `PI4/Frontend/src/views/ai_assistant/context.py`, `PI4/Frontend/src/views/capital_giro.py`, `PI4/Frontend/src/views/como_ler.py`, `PI4/Frontend/src/views/comparar.py`, `PI4/Frontend/src/views/distribuicao.py`, `PI4/Frontend/src/views/faixa_risco.py`, `PI4/Frontend/src/views/mapeamento_risco.py`, `PI4/Frontend/src/views/persona_tabs/ceo.py`, `PI4/Frontend/src/views/persona_tabs/comparison_ceo_cfo.py`, `PI4/Frontend/src/views/persona_tabs/comparison_concession.py`, `PI4/Frontend/src/views/persona_tabs/comparison_helpers.py`, `PI4/Frontend/src/views/persona_tabs/comparison_shareholders.py`, `PI4/Frontend/src/views/persona_tabs/custom_analysis.py`, `PI4/Frontend/src/views/prazos_ciclo.py`, `PI4/Frontend/src/views/report.py`.

<a id="arquivo-178"></a>

#### `PI4/Frontend/src/models/formatting/base.py`

**Para que serve:** Primitivas compartilhadas de formatacao.

**Como funciona:** Configura os valores e as integrações compartilhadas indicados por este módulo.

**Como se relaciona com o restante:** Dados e apresentação de valores: API HTTP, compatibilidade com regras do backend, séries financeiras e formatação.

**Arquivos que utilizam este módulo:** `PI4/Frontend/src/models/formatting/__init__.py`, `PI4/Frontend/src/models/formatting/comparisons.py`, `PI4/Frontend/src/models/formatting/numbers.py`, `PI4/Frontend/src/models/formatting/texts.py`.

**Outras dependências declaradas:** `typing`.

<a id="arquivo-179"></a>

#### `PI4/Frontend/src/models/formatting/comparisons.py`

**Para que serve:** Helpers de comparacao visual e defaults.

**Como funciona:** Configura os valores e as integrações compartilhadas indicados por este módulo.

**Como se relaciona com o restante:** Dados e apresentação de valores: API HTTP, compatibilidade com regras do backend, séries financeiras e formatação.

**Arquivos do projeto que utiliza:** `PI4/Frontend/src/models/formatting/base.py`.

**Arquivos que utilizam este módulo:** `PI4/Frontend/src/models/formatting/__init__.py`.

**Outras dependências declaradas:** `__future__`.

<a id="arquivo-180"></a>

#### `PI4/Frontend/src/models/formatting/numbers.py`

**Para que serve:** Formatadores numericos dependentes de idioma.

**Como funciona:** Configura os valores e as integrações compartilhadas indicados por este módulo.

**Como se relaciona com o restante:** Dados e apresentação de valores: API HTTP, compatibilidade com regras do backend, séries financeiras e formatação.

**Arquivos do projeto que utiliza:** `PI4/Frontend/src/config/i18n.py`, `PI4/Frontend/src/models/formatting/base.py`.

**Arquivos que utilizam este módulo:** `PI4/Frontend/src/models/formatting/__init__.py`, `PI4/Frontend/src/models/formatting/texts.py`.

**Outras dependências declaradas:** `__future__`.

<a id="arquivo-181"></a>

#### `PI4/Frontend/src/models/formatting/scenarios.py`

**Para que serve:** Formatacao e ordenacao de cenarios.

**Como funciona:** True quando o filtro de cenário pede a consolidação de Monte Carlo. Extrai o numero do cenario de strings como ``Total Cen_00001``. Converte ``Total Cen_00001`` -> ``Cenario 00001`` / ``Scenario 00001``.

**Como se relaciona com o restante:** Dados e apresentação de valores: API HTTP, compatibilidade com regras do backend, séries financeiras e formatação.

**Arquivos do projeto que utiliza:** `PI4/Frontend/src/config/i18n.py`.

**Arquivos que utilizam este módulo:** `PI4/Frontend/src/models/financial_metrics/series.py`, `PI4/Frontend/src/models/formatting/__init__.py`, `PI4/Frontend/src/models/rag_engine/context.py`.

**Outras dependências declaradas:** `re`.

**Responsabilidades internas:**

- `is_all_scenarios`: True quando o filtro de cenário pede a consolidação de Monte Carlo.
- `cena_id`: Extrai o numero do cenario de strings como ``Total Cen_00001``.
- `cena_rotulo`: Converte ``Total Cen_00001`` -> ``Cenario 00001`` / ``Scenario 00001``.

<a id="arquivo-182"></a>

#### `PI4/Frontend/src/models/formatting/tables.py`

**Para que serve:** Renderizacao de tabelas nativas com formato numerico PT/EN.

**Como funciona:** Evita titulos markdown gigantes no chat e mantem paragrafos com espaco. Renderiza markdown e converte tabelas GFM em st.dataframe sem quebrar o layout.

**Como se relaciona com o restante:** Dados e apresentação de valores: API HTTP, compatibilidade com regras do backend, séries financeiras e formatação.

**Arquivos do projeto que utiliza:** `PI4/Frontend/src/config/i18n.py`.

**Arquivos que utilizam este módulo:** `PI4/Frontend/src/controllers/data_input.py`, `PI4/Frontend/src/controllers/headers.py`, `PI4/Frontend/src/models/formatting/__init__.py`, `PI4/Frontend/src/views/ai_assistant/panel.py`, `PI4/Frontend/src/views/persona_tabs/audit.py`, `PI4/Frontend/src/views/persona_tabs/ceo.py`, `PI4/Frontend/src/views/persona_tabs/concession.py`, `PI4/Frontend/src/views/persona_tabs/custom_analysis.py`, `PI4/Frontend/src/views/persona_tabs/shareholders.py`.

**Outras dependências declaradas:** `pandas`, `re`, `streamlit`.

**Responsabilidades internas:**

- `limpar_markdown_chat`: Evita titulos markdown gigantes no chat e mantem paragrafos com espaco.
- `render_markdown_with_tables`: Renderiza markdown e converte tabelas GFM em st.dataframe sem quebrar o layout.

**Operações concretas realizadas neste arquivo:**

- Converte entradas para números e trata conversões inválidas conforme as opções utilizadas.
- Apresenta uma tabela interativa na interface.

<a id="arquivo-183"></a>

#### `PI4/Frontend/src/models/formatting/texts.py`

**Para que serve:** Textos explicativos para indicadores financeiros.

**Como funciona:** Configura os valores e as integrações compartilhadas indicados por este módulo.

**Como se relaciona com o restante:** Dados e apresentação de valores: API HTTP, compatibilidade com regras do backend, séries financeiras e formatação.

**Arquivos do projeto que utiliza:** `PI4/Frontend/src/config/i18n.py`, `PI4/Frontend/src/models/formatting/base.py`, `PI4/Frontend/src/models/formatting/numbers.py`.

**Arquivos que utilizam este módulo:** `PI4/Frontend/src/models/formatting/__init__.py`.

**Outras dependências declaradas:** `__future__`.

<a id="pasta-035"></a>

### Pasta `PI4/Frontend/src/models/rag_engine/`

Motor conversacional: documentos, TF-IDF, índice FAISS, contexto financeiro, respostas extrativas/Gemini e restrições por perfil.

| Arquivo | O que faz |
|---|---|
| [__init__.py](#arquivo-185) | Compatibilidade publica do motor RAG. |
| [answers.py](#arquivo-186) | Respostas extrativas e integracao Gemini. |
| [config.py](#arquivo-187) | Configuracao e constantes do motor RAG. |
| [context.py](#arquivo-188) | Construcao do contexto do recorte em foco. |
| [documents.py](#arquivo-189) | Construcao dos documentos usados pelo RAG. |
| [embeddings.py](#arquivo-190) | Embeddings locais baseados em TF-IDF. |
| [engine.py](#arquivo-191) | Classe principal do motor RAG e retrieval. |
| [formatters.py](#arquivo-192) | Formatadores locais usados no contexto RAG. |
| [rbac.py](#arquivo-193) | Isolamento RBAC do Assistente CTI: prompt, retrieval e guardrail. |

<a id="arquivo-185"></a>

#### `PI4/Frontend/src/models/rag_engine/__init__.py`

**Para que serve:** Compatibilidade publica do motor RAG.

**Como funciona:** Reúne constantes, imports e exports para os consumidores do pacote.

**Como se relaciona com o restante:** Motor conversacional: documentos, TF-IDF, índice FAISS, contexto financeiro, respostas extrativas/Gemini e restrições por perfil.

**Arquivos do projeto que utiliza:** `PI4/Frontend/src/models/rag_engine/answers.py`, `PI4/Frontend/src/models/rag_engine/config.py`, `PI4/Frontend/src/models/rag_engine/context.py`, `PI4/Frontend/src/models/rag_engine/documents.py`, `PI4/Frontend/src/models/rag_engine/embeddings.py`, `PI4/Frontend/src/models/rag_engine/engine.py`, `PI4/Frontend/src/models/rag_engine/formatters.py`.

**Arquivos que utilizam este módulo:** `PI4/Backend/rag_engine.py`, `PI4/Frontend/src/views/ai_assistant/context.py`.

<a id="arquivo-186"></a>

#### `PI4/Frontend/src/models/rag_engine/answers.py`

**Para que serve:** Respostas extrativas e integracao Gemini.

**Como funciona:** Configura os valores e as integrações compartilhadas indicados por este módulo.

**Como se relaciona com o restante:** Motor conversacional: documentos, TF-IDF, índice FAISS, contexto financeiro, respostas extrativas/Gemini e restrições por perfil.

**Arquivos do projeto que utiliza:** `PI4/Backend/diag.py`, `PI4/Frontend/src/models/rag_engine/config.py`, `PI4/Frontend/src/models/rag_engine/rbac.py`.

**Arquivos que utilizam este módulo:** `PI4/Frontend/src/models/rag_engine/__init__.py`, `PI4/Frontend/src/models/rag_engine/engine.py`.

**Outras dependências declaradas:** `google`, `langchain_core`, `os`, `re`.

**Operações concretas realizadas neste arquivo:**

- Solicita a geração de uma resposta ao modelo de linguagem.

<a id="arquivo-187"></a>

#### `PI4/Frontend/src/models/rag_engine/config.py`

**Para que serve:** Configuracao e constantes do motor RAG.

**Como funciona:** Configura os valores e as integrações compartilhadas indicados por este módulo.

**Como se relaciona com o restante:** Motor conversacional: documentos, TF-IDF, índice FAISS, contexto financeiro, respostas extrativas/Gemini e restrições por perfil.

**Arquivos do projeto que utiliza:** `PI4/Frontend/src/config/__init__.py`.

**Arquivos que utilizam este módulo:** `PI4/Frontend/src/models/rag_engine/__init__.py`, `PI4/Frontend/src/models/rag_engine/answers.py`, `PI4/Frontend/src/models/rag_engine/documents.py`.

**Outras dependências declaradas:** `dotenv`, `re`.

<a id="arquivo-188"></a>

#### `PI4/Frontend/src/models/rag_engine/context.py`

**Para que serve:** Construcao do contexto do recorte em foco.

**Como funciona:** Texto de contexto do cenario/recorte em foco (NCG, tesouraria e riscos).

**Como se relaciona com o restante:** Motor conversacional: documentos, TF-IDF, índice FAISS, contexto financeiro, respostas extrativas/Gemini e restrições por perfil.

**Arquivos do projeto que utiliza:** `PI4/Frontend/src/models/formatting/scenarios.py`, `PI4/Frontend/src/models/rag_engine/formatters.py`.

**Arquivos que utilizam este módulo:** `PI4/Frontend/src/models/rag_engine/__init__.py`.

**Outras dependências declaradas:** `pandas`.

**Responsabilidades internas:**

- `build_focus_context`: Texto de contexto do cenario/recorte em foco (NCG, tesouraria e riscos).

<a id="arquivo-189"></a>

#### `PI4/Frontend/src/models/rag_engine/documents.py`

**Para que serve:** Construcao dos documentos usados pelo RAG.

**Como funciona:** Anotacoes de aula/reuniao ficam fora do indice. Usa a varredura recursiva de Backend/services; fallback local se o import falhar. Varre recursivamente Backend/documentos com glob **/*.md e **/*.pdf. Resume os arquivos tecnicos disponiveis para o indice RAG.

**Como se relaciona com o restante:** Motor conversacional: documentos, TF-IDF, índice FAISS, contexto financeiro, respostas extrativas/Gemini e restrições por perfil.

**Arquivos do projeto que utiliza:** `PI4/Backend/diag.py`, `PI4/Backend/services/rag_indexer.py`, `PI4/Frontend/src/config/__init__.py`, `PI4/Frontend/src/config/glossary.py`, `PI4/Frontend/src/models/rag_engine/config.py`, `PI4/Frontend/src/models/rag_engine/formatters.py`, `PI4/Frontend/src/models/rag_engine/rbac.py`.

**Arquivos que utilizam este módulo:** `PI4/Frontend/src/models/rag_engine/__init__.py`, `PI4/Frontend/src/models/rag_engine/engine.py`.

**Outras dependências declaradas:** `langchain_core`, `langchain_text_splitters`, `pandas`, `pathlib`, `pypdf`.

**Responsabilidades internas:**

- `parece_transcricao`: Anotacoes de aula/reuniao ficam fora do indice.
- `_candidatos_documentos`: Usa a varredura recursiva de Backend/services; fallback local se o import falhar.
- `iter_arquivos_doc`: Varre recursivamente Backend/documentos com glob **/*.md e **/*.pdf.
- `status_documentos`: Resume os arquivos tecnicos disponiveis para o indice RAG.

**Operações concretas realizadas neste arquivo:**

- Agrupa registros para calcular resultados por conta, ano, cenário ou outra chave indicada no módulo.
- Abre um PDF para extrair seu conteúdo.

<a id="arquivo-190"></a>

#### `PI4/Frontend/src/models/rag_engine/embeddings.py`

**Para que serve:** Embeddings locais baseados em TF-IDF.

**Como funciona:** Embeddings locais (TF-IDF) para o FAISS, sem depender de API para retrieval.

**Como se relaciona com o restante:** Motor conversacional: documentos, TF-IDF, índice FAISS, contexto financeiro, respostas extrativas/Gemini e restrições por perfil.

**Arquivos que utilizam este módulo:** `PI4/Frontend/src/models/rag_engine/__init__.py`, `PI4/Frontend/src/models/rag_engine/engine.py`.

**Outras dependências declaradas:** `langchain_core`, `numpy`, `sklearn`.

**Responsabilidades internas:**

- `TfidfEmbeddings`: Embeddings locais (TF-IDF) para o FAISS, sem depender de API para retrieval.

<a id="arquivo-191"></a>

#### `PI4/Frontend/src/models/rag_engine/engine.py`

**Para que serve:** Classe principal do motor RAG e retrieval.

**Como funciona:** Manual executivo e indicadores do CSV sobem na busca.

**Como se relaciona com o restante:** Motor conversacional: documentos, TF-IDF, índice FAISS, contexto financeiro, respostas extrativas/Gemini e restrições por perfil.

**Arquivos do projeto que utiliza:** `PI4/Backend/diag.py`, `PI4/Frontend/src/models/rag_engine/answers.py`, `PI4/Frontend/src/models/rag_engine/documents.py`, `PI4/Frontend/src/models/rag_engine/embeddings.py`, `PI4/Frontend/src/models/rag_engine/rbac.py`.

**Arquivos que utilizam este módulo:** `PI4/Frontend/src/models/rag_engine/__init__.py`, `PI4/Frontend/src/views/ai_assistant/panel.py`.

**Outras dependências declaradas:** `dataclasses`, `faiss`, `langchain_core`, `numpy`, `pandas`, `re`, `time`, `typing`, `unicodedata`.

**Responsabilidades internas:**

- `prioridade_fonte`: Manual executivo e indicadores do CSV sobem na busca.

<a id="arquivo-192"></a>

#### `PI4/Frontend/src/models/rag_engine/formatters.py`

**Para que serve:** Formatadores locais usados no contexto RAG.

**Como funciona:** Configura os valores e as integrações compartilhadas indicados por este módulo.

**Como se relaciona com o restante:** Motor conversacional: documentos, TF-IDF, índice FAISS, contexto financeiro, respostas extrativas/Gemini e restrições por perfil.

**Arquivos que utilizam este módulo:** `PI4/Frontend/src/models/rag_engine/__init__.py`, `PI4/Frontend/src/models/rag_engine/context.py`, `PI4/Frontend/src/models/rag_engine/documents.py`, `PI4/Frontend/src/views/ai_assistant/context.py`.

**Outras dependências declaradas:** `pandas`.

<a id="arquivo-193"></a>

#### `PI4/Frontend/src/models/rag_engine/rbac.py`

**Para que serve:** Isolamento RBAC do Assistente CTI: prompt, retrieval e guardrail.

**Como funciona:** Classifica a visibilidade do documento pela pasta/tag. Guardrail: se a resposta vazou termo bloqueado, substitui pela mensagem de acesso negado.

**Como se relaciona com o restante:** Motor conversacional: documentos, TF-IDF, índice FAISS, contexto financeiro, respostas extrativas/Gemini e restrições por perfil.

**Arquivos que utilizam este módulo:** `PI4/Frontend/src/models/rag_engine/answers.py`, `PI4/Frontend/src/models/rag_engine/documents.py`, `PI4/Frontend/src/models/rag_engine/engine.py`, `PI4/Frontend/src/views/ai_assistant/context.py`, `PI4/Frontend/src/views/ai_assistant/panel.py`.

**Outras dependências declaradas:** `re`, `typing`, `unicodedata`.

**Responsabilidades internas:**

- `visibility_for_source`: Classifica a visibilidade do documento pela pasta/tag.
- `sanitize_answer`: Guardrail: se a resposta vazou termo bloqueado, substitui pela mensagem de acesso negado.

<a id="pasta-036"></a>

### Pasta `PI4/Frontend/src/views/`

Views Streamlit e Plotly por tema/persona; leem contexto e estado, produzem tabelas, gráficos, diálogos e chat.

| Arquivo | O que faz |
|---|---|
| [__init__.py](#arquivo-194) | Views (abas) do painel CTI. |
| [capital_giro.py](#arquivo-198) | Aba Capital de giro. |
| [como_ler.py](#arquivo-199) | Aba Como ler estes números. |
| [comparar.py](#arquivo-200) | Aba Comparar cenários. |
| [distribuicao.py](#arquivo-201) | Aba Distribuição & Probabilidades. |
| [faixa_risco.py](#arquivo-202) | Aba Faixa de risco. |
| [mapeamento_risco.py](#arquivo-203) | Aba Mapeamento de Risco × Retorno. |
| [prazos_ciclo.py](#arquivo-218) | Aba Prazos e ciclo. |
| [report.py](#arquivo-219) | Modal do construtor modular de relatorios executivos. |

<a id="arquivo-194"></a>

#### `PI4/Frontend/src/views/__init__.py`

**Para que serve:** Views (abas) do painel CTI.

**Como funciona:** Reúne constantes, imports e exports para os consumidores do pacote.

**Como se relaciona com o restante:** Views Streamlit e Plotly por tema/persona; leem contexto e estado, produzem tabelas, gráficos, diálogos e chat.

**Arquivos do projeto que utiliza:** `PI4/Frontend/src/views/ai_assistant/__init__.py`, `PI4/Frontend/src/views/capital_giro.py`, `PI4/Frontend/src/views/como_ler.py`, `PI4/Frontend/src/views/comparar.py`, `PI4/Frontend/src/views/distribuicao.py`, `PI4/Frontend/src/views/faixa_risco.py`, `PI4/Frontend/src/views/mapeamento_risco.py`, `PI4/Frontend/src/views/persona_tabs/__init__.py`, `PI4/Frontend/src/views/prazos_ciclo.py`, `PI4/Frontend/src/views/report.py`.

**Arquivos que utilizam este módulo:** `PI4/Backend/tests/test_memorial_api.py`, `PI4/Frontend/src/controllers/navigation.py`, `PI4/Frontend/src/controllers/test_sandbox.py`.

<a id="arquivo-198"></a>

#### `PI4/Frontend/src/views/capital_giro.py`

**Para que serve:** Aba Capital de giro.

**Como funciona:** Configura os valores e as integrações compartilhadas indicados por este módulo.

**Como se relaciona com o restante:** Views Streamlit e Plotly por tema/persona; leem contexto e estado, produzem tabelas, gráficos, diálogos e chat.

**Arquivos do projeto que utiliza:** `PI4/Frontend/src/config/__init__.py`, `PI4/Frontend/src/config/i18n.py`, `PI4/Frontend/src/controllers/charts/__init__.py`, `PI4/Frontend/src/controllers/headers.py`, `PI4/Frontend/src/controllers/resilience.py`, `PI4/Frontend/src/models/formatting/__init__.py`.

**Arquivos que utilizam este módulo:** `PI4/Frontend/src/controllers/navigation.py`, `PI4/Frontend/src/views/__init__.py`.

**Outras dependências declaradas:** `pandas`, `plotly`, `streamlit`.

**Operações concretas realizadas neste arquivo:**

- Exibe gráficos Plotly no Streamlit.

<a id="arquivo-199"></a>

#### `PI4/Frontend/src/views/como_ler.py`

**Para que serve:** Aba Como ler estes números.

**Como funciona:** Configura os valores e as integrações compartilhadas indicados por este módulo.

**Como se relaciona com o restante:** Views Streamlit e Plotly por tema/persona; leem contexto e estado, produzem tabelas, gráficos, diálogos e chat.

**Arquivos do projeto que utiliza:** `PI4/Frontend/src/config/i18n.py`, `PI4/Frontend/src/controllers/resilience.py`, `PI4/Frontend/src/models/formatting/__init__.py`.

**Arquivos que utilizam este módulo:** `PI4/Frontend/src/controllers/navigation.py`, `PI4/Frontend/src/views/__init__.py`.

**Outras dependências declaradas:** `pandas`, `streamlit`.

<a id="arquivo-200"></a>

#### `PI4/Frontend/src/views/comparar.py`

**Para que serve:** Aba Comparar cenários.

**Como funciona:** Configura os valores e as integrações compartilhadas indicados por este módulo.

**Como se relaciona com o restante:** Views Streamlit e Plotly por tema/persona; leem contexto e estado, produzem tabelas, gráficos, diálogos e chat.

**Arquivos do projeto que utiliza:** `PI4/Frontend/src/config/__init__.py`, `PI4/Frontend/src/config/glossary.py`, `PI4/Frontend/src/config/i18n.py`, `PI4/Frontend/src/controllers/charts/__init__.py`, `PI4/Frontend/src/controllers/headers.py`, `PI4/Frontend/src/controllers/kpis/__init__.py`, `PI4/Frontend/src/controllers/resilience.py`, `PI4/Frontend/src/models/formatting/__init__.py`.

**Arquivos que utilizam este módulo:** `PI4/Frontend/src/controllers/navigation.py`, `PI4/Frontend/src/views/__init__.py`.

**Outras dependências declaradas:** `pandas`, `plotly`, `streamlit`.

**Operações concretas realizadas neste arquivo:**

- Agrupa registros para calcular resultados por conta, ano, cenário ou outra chave indicada no módulo.
- Exibe gráficos Plotly no Streamlit.
- Apresenta uma tabela interativa na interface.
- Recebe uma seleção do usuário na interface.

<a id="arquivo-201"></a>

#### `PI4/Frontend/src/views/distribuicao.py`

**Para que serve:** Aba Distribuição & Probabilidades.

**Como funciona:** Configura os valores e as integrações compartilhadas indicados por este módulo.

**Como se relaciona com o restante:** Views Streamlit e Plotly por tema/persona; leem contexto e estado, produzem tabelas, gráficos, diálogos e chat.

**Arquivos do projeto que utiliza:** `PI4/Frontend/src/config/__init__.py`, `PI4/Frontend/src/config/glossary.py`, `PI4/Frontend/src/config/i18n.py`, `PI4/Frontend/src/controllers/charts/__init__.py`, `PI4/Frontend/src/controllers/headers.py`, `PI4/Frontend/src/controllers/kpis/__init__.py`, `PI4/Frontend/src/controllers/resilience.py`, `PI4/Frontend/src/models/formatting/__init__.py`.

**Arquivos que utilizam este módulo:** `PI4/Frontend/src/controllers/navigation.py`, `PI4/Frontend/src/views/__init__.py`.

**Outras dependências declaradas:** `pandas`, `plotly`, `streamlit`.

**Operações concretas realizadas neste arquivo:**

- Calcula percentis usados nas faixas, comparações ou classificações.
- Exibe gráficos Plotly no Streamlit.

<a id="arquivo-202"></a>

#### `PI4/Frontend/src/views/faixa_risco.py`

**Para que serve:** Aba Faixa de risco.

**Como funciona:** Configura os valores e as integrações compartilhadas indicados por este módulo.

**Como se relaciona com o restante:** Views Streamlit e Plotly por tema/persona; leem contexto e estado, produzem tabelas, gráficos, diálogos e chat.

**Arquivos do projeto que utiliza:** `PI4/Frontend/src/config/__init__.py`, `PI4/Frontend/src/config/glossary.py`, `PI4/Frontend/src/config/i18n.py`, `PI4/Frontend/src/controllers/charts/__init__.py`, `PI4/Frontend/src/controllers/headers.py`, `PI4/Frontend/src/controllers/kpis/__init__.py`, `PI4/Frontend/src/controllers/resilience.py`, `PI4/Frontend/src/models/analytics/__init__.py`, `PI4/Frontend/src/models/formatting/__init__.py`.

**Arquivos que utilizam este módulo:** `PI4/Frontend/src/controllers/navigation.py`, `PI4/Frontend/src/views/__init__.py`.

**Outras dependências declaradas:** `pandas`, `streamlit`.

**Operações concretas realizadas neste arquivo:**

- Exibe gráficos Plotly no Streamlit.
- Recebe uma seleção do usuário na interface.

<a id="arquivo-203"></a>

#### `PI4/Frontend/src/views/mapeamento_risco.py`

**Para que serve:** Aba Mapeamento de Risco × Retorno.

**Como funciona:** Configura os valores e as integrações compartilhadas indicados por este módulo.

**Como se relaciona com o restante:** Views Streamlit e Plotly por tema/persona; leem contexto e estado, produzem tabelas, gráficos, diálogos e chat.

**Arquivos do projeto que utiliza:** `PI4/Frontend/src/config/__init__.py`, `PI4/Frontend/src/config/glossary.py`, `PI4/Frontend/src/config/i18n.py`, `PI4/Frontend/src/controllers/headers.py`, `PI4/Frontend/src/controllers/kpis/__init__.py`, `PI4/Frontend/src/controllers/resilience.py`, `PI4/Frontend/src/models/analytics/__init__.py`, `PI4/Frontend/src/models/formatting/__init__.py`.

**Arquivos que utilizam este módulo:** `PI4/Frontend/src/controllers/navigation.py`, `PI4/Frontend/src/views/__init__.py`.

**Outras dependências declaradas:** `pandas`, `plotly`, `streamlit`.

**Operações concretas realizadas neste arquivo:**

- Aplica os valores de substituição definidos para dados ausentes.
- Exibe gráficos Plotly no Streamlit.
- Recebe uma seleção do usuário na interface.
- Solicita uma nova execução da página Streamlit para refletir mudanças de estado.

<a id="arquivo-218"></a>

#### `PI4/Frontend/src/views/prazos_ciclo.py`

**Para que serve:** Aba Prazos e ciclo.

**Como funciona:** Configura os valores e as integrações compartilhadas indicados por este módulo.

**Como se relaciona com o restante:** Views Streamlit e Plotly por tema/persona; leem contexto e estado, produzem tabelas, gráficos, diálogos e chat.

**Arquivos do projeto que utiliza:** `PI4/Frontend/src/config/glossary.py`, `PI4/Frontend/src/config/i18n.py`, `PI4/Frontend/src/controllers/charts/__init__.py`, `PI4/Frontend/src/controllers/headers.py`, `PI4/Frontend/src/controllers/kpis/__init__.py`, `PI4/Frontend/src/controllers/resilience.py`, `PI4/Frontend/src/models/formatting/__init__.py`.

**Arquivos que utilizam este módulo:** `PI4/Frontend/src/controllers/navigation.py`, `PI4/Frontend/src/views/__init__.py`.

**Outras dependências declaradas:** `pandas`, `plotly`, `streamlit`.

**Operações concretas realizadas neste arquivo:**

- Exibe gráficos Plotly no Streamlit.

<a id="arquivo-219"></a>

#### `PI4/Frontend/src/views/report.py`

**Para que serve:** Modal do construtor modular de relatorios executivos.

**Como funciona:** Inicializa chaves estaveis sem apagar edicoes ja feitas pelo usuario. Rasteriza paginas do PDF em JPEG compacto para o modal. Gera o PDF fora do st.dialog para o websocket nao cair no meio do modal. Renderiza o report builder em modal estavel com formulario.

**Como se relaciona com o restante:** Views Streamlit e Plotly por tema/persona; leem contexto e estado, produzem tabelas, gráficos, diálogos e chat.

**Arquivos do projeto que utiliza:** `PI4/Backend/diag.py`, `PI4/Backend/services/custom_report_service.py`, `PI4/Backend/services/report_generator.py`, `PI4/Frontend/src/config/i18n.py`, `PI4/Frontend/src/controllers/bootstrap.py`, `PI4/Frontend/src/controllers/data_input.py`, `PI4/Frontend/src/controllers/modals.py`, `PI4/Frontend/src/models/api_client.py`, `PI4/Frontend/src/models/formatting/__init__.py`, `PI4/Frontend/src/views/persona_tabs/common.py`.

**Arquivos que utilizam este módulo:** `PI4/Backend/tests/test_memorial_api.py`, `PI4/Frontend/src/controllers/navigation.py`, `PI4/Frontend/src/views/__init__.py`.

**Outras dependências declaradas:** `datetime`, `fitz`, `html`, `io`, `os`, `pandas`, `pypdfium2`, `streamlit`, `time`, `traceback`.

**Responsabilidades internas:**

- `_ensure_report_defaults`: Inicializa chaves estaveis sem apagar edicoes ja feitas pelo usuario.
- `_pdf_para_imagens`: Rasteriza paginas do PDF em JPEG compacto para o modal.
- `flush_pending_pdf`: Gera o PDF fora do st.dialog para o websocket nao cair no meio do modal.
- `render_dialog`: Renderiza o report builder em modal estavel com formulario.

**Operações concretas realizadas neste arquivo:**

- Converte entradas para números e trata conversões inválidas conforme as opções utilizadas.
- Disponibiliza um arquivo para download na interface.
- Recebe uma seleção do usuário na interface.
- Solicita uma nova execução da página Streamlit para refletir mudanças de estado.

<a id="pasta-037"></a>

### Pasta `PI4/Frontend/src/views/ai_assistant/`

Views Streamlit e Plotly por tema/persona; leem contexto e estado, produzem tabelas, gráficos, diálogos e chat.

| Arquivo | O que faz |
|---|---|
| [__init__.py](#arquivo-195) | Compatibilidade publica da view do Assistente CTI. |
| [context.py](#arquivo-196) | Contexto e cache do Assistente CTI. |
| [panel.py](#arquivo-197) | Painel conversacional do Assistente CTI. |

<a id="arquivo-195"></a>

#### `PI4/Frontend/src/views/ai_assistant/__init__.py`

**Para que serve:** Compatibilidade publica da view do Assistente CTI.

**Como funciona:** Reúne constantes, imports e exports para os consumidores do pacote.

**Como se relaciona com o restante:** Views Streamlit e Plotly por tema/persona; leem contexto e estado, produzem tabelas, gráficos, diálogos e chat.

**Arquivos do projeto que utiliza:** `PI4/Frontend/src/views/ai_assistant/panel.py`.

**Arquivos que utilizam este módulo:** `PI4/Frontend/src/controllers/ai_sidebar_right.py`, `PI4/Frontend/src/views/__init__.py`.

**Outras dependências declaradas:** `typing`.

<a id="arquivo-196"></a>

#### `PI4/Frontend/src/views/ai_assistant/context.py`

**Para que serve:** Contexto e cache do Assistente CTI.

**Como funciona:** Resume a base ativa para o motor analitico nativo do Dashboard CTI.

**Como se relaciona com o restante:** Views Streamlit e Plotly por tema/persona; leem contexto e estado, produzem tabelas, gráficos, diálogos e chat.

**Arquivos do projeto que utiliza:** `PI4/Backend/diag.py`, `PI4/Backend/metrics/financial_kpis.py`, `PI4/Frontend/src/config/i18n.py`, `PI4/Frontend/src/controllers/kpis/__init__.py`, `PI4/Frontend/src/controllers/kpis/constants.py`, `PI4/Frontend/src/controllers/kpis/helpers.py`, `PI4/Frontend/src/models/formatting/__init__.py`, `PI4/Frontend/src/models/rag_engine/__init__.py`, `PI4/Frontend/src/models/rag_engine/formatters.py`, `PI4/Frontend/src/models/rag_engine/rbac.py`.

**Arquivos que utilizam este módulo:** `PI4/Frontend/src/views/ai_assistant/panel.py`.

**Outras dependências declaradas:** `pandas`, `streamlit`, `time`.

**Responsabilidades internas:**

- `contexto_dataset_ativo`: Resume a base ativa para o motor analitico nativo do Dashboard CTI.

**Operações concretas realizadas neste arquivo:**

- Agrupa registros para calcular resultados por conta, ano, cenário ou outra chave indicada no módulo.
- Converte entradas para números e trata conversões inválidas conforme as opções utilizadas.
- Aplica os valores de substituição definidos para dados ausentes.

<a id="arquivo-197"></a>

#### `PI4/Frontend/src/views/ai_assistant/panel.py`

**Para que serve:** Painel conversacional do Assistente CTI.

**Como funciona:** Sai do fragmento do chat para o dashboard aplicar persona + aba. Chama o RAG/LLM com contexto financeiro da base ativa. Painel do assistente. Nao recebe o df de 1M linhas — isso gerava 429 no fragmento.

**Como se relaciona com o restante:** Views Streamlit e Plotly por tema/persona; leem contexto e estado, produzem tabelas, gráficos, diálogos e chat.

**Arquivos do projeto que utiliza:** `PI4/Backend/diag.py`, `PI4/Frontend/src/config/i18n.py`, `PI4/Frontend/src/controllers/auth.py`, `PI4/Frontend/src/controllers/modals.py`, `PI4/Frontend/src/controllers/resilience.py`, `PI4/Frontend/src/controllers/stability.py`, `PI4/Frontend/src/models/formatting/tables.py`, `PI4/Frontend/src/models/rag_engine/engine.py`, `PI4/Frontend/src/models/rag_engine/rbac.py`, `PI4/Frontend/src/views/ai_assistant/context.py`.

**Arquivos que utilizam este módulo:** `PI4/Frontend/app.py`, `PI4/Frontend/src/views/ai_assistant/__init__.py`.

**Outras dependências declaradas:** `pandas`, `streamlit`, `time`.

**Responsabilidades internas:**

- `_rerun_app`: Sai do fragmento do chat para o dashboard aplicar persona + aba.
- `gerar_resposta_ia`: Chama o RAG/LLM com contexto financeiro da base ativa.
- `render_floating_chat`: Painel do assistente. Nao recebe o df de 1M linhas — isso gerava 429 no fragmento.

**Operações concretas realizadas neste arquivo:**

- Solicita uma nova execução da página Streamlit para refletir mudanças de estado.

<a id="pasta-038"></a>

### Pasta `PI4/Frontend/src/views/persona_tabs/`

Views Streamlit e Plotly por tema/persona; leem contexto e estado, produzem tabelas, gráficos, diálogos e chat.

| Arquivo | O que faz |
|---|---|
| [__init__.py](#arquivo-204) | Compatibilidade publica das sub-abas por persona. |
| [admin_users.py](#arquivo-205) | Painel exclusivo do Super Admin para gestao de usuarios. |
| [audit.py](#arquivo-206) | Aba CEO de auditoria de logs de acesso. |
| [ceo.py](#arquivo-207) | Sub-abas da persona CEO. |
| [common.py](#arquivo-208) | Compatibilidade visual para dados financeiros calculados no Backend. |
| [comparison.py](#arquivo-209) | Roteador do comparador de cenarios por persona. |
| [comparison_ceo_cfo.py](#arquivo-210) | Comparacoes das personas CEO e CFO. |
| [comparison_concession.py](#arquivo-211) | Comparacao da persona Poder Concedente. |
| [comparison_helpers.py](#arquivo-212) | Helpers visuais do comparador de cenarios. |
| [comparison_shareholders.py](#arquivo-213) | Comparacao da persona Acionistas. |
| [concession.py](#arquivo-214) | Sub-abas da persona Poder Concedente. |
| [custom_analysis.py](#arquivo-215) | Analises customizadas do sandbox. |
| [shareholders.py](#arquivo-216) | Sub-abas da persona Acionistas. |
| [styles.py](#arquivo-217) | Estilos compartilhados do comparador de cenarios. |

<a id="arquivo-204"></a>

#### `PI4/Frontend/src/views/persona_tabs/__init__.py`

**Para que serve:** Compatibilidade publica das sub-abas por persona.

**Como funciona:** Reúne constantes, imports e exports para os consumidores do pacote.

**Como se relaciona com o restante:** Views Streamlit e Plotly por tema/persona; leem contexto e estado, produzem tabelas, gráficos, diálogos e chat.

**Arquivos do projeto que utiliza:** `PI4/Frontend/src/views/persona_tabs/admin_users.py`, `PI4/Frontend/src/views/persona_tabs/audit.py`, `PI4/Frontend/src/views/persona_tabs/ceo.py`, `PI4/Frontend/src/views/persona_tabs/comparison.py`, `PI4/Frontend/src/views/persona_tabs/concession.py`, `PI4/Frontend/src/views/persona_tabs/custom_analysis.py`, `PI4/Frontend/src/views/persona_tabs/shareholders.py`.

**Arquivos que utilizam este módulo:** `PI4/Frontend/src/controllers/navigation.py`, `PI4/Frontend/src/controllers/test_sandbox.py`, `PI4/Frontend/src/views/__init__.py`.

<a id="arquivo-205"></a>

#### `PI4/Frontend/src/views/persona_tabs/admin_users.py`

**Para que serve:** Painel exclusivo do Super Admin para gestao de usuarios.

**Como funciona:** Configura os valores e as integrações compartilhadas indicados por este módulo.

**Como se relaciona com o restante:** Views Streamlit e Plotly por tema/persona; leem contexto e estado, produzem tabelas, gráficos, diálogos e chat.

**Arquivos do projeto que utiliza:** `PI4/Frontend/src/config/i18n.py`, `PI4/Frontend/src/controllers/auth.py`, `PI4/Frontend/src/models/api_client.py`.

**Arquivos que utilizam este módulo:** `PI4/Frontend/src/views/persona_tabs/__init__.py`.

**Outras dependências declaradas:** `pandas`, `streamlit`.

**Operações concretas realizadas neste arquivo:**

- Apresenta uma tabela interativa na interface.
- Recebe uma seleção do usuário na interface.

<a id="arquivo-206"></a>

#### `PI4/Frontend/src/views/persona_tabs/audit.py`

**Para que serve:** Aba CEO de auditoria de logs de acesso.

**Como funciona:** Configura os valores e as integrações compartilhadas indicados por este módulo.

**Como se relaciona com o restante:** Views Streamlit e Plotly por tema/persona; leem contexto e estado, produzem tabelas, gráficos, diálogos e chat.

**Arquivos do projeto que utiliza:** `PI4/Frontend/src/config/i18n.py`, `PI4/Frontend/src/controllers/auth.py`, `PI4/Frontend/src/models/formatting/tables.py`.

**Arquivos que utilizam este módulo:** `PI4/Frontend/src/views/persona_tabs/__init__.py`.

**Outras dependências declaradas:** `pandas`, `streamlit`.

<a id="arquivo-207"></a>

#### `PI4/Frontend/src/views/persona_tabs/ceo.py`

**Para que serve:** Sub-abas da persona CEO.

**Como funciona:** Renderiza cascata media da DRE e evolucao de receita/EBITDA. Renderiza margens e composicao operacional. Renderiza ponto de equilibrio com intersecao igual ao KPI consolidado. Renderiza LTV/CAC calculado no backend.

**Como se relaciona com o restante:** Views Streamlit e Plotly por tema/persona; leem contexto e estado, produzem tabelas, gráficos, diálogos e chat.

**Arquivos do projeto que utiliza:** `PI4/Backend/metrics/__init__.py`, `PI4/Backend/metrics/column_resolver.py`, `PI4/Frontend/src/config/__init__.py`, `PI4/Frontend/src/config/i18n.py`, `PI4/Frontend/src/models/formatting/__init__.py`, `PI4/Frontend/src/models/formatting/tables.py`, `PI4/Frontend/src/views/persona_tabs/common.py`.

**Arquivos que utilizam este módulo:** `PI4/Frontend/src/views/persona_tabs/__init__.py`.

**Outras dependências declaradas:** `pandas`, `plotly`, `streamlit`.

**Responsabilidades internas:**

- `render_ceo_visao_geral`: Renderiza cascata media da DRE e evolucao de receita/EBITDA.
- `render_ceo_dre_operacional`: Renderiza margens e composicao operacional.
- `render_ceo_break_even`: Renderiza ponto de equilibrio com intersecao igual ao KPI consolidado.
- `render_ceo_ltv_cac`: Renderiza LTV/CAC calculado no backend.

**Operações concretas realizadas neste arquivo:**

- Converte uma tabela larga em registros no formato longo.
- Converte entradas para números e trata conversões inválidas conforme as opções utilizadas.
- Exibe gráficos Plotly no Streamlit.

<a id="arquivo-208"></a>

#### `PI4/Frontend/src/views/persona_tabs/common.py`

**Para que serve:** Compatibilidade visual para dados financeiros calculados no Backend.

**Como funciona:** LTV/CAC a partir do Break-Even já cacheado — sem varrer 1M de linhas.

**Como se relaciona com o restante:** Views Streamlit e Plotly por tema/persona; leem contexto e estado, produzem tabelas, gráficos, diálogos e chat.

**Arquivos do projeto que utiliza:** `PI4/Backend/metrics/financial_kpis.py`, `PI4/Frontend/src/controllers/bootstrap.py`, `PI4/Frontend/src/controllers/data_input.py`.

**Arquivos que utilizam este módulo:** `PI4/Frontend/src/views/persona_tabs/ceo.py`, `PI4/Frontend/src/views/persona_tabs/comparison_ceo_cfo.py`, `PI4/Frontend/src/views/persona_tabs/comparison_concession.py`, `PI4/Frontend/src/views/persona_tabs/comparison_helpers.py`, `PI4/Frontend/src/views/persona_tabs/comparison_shareholders.py`, `PI4/Frontend/src/views/persona_tabs/concession.py`, `PI4/Frontend/src/views/persona_tabs/shareholders.py`, `PI4/Frontend/src/views/report.py`.

**Outras dependências declaradas:** `pandas`, `pathlib`, `streamlit`, `sys`.

**Responsabilidades internas:**

- `_ltv_from_be`: LTV/CAC a partir do Break-Even já cacheado — sem varrer 1M de linhas.

**Operações concretas realizadas neste arquivo:**

- Converte entradas para números e trata conversões inválidas conforme as opções utilizadas.
- Aplica os valores de substituição definidos para dados ausentes.

<a id="arquivo-209"></a>

#### `PI4/Frontend/src/views/persona_tabs/comparison.py`

**Para que serve:** Roteador do comparador de cenarios por persona.

**Como funciona:** Configura os valores e as integrações compartilhadas indicados por este módulo.

**Como se relaciona com o restante:** Views Streamlit e Plotly por tema/persona; leem contexto e estado, produzem tabelas, gráficos, diálogos e chat.

**Arquivos do projeto que utiliza:** `PI4/Frontend/src/config/i18n.py`, `PI4/Frontend/src/views/persona_tabs/comparison_ceo_cfo.py`, `PI4/Frontend/src/views/persona_tabs/comparison_concession.py`, `PI4/Frontend/src/views/persona_tabs/comparison_helpers.py`, `PI4/Frontend/src/views/persona_tabs/comparison_shareholders.py`.

**Arquivos que utilizam este módulo:** `PI4/Frontend/src/views/persona_tabs/__init__.py`.

**Outras dependências declaradas:** `pandas`, `streamlit`.

<a id="arquivo-210"></a>

#### `PI4/Frontend/src/views/persona_tabs/comparison_ceo_cfo.py`

**Para que serve:** Comparacoes das personas CEO e CFO.

**Como funciona:** Configura os valores e as integrações compartilhadas indicados por este módulo.

**Como se relaciona com o restante:** Views Streamlit e Plotly por tema/persona; leem contexto e estado, produzem tabelas, gráficos, diálogos e chat.

**Arquivos do projeto que utiliza:** `PI4/Backend/metrics/column_resolver.py`, `PI4/Frontend/src/config/__init__.py`, `PI4/Frontend/src/config/i18n.py`, `PI4/Frontend/src/models/formatting/__init__.py`, `PI4/Frontend/src/views/persona_tabs/common.py`, `PI4/Frontend/src/views/persona_tabs/comparison_helpers.py`, `PI4/Frontend/src/views/persona_tabs/styles.py`.

**Arquivos que utilizam este módulo:** `PI4/Frontend/src/views/persona_tabs/comparison.py`.

**Outras dependências declaradas:** `pandas`, `plotly`, `streamlit`.

**Operações concretas realizadas neste arquivo:**

- Combina tabelas usando suas chaves de relacionamento.
- Exibe gráficos Plotly no Streamlit.

<a id="arquivo-211"></a>

#### `PI4/Frontend/src/views/persona_tabs/comparison_concession.py`

**Para que serve:** Comparacao da persona Poder Concedente.

**Como funciona:** Configura os valores e as integrações compartilhadas indicados por este módulo.

**Como se relaciona com o restante:** Views Streamlit e Plotly por tema/persona; leem contexto e estado, produzem tabelas, gráficos, diálogos e chat.

**Arquivos do projeto que utiliza:** `PI4/Frontend/src/config/__init__.py`, `PI4/Frontend/src/config/i18n.py`, `PI4/Frontend/src/models/formatting/__init__.py`, `PI4/Frontend/src/views/persona_tabs/common.py`, `PI4/Frontend/src/views/persona_tabs/comparison_helpers.py`, `PI4/Frontend/src/views/persona_tabs/styles.py`.

**Arquivos que utilizam este módulo:** `PI4/Frontend/src/views/persona_tabs/comparison.py`.

**Outras dependências declaradas:** `pandas`, `plotly`, `streamlit`.

**Operações concretas realizadas neste arquivo:**

- Combina tabelas usando suas chaves de relacionamento.
- Aplica os valores de substituição definidos para dados ausentes.
- Exibe gráficos Plotly no Streamlit.

<a id="arquivo-212"></a>

#### `PI4/Frontend/src/views/persona_tabs/comparison_helpers.py`

**Para que serve:** Helpers visuais do comparador de cenarios.

**Como funciona:** Configura os valores e as integrações compartilhadas indicados por este módulo.

**Como se relaciona com o restante:** Views Streamlit e Plotly por tema/persona; leem contexto e estado, produzem tabelas, gráficos, diálogos e chat.

**Arquivos do projeto que utiliza:** `PI4/Frontend/src/config/__init__.py`, `PI4/Frontend/src/config/i18n.py`, `PI4/Frontend/src/models/formatting/__init__.py`, `PI4/Frontend/src/views/persona_tabs/common.py`.

**Arquivos que utilizam este módulo:** `PI4/Frontend/src/views/persona_tabs/comparison.py`, `PI4/Frontend/src/views/persona_tabs/comparison_ceo_cfo.py`, `PI4/Frontend/src/views/persona_tabs/comparison_concession.py`, `PI4/Frontend/src/views/persona_tabs/comparison_shareholders.py`.

**Outras dependências declaradas:** `pandas`, `streamlit`.

**Operações concretas realizadas neste arquivo:**

- Recebe uma seleção do usuário na interface.

<a id="arquivo-213"></a>

#### `PI4/Frontend/src/views/persona_tabs/comparison_shareholders.py`

**Para que serve:** Comparacao da persona Acionistas.

**Como funciona:** Configura os valores e as integrações compartilhadas indicados por este módulo.

**Como se relaciona com o restante:** Views Streamlit e Plotly por tema/persona; leem contexto e estado, produzem tabelas, gráficos, diálogos e chat.

**Arquivos do projeto que utiliza:** `PI4/Frontend/src/config/i18n.py`, `PI4/Frontend/src/models/formatting/__init__.py`, `PI4/Frontend/src/views/persona_tabs/common.py`, `PI4/Frontend/src/views/persona_tabs/comparison_helpers.py`.

**Arquivos que utilizam este módulo:** `PI4/Frontend/src/views/persona_tabs/comparison.py`.

**Outras dependências declaradas:** `pandas`, `plotly`, `streamlit`.

**Operações concretas realizadas neste arquivo:**

- Converte entradas para números e trata conversões inválidas conforme as opções utilizadas.
- Exibe gráficos Plotly no Streamlit.

<a id="arquivo-214"></a>

#### `PI4/Frontend/src/views/persona_tabs/concession.py`

**Para que serve:** Sub-abas da persona Poder Concedente.

**Como funciona:** Configura os valores e as integrações compartilhadas indicados por este módulo.

**Como se relaciona com o restante:** Views Streamlit e Plotly por tema/persona; leem contexto e estado, produzem tabelas, gráficos, diálogos e chat.

**Arquivos do projeto que utiliza:** `PI4/Frontend/src/config/__init__.py`, `PI4/Frontend/src/config/i18n.py`, `PI4/Frontend/src/models/formatting/tables.py`, `PI4/Frontend/src/views/persona_tabs/common.py`.

**Arquivos que utilizam este módulo:** `PI4/Frontend/src/views/persona_tabs/__init__.py`.

**Outras dependências declaradas:** `pandas`, `plotly`, `streamlit`.

**Operações concretas realizadas neste arquivo:**

- Converte uma tabela larga em registros no formato longo.
- Combina tabelas usando suas chaves de relacionamento.
- Aplica os valores de substituição definidos para dados ausentes.
- Exibe gráficos Plotly no Streamlit.

<a id="arquivo-215"></a>

#### `PI4/Frontend/src/views/persona_tabs/custom_analysis.py`

**Para que serve:** Analises customizadas do sandbox.

**Como funciona:** Configura os valores e as integrações compartilhadas indicados por este módulo.

**Como se relaciona com o restante:** Views Streamlit e Plotly por tema/persona; leem contexto e estado, produzem tabelas, gráficos, diálogos e chat.

**Arquivos do projeto que utiliza:** `PI4/Frontend/src/config/i18n.py`, `PI4/Frontend/src/models/financial_metrics/__init__.py`, `PI4/Frontend/src/models/formatting/__init__.py`, `PI4/Frontend/src/models/formatting/tables.py`.

**Arquivos que utilizam este módulo:** `PI4/Frontend/src/views/persona_tabs/__init__.py`.

**Outras dependências declaradas:** `pandas`, `plotly`, `streamlit`.

**Operações concretas realizadas neste arquivo:**

- Exibe gráficos Plotly no Streamlit.

<a id="arquivo-216"></a>

#### `PI4/Frontend/src/views/persona_tabs/shareholders.py`

**Para que serve:** Sub-abas da persona Acionistas.

**Como funciona:** Configura os valores e as integrações compartilhadas indicados por este módulo.

**Como se relaciona com o restante:** Views Streamlit e Plotly por tema/persona; leem contexto e estado, produzem tabelas, gráficos, diálogos e chat.

**Arquivos do projeto que utiliza:** `PI4/Frontend/src/config/__init__.py`, `PI4/Frontend/src/config/i18n.py`, `PI4/Frontend/src/models/formatting/tables.py`, `PI4/Frontend/src/views/persona_tabs/common.py`.

**Arquivos que utilizam este módulo:** `PI4/Frontend/src/views/persona_tabs/__init__.py`.

**Outras dependências declaradas:** `pandas`, `plotly`, `streamlit`.

**Operações concretas realizadas neste arquivo:**

- Converte uma tabela larga em registros no formato longo.
- Aplica os valores de substituição definidos para dados ausentes.
- Exibe gráficos Plotly no Streamlit.

<a id="arquivo-217"></a>

#### `PI4/Frontend/src/views/persona_tabs/styles.py`

**Para que serve:** Estilos compartilhados do comparador de cenarios.

**Como funciona:** Configura os valores e as integrações compartilhadas indicados por este módulo.

**Como se relaciona com o restante:** Views Streamlit e Plotly por tema/persona; leem contexto e estado, produzem tabelas, gráficos, diálogos e chat.

**Arquivos do projeto que utiliza:** `PI4/Frontend/src/config/__init__.py`.

**Arquivos que utilizam este módulo:** `PI4/Frontend/src/views/persona_tabs/comparison_ceo_cfo.py`, `PI4/Frontend/src/views/persona_tabs/comparison_concession.py`.

**Outras dependências declaradas:** `__future__`.

<a id="pasta-039"></a>

### Pasta `PI4/scripts/`

Ferramentas operacionais e geração do memorial; usam as regras reais do backend.

| Arquivo | O que faz |
|---|---|
| [gerar_memorial_cti.py](#arquivo-222) | Gera DOCX sem dependências de edição; usa as funções financeiras reais do CTI. |
| [precompute_cache.py](#arquivo-223) | Encaminha o precompute do build da Render para o script em Backend. |

<a id="arquivo-222"></a>

#### `PI4/scripts/gerar_memorial_cti.py`

**Para que serve:** Gera DOCX sem dependências de edição; usa as funções financeiras reais do CTI.
Saída: PI4/Backend/relatorios/ (criada automaticamente).
Execução na raiz: python3 PI4/scripts/gerar_memorial_cti.py --modelo /caminho/modelo.docx

**Como funciona:** Configura os valores e as integrações compartilhadas indicados por este módulo.

**Como se relaciona com o restante:** Ferramentas operacionais e geração do memorial; usam as regras reais do backend.

**Arquivos do projeto que utiliza:** `PI4/Backend/metrics/commercial_kpis.py`, `PI4/Backend/metrics/financial_kpis.py`.

**Outras dependências declaradas:** `argparse`, `copy`, `csv`, `hashlib`, `json`, `pandas`, `pathlib`, `re`, `sys`, `xml`, `zipfile`.

**Operações concretas realizadas neste arquivo:**

- Carrega o conteúdo binário de um arquivo.

<a id="arquivo-223"></a>

#### `PI4/scripts/precompute_cache.py`

**Para que serve:** Encaminha o precompute do build da Render para o script em Backend.

**Como funciona:** Configura os valores e as integrações compartilhadas indicados por este módulo.

**Como se relaciona com o restante:** Ferramentas operacionais e geração do memorial; usam as regras reais do backend.

**Outras dependências declaradas:** `pathlib`, `runpy`.

## Pastas de ferramentas e arquivos gerados

Esses itens estavam incluídos na contagem de dezenas de milhares de arquivos. São explicados por sua função técnica, sem transformar as bibliotecas instaladas em documentação do código da aplicação.

### `.git/`

**Para que serve:** Guarda o histórico e o estado de versionamento do repositório.

**Como funciona:** objects armazena conteúdo/histórico; refs e HEAD apontam commits; index representa a preparação do próximo commit; logs registra mudanças de referências; config configura o repositório; hooks permite automações de eventos Git.

**Interações:** É usado pelo Git e pelas ferramentas de desenvolvimento. Não é carregado pelo dashboard nem pela API.

### `PI4/.venv/`

**Para que serve:** Isola o interpretador e as bibliotecas Python instaladas para desenvolvimento local.

**Como funciona:** bin contém comandos; lib/python3.14/site-packages contém pacotes; dist-info registra versões e metadados; pyvenv.cfg descreve o ambiente.

**Interações:** Fornece FastAPI, Streamlit, pandas, NumPy, SQLAlchemy e demais dependências. Os requirements descrevem o que instalar; não são uma cópia exata de tudo que existe no ambiente.

### `**/__pycache__/ e arquivos .pyc`

**Para que serve:** Aceleram a importação dos módulos Python.

**Como funciona:** Guardam versões compiladas dos arquivos .py, específicas do interpretador.

**Interações:** São derivados do código-fonte correspondente; a responsabilidade funcional é explicada na ficha do arquivo .py.

### `.agents/, .codex/ e .aws/`

**Para que serve:** São diretórios de ferramentas presentes na raiz.

**Como funciona:** Estavam sem arquivos no inventário analisado; não há implementação local a explicar.

**Interações:** Nenhuma integração funcional pode ser deduzida apenas pela existência dos diretórios.

## Sobre a leitura deste guia

Foram explicados individualmente **228 arquivos da aplicação, dados, documentação e configuração**, além das pastas e das categorias de ferramentas e arquivos gerados. Os vínculos entre módulos foram extraídos dos imports locais; imports dinâmicos e caminhos condicionais podem estabelecer relações adicionais. Presença de um arquivo não comprova sua execução em produção.

Este próprio arquivo, `DOCUMENTACAO_TECNICA_COMPLETA_PI4.md`, serve como guia de responsabilidades e relações do projeto. Não participa da execução da API nem do dashboard.

