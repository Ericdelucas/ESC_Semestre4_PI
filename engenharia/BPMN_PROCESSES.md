# Modelagem de Processos de Negócio — BPMN do Dashboard Financeiro CTI

Especificação derivada do código do repositório em 17/10/2026. Os processos descrevem o comportamento implementado em `PI4/Frontend` e `PI4/Backend`, incluindo caminhos alternativos, regras, dados e resultados observáveis.

## 1. Visão geral e mapeamento de raias — Pools & Lanes

### 1.1 Convenções

Os diagramas usam uma **representação visual de BPMN em Mermaid**, não XML BPMN executável. Subgraphs representam pools/raias; círculos representam eventos de início/fim; retângulos representam tarefas; losangos representam gateways exclusivos ou condições. Setas contínuas representam progressão do processo; setas tracejadas representam mensagens entre participantes ou associações explicitamente rotuladas. Uma transferência por import Python não implica comunicação HTTP. Os gateways possuem saídas identificadas; ramos opcionais de background são indicados no texto.

| Pool / raia | Responsabilidade e elementos reais |
|---|---|
| Usuário | CEO, CFO, Acionistas e Poder Concedente: autenticar, escolher filtros, analisar dados, editar pareceres e consultar IA. Super Admin é condição administrativa de uma conta, cujo seed usa função CEO. |
| Interface Streamlit | `app.py:main()`, controllers `auth`, `bootstrap`, `sidebar`, `navigation`, `data_input`, `ops_menu` e views; mantém `st.session_state`, exibe gráficos e oferece downloads. |
| Servidor FastAPI | `Backend/main.py`, `runtime.py` e routers de autenticação, usuários, e-mail, chat, saúde e memorial. Executa operações HTTP e tarefas em background. |
| Pipeline analítico | `dashboard_pipeline`, `dashboard_cache`, `metrics_calculator`, `scenario_filter`, leitores e `metrics/*`; opera DataFrames e Parquets. É importado tanto pelo Streamlit quanto pela API. |
| RAG / IA | `Frontend/src/models/rag_engine` e `views/ai_assistant`; TF-IDF, FAISS ou NumPy, documentos, contexto financeiro, regras por role e Gemini. API reutiliza esse motor via `Backend/rag_engine.py:CTIRag`. |
| Infraestrutura e persistência | Render em dois serviços, Parquets locais, SQLite de autenticação e servidor SMTP. Suporte SQL/Supabase existe, mas `USAR_SUPABASE=False`; não é uma fonte ativa ou fallback automático financeiro. |

```mermaid
flowchart LR
    subgraph US["Pool: Usuário"]
        U["CEO / CFO / Acionistas / Concedente\nSuper Admin: gestão de usuários"]
    end
    subgraph ST["Pool: Interface Streamlit"]
        UI["app.main / controllers / views\nSessão, filtros, gráficos e downloads"]
    end
    subgraph API["Pool: API FastAPI"]
        HTTP["auth_router, users, email\nchat_router, report_router, health_router"]
    end
    subgraph AN["Raia compartilhada: Pipeline analítico"]
        PIPE["prepare_dashboard_data\nmontar_indicadores / build_dre\nbuild_context_metrics"]
    end
    subgraph IA["Raia: RAG / IA"]
        RAG["RagEngine.from_ranking / ask\nDocumentos e contexto da base ativa"]
    end
    subgraph INF["Pool: Infraestrutura"]
        CACHE[("Parquets locais por serviço")]
        DB[("SQLite por serviço\nusuarios / logs_acesso")]
        SMTP["SMTP externo"]
        GEM["Gemini externo"]
        SQL["Supabase / PostgreSQL\nSuporte inativo no caminho atual"]
    end
    U -. "Ações e respostas na interface" .-> UI
    UI -. "HTTP JSON / PDF" .-> HTTP
    UI -->|"Import Python local"| PIPE
    HTTP --> PIPE
    PIPE --> CACHE
    HTTP --> DB & SMTP
    UI --> RAG
    HTTP -->|"CTIRag"| RAG
    RAG -. "Inferência quando configurada" .-> GEM
    SQL -. "Não acionado pelo pipeline atual" .-> PIPE
```

### 1.2 Premissas verificadas e limites

- A leitura direta de `Backend/Cti.csv` encontrou **1.002.000 registros, 1.200 valores distintos de `CENA` e anos 1 a 12**. A quantidade pertence à base atual; os algoritmos trabalham com o universo recebido e não fixam 1.200 execuções.
- Não existe uma tarefa ativa que sorteie/execute novas trajetórias Monte Carlo. O processo 3 analisa as trajetórias armazenadas. `simular=True` testa alertas e não recalcula trajetórias.
- Cenários são selecionados por `CENA` / `cena_sel`. A expressão “cenários B3” não corresponde a uma integração com a B3 ou a um parâmetro de rota próprio; o processo 2 modela o seletor real do painel.
- EBITDA e EBIT são lidos de contas da DRE. A composição das tabelas ocorre sob demanda, com caches; não há obrigação de refazer todos os cálculos a cada clique.
- Executivo personalizado e memorial têm caminhos diferentes. O primeiro usa funções do Backend dentro do Streamlit; o segundo usa `POST /api/v1/relatorio/memorial`.

## 2. Processo 1 — Autenticação, RBAC e bootstrap de sessão

**Objetivo:** liberar uma sessão Streamlit conforme o perfil e carregar os dados necessários ao painel. **Início:** acesso à URL pública. **Entradas:** `LoginIn.email`, `LoginIn.password`. **Saídas:** sessão autenticada e `AppContext`, ou mensagem de rejeição/indisponibilidade.

```mermaid
flowchart TD
    subgraph U1["Raia: Usuário"]
        S1(("Início: acessar URL pública"))
        C1["Digitar e-mail e senha\nSubmeter render_login"]
        E1(("Fim: painel disponível"))
    end
    subgraph F1["Raia: Streamlit"]
        A1["app.main: configure_page\nPrimeiro rerun leve de WebSocket"]
        G1{"is_authenticated?"}
        L1["render_login / authenticate\nIgnorar submit duplicado em andamento"]
        H1["post_json: /api/v1/auth/login\nemail, password; timeout=20"]
        R1{"Status da autenticação?"}
        ERR1["Exibir st.error\nManter formulário de login"]
        LOCAL1["_autenticar_local\nseed_usuarios e autenticar_db\nBanco do processo Streamlit"]
        LG1{"Fallback local válido?"}
        ROLE1{"role está em ROLE_PERSONAS?"}
        SET1["_abrir_sessao / _aplicar_usuario\nauthenticated, user_role, user_email, user_funcao\nSelecionar persona permitida; st.rerun"]
        BOOT1["carregar_estado / carregar_pipeline\nReutilizar st.cache_data quando disponível"]
        BG1{"Dados carregados?"}
        STOP1(("Fim de erro: st.stop após diagnóstico"))
        VIEW1["render_sidebar / render_persona\nmontar_contexto e render_pagina\nPERSONA_NAV_KEYS libera abas"]
    end
    subgraph API1["Raia: FastAPI e autenticação"]
        APIAUTH1["auth_router.login\nPOST /api/v1/auth/login"]
        DB1["session_scope / db.auth.autenticar\nNormalizar e-mail e buscar Usuario"]
        VALID1{"Usuário existe, ativo\ne verificar_senha é verdadeiro?"}
        LOGFAIL1["registrar_log de falha\nHTTP 401"]
        LOGOK1["registrar_log de sucesso\nusuario_publico; commit da sessão\nHTTP 200 com user e risk_alert:null"]
        BACK1["Se executivo ou Super Admin:\nagendar _alerta_risco_em_fundo\nContinuação independente no processo 3"]
    end
    subgraph P1["Raia: Pipeline analítico"]
        LOAD1["prepare_dashboard_data\nParquets ou caminho de contingência do processo 2"]
    end
    S1 --> A1 --> G1
    G1 -->|Não| C1
    C1 --> L1 --> H1
    H1 -. "Requisição HTTP" .-> APIAUTH1
    APIAUTH1 --> DB1 --> VALID1
    VALID1 -->|Não| LOGFAIL1
    VALID1 -->|Sim| LOGOK1
    LOGOK1 -. "Tarefa opcional em background" .-> BACK1
    LOGFAIL1 -. "Resposta" .-> R1
    LOGOK1 -. "Resposta" .-> R1
    H1 -->|"Falha de conexão: cliente retorna 503"| R1
    R1 -->|"200 e ok"| ROLE1
    R1 -->|503| LOCAL1 --> LG1
    R1 -->|"Demais respostas"| ERR1
    LG1 -->|Sim| ROLE1
    LG1 -->|Não| ERR1
    ROLE1 -->|Não| ERR1
    ERR1 --> C1
    ROLE1 -->|Sim| SET1 --> BOOT1
    G1 -->|Sim| BOOT1
    BOOT1 --> LOAD1 --> BG1
    BG1 -->|Não| STOP1
    BG1 -->|Sim| VIEW1 --> E1
```

### Regras e exceções

| Regra | Implementação |
|---|---|
| Validação de senha | `db/auth.py:verificar_senha()`, PBKDF2-HMAC-SHA256, salt e 120.000 iterações; comparação por `hmac.compare_digest` |
| CEO | Personas `ceo`, `cfo`, `acionistas`, `concedente` |
| CFO | Personas `cfo`, `acionistas`, `concedente` |
| Acionistas / Poder Concedente | Apenas `acionistas` / `concedente`, respectivamente |
| Super Admin | `navigation.render_analises()` acrescenta `admin_users` na persona CEO; API usa `_exigir_super_admin(email)` |
| Logs de acesso | `LogAcesso`: e-mail, função, sucesso, horário, IP e mensagem; consulta por `GET /api/v1/auth/logs?email=...&limite=200`, exigindo CEO ativo |
| Falha de API | `authenticate()` tenta `_autenticar_local()` em status 503; não faz fallback para credenciais rejeitadas com 401 |
| Falha no bootstrap | `carregar_estado()` tenta reler o cache em certas exceções; `MemoryError` retorna `None`; `app.main()` interrompe se estado ausente |

`db/database.py` usa `Backend/cache/cti_auth.db` no caminho ativo. Os SQLite do frontend e da API são independentes na implantação em dois serviços. O login não emite JWT; as rotas administrativas verificam o e-mail fornecido na query, sem ligação por token com a sessão Streamlit. Funções de cookie assinado existem, mas a sequência principal atual não as invoca para restaurar a sessão. Logout registra a saída por `POST /api/v1/auth/logout` e limpa o estado do painel preservando idioma.

## 3. Processo 2 — Exploração analítica, filtros de cenário e reconciliação DRE

**Objetivo:** apresentar o recorte financeiro e as comparações da base ativa. **Início:** seleção de `cena_sel` ou `ano_sel` ou abertura inicial do painel. **Entradas:** base longa `df`, indicadores `ind`, `ranking`, cenário, ano e persona. **Saída:** cartões, tabelas, séries, distribuição e gráficos atualizados.

```mermaid
flowchart TD
    subgraph U2["Raia: Usuário"]
        S2(("Início: selecionar cenário ou ano"))
        END2(("Fim: analisar tabelas e gráficos"))
    end
    subgraph F2["Raia: Streamlit"]
        RERUN2["app.main: rerun\ncarregar_estado / carregar_pipeline"]
        HIT2{"Resultado em st.cache_data?"}
        ACTIVE2{"has_custom_data?"}
        CUSTOM2["render_data_input\nnormalizar_upload / importar_planilha\nmontar_indicadores_customizados"]
        FILTER2["render_sidebar e render_persona\nmontar_contexto(df, ind, ranking, filtros)"]
        SHOW2["render_pagina / render_analises\nViews da persona e comparação\nrender_comparar_cenarios"]
        FAIL2(("Fim de erro: diagnóstico de dados"))
    end
    subgraph P2["Raia: Pipeline e armazenamento local"]
        PREP2["prepare_dashboard_data(csv_path)"]
        PQ2{"Três Parquets presentes\ne leitura bem-sucedida?"}
        READ2["load_cached_dashboard\ncti_limpo, indicadores e ranking"]
        RENDER2{"RENDER está definido?"}
        BLOCK2["RuntimeError\nCSV bloqueado em runtime Render"]
        CSV2["carregar_csv / load_cti_csv\nforcar_ficheiro=True\nNormalizar e compactar a base"]
        CALC2["calcular_indicadores / montar_indicadores\nResolver contas, pivotar, calcular KPIs e ranking\nTentar gravar Parquets"]
        DATA2["Disponibilizar df, ind, ranking"]
        CTX2["build_context_metrics\nfiltrar_cenario_ano / calcular_kpis_recorte\nmedia_por_ano para Todos\nProbabilidade com ranking integral"]
        TABLE2["Cálculos sob demanda nas views\nbuild_dre / build_break_even\nbuild_financial_statement\ncalculate_ltv_cac ou helpers locais de LTV"]
    end
    S2 --> RERUN2 --> HIT2
    HIT2 -->|Não| PREP2 --> PQ2
    HIT2 -->|Sim| ACTIVE2
    PQ2 -->|Sim| READ2 --> DATA2
    PQ2 -->|Não| RENDER2
    RENDER2 -->|Sim| BLOCK2 --> FAIL2
    RENDER2 -->|Não| CSV2 --> CALC2 --> DATA2
    DATA2 --> ACTIVE2
    ACTIVE2 -->|Sim| CUSTOM2 --> FILTER2
    ACTIVE2 -->|Não| FILTER2
    FILTER2 --> CTX2 --> TABLE2 --> SHOW2 --> END2
```

### Regras financeiras e significado da reconciliação

1. `montar_indicadores()` mapeia nomes com `resolve_account_name()`, agrega por `ANO`, `ano_num`, `CENA` e campo e calcula NCG, prazos, liquidez, retorno e risco. Não é chamada para recalcular a base padrão a cada filtro quando o resultado está cacheado.
2. `build_dre(df, cena)` monta a tabela: receita líquida = receita + tributos; EBITDA = conta `DRE - EBITDA`; EBIT = conta `DRE - Resultado Operacional`. Lucro informado prevalece se `abs(lucro) > 1e-9`; senão usa EBIT + resultado financeiro + IR/CS. Isso não impõe uma reconciliação genérica entre EBITDA, depreciação e EBIT.
3. `build_break_even()` usa custos variáveis absolutos, custos fixos e margem de contribuição; divisores nulos podem produzir valores não definidos. `calculate_ltv_cac()` busca premissas por aliases e aplica padrões se ausentes. `views/persona_tabs/common.py` oferece `_dre`, `_break_even_df` e `_ltv_df` com caminhos cacheados da base padrão.
4. `_wide()` usa soma por ano/conta para cenário específico e média para `Todos`. `build_context_metrics()` mantém o risco de encerramento no universo integral do ranking, mesmo com filtro visual específico.
5. `cache_disponivel()` exige os três Parquets. O leitor isolado pode reconstruir uma base parcial por `df_longo_de_indicadores()` quando o bruto está vazio/ausente, mas a ausência do arquivo bruto bloqueia a entrada normal pelo teste dos três arquivos. Essa reconstrução não recupera todas as contas da DRE.
6. Nenhuma seleção consulta cotações da B3. A entrada de cenário real é a coluna `CENA`; o ano real é `ano_num`. Alterações de dados importados ficam na sessão e não atualizam automaticamente a base financeira da API.

**Preparação anterior ao processo:** `Backend/scripts/precompute_cache.py:main()` lê o CSV em chunks de 120.000 registros, normaliza contas e valores brasileiros, extrai `ano_num`, rejeita base vazia/com menos de 1.000 linhas, calcula indicadores/ranking e reescreve os três Parquets. O manifesto Render executa essa tarefa no build do frontend.

## 4. Processo 3 — Análise Monte Carlo, varredura e alertas de risco

**Objetivo:** avaliar risco das trajetórias existentes e emitir um único e-mail consolidado quando autorizado pelas regras. **Inícios:** login executivo com tarefa em background, ação manual no menu ou chamada do serviço. **Entradas HTTP:** query `email`; `VarreduraIn(enviar=True, simular=False)`. **Saída:** payload de varredura e resultado de envio.

```mermaid
flowchart TD
    subgraph U3["Raia: Usuário / evento de negócio"]
        MAN3(("Início: acionar varredura no menu"))
        LOGIN3(("Início alternativo: login executivo"))
    end
    subgraph F3["Raia: Streamlit"]
        REQ3["render_ops_menu\nPOST /api/v1/email/varrer-risco\nquery email; body enviar e simular"]
        RES3["guardar_varredura / _toast_resposta_email\nExibir resultado ou diagnóstico"]
        FALL3["Fallback local em falha de API/SMTP\ndisparar_alerta_risco no Streamlit"]
        END3(("Fim: resultado disponível"))
    end
    subgraph API3["Raia: FastAPI"]
        AUTH3["varrer_e_alertar / _exigir_executivo\nValidar usuário ativo CEO/CFO ou Super Admin"]
        PERM3{"Autorizado?"}
        DENY3["HTTP 403"]
        SEND3{"body.enviar?"}
        BG3["_alerta_risco_em_fundo\nforcar=False, origem=login\nsimular=forcar_alerta_login()"]
        RETURN3["Retornar payload\ncritical, checks, metrics, summary\nsent, recipients, email_error quando envio avaliado"]
    end
    subgraph P3["Raia: Pipeline / motor de risco"]
        LOAD3["_ranking / _ranking_cache\nprepare_dashboard_data\nLer trajetórias já armazenadas"]
        MET3["varrer_riscos(ranking)\nprobabilidade_caixa_negativo\nP5 de caixa_ano12, liquidez e selos"]
        EVAL3{"Fluxo pede envio?"}
        SIM3{"simular=True?"}
        SIMTASK3["_aplicar_simulacao\nAlterar payload para testar alerta"]
        DEST3["_destinatarios / _chave_digest"]
        SKIP3{"Já enviado neste login\nou dentro do debounce?"}
        SKIPPED3["sent=False\nskipped=sessao_login ou debounce"]
        CRIT3{"Algum check crítico?\nRuína > limiar OU P5 < 0\nOU liquidez < mínimo OU selo > limiar"}
        NORMAL3["sent=False\nSem envio por ausência de criticidade"]
        HTML3["html_alerta_consolidado\nConsolidar métricas em um e-mail"]
    end
    subgraph I3["Raia: SMTP e observabilidade"]
        SMTP3["enviar_alerta_email\nValidar configuração e tentar entrega SMTP"]
        OK3{"Envio bem-sucedido?"}
        SUCCESS3["_marcar_envio\nRegistrar destino em _LOGIN_ENVIADO se login\nsent=True e recipients"]
        ERROR3["sent=False e email_error\nDiagnóstico de configuração/rede/SMTP"]
    end
    MAN3 --> REQ3
    REQ3 -. "HTTP" .-> AUTH3 --> PERM3
    PERM3 -->|Não| DENY3 -. "Resposta" .-> RES3
    PERM3 -->|Sim| SEND3
    SEND3 -->|"Sim: disparar_alerta_risco"| LOAD3
    SEND3 -->|"Não: varrer_riscos"| LOAD3
    LOGIN3 --> BG3 --> LOAD3
    LOAD3 --> MET3 --> EVAL3
    EVAL3 -->|Não| RETURN3
    EVAL3 -->|Sim| SIM3
    SIM3 -->|Sim| SIMTASK3 --> DEST3
    SIM3 -->|Não| DEST3
    DEST3 --> SKIP3
    SKIP3 -->|Sim| SKIPPED3 --> RETURN3
    SKIP3 -->|Não| CRIT3
    CRIT3 -->|Não| NORMAL3 --> RETURN3
    CRIT3 -->|Sim| HTML3 --> SMTP3 --> OK3
    OK3 -->|Sim| SUCCESS3 --> RETURN3
    OK3 -->|Não| ERROR3 --> RETURN3
    RETURN3 -. "Resposta manual; background apenas registra resultado" .-> RES3
    REQ3 -->|"Falha identificada pelo controller"| FALL3
    ERROR3 -. "Se resposta manual indicar falha" .-> FALL3
    FALL3 -->|"Reutiliza o mesmo fluxo de risco localmente"| LOAD3
    RES3 --> END3
```

O diagrama reúne variantes do mesmo serviço. O ramo de envio conhece a origem (`manual` ou `login`); a execução local reutiliza os mesmos gateways e retorna ao controller, sem novo POST. No fluxo de background, não há resposta de risco anexada ao login: o contrato mantém `risk_alert:null`; exceções são capturadas por `_alerta_risco_em_fundo()` e registradas em logs técnicos.

### Regras de risco e evidências de auditoria

| Item | Regra implementada |
|---|---|
| Universo | `CENA` distinta; base atual com 1.200 trajetórias de 12 anos, sem executar novas trajetórias |
| Encerramento | Maior `ano_num` da base; campo mantém o nome `caixa_ano12`; usa saldo final quando módulo > `1e-9`, senão disponível |
| Ruína | `100 × média(caixa_ano12 < 0)`; crítico acima de `RISK_RUIN_THRESHOLD`, padrão 15%; acima de 5% gera atenção se não ultrapassa o limiar crítico |
| P5 | Quantil 0,05 de `caixa_ano12`; crítico se negativo |
| Liquidez | Média do ranking abaixo de `RISK_LIQUIDEZ_MIN`, padrão 1,0; usa liquidez corrente, não liquidez geral do concedente |
| Selo | Participação de `Encerramento com Caixa Insuficiente` acima do limiar de ruína |
| Debounce | Padrão 900 s no login e 45 s no manual; estruturas em memória `_ULTIMO_DIGEST` e `_LOGIN_ENVIADO` |
| Consulta sem envio | `GET /api/v1/email/riscos?email=...` ou POST com `enviar=False`; este último não aplica simulação no ramo sem envio |
| Simulação de alerta | `simular=True` / `FORCE_EMAIL_ALERT_ON_LOGIN`; altera checks para teste, não a base de cenários |

**Distinção de logs:** login e logout persistem registros em `logs_acesso`. A varredura e o SMTP produzem logs técnicos/diagnósticos e payload de resultado; o fluxo não insere um registro `LogAcesso` para cada varredura ou envio. `risk_report.gerar_relatorio_riscos()` é utilitário adicional e não uma etapa obrigatória de cada alerta. `garantir_varredura_silenciosa()` apenas marca estado da sessão; não dispara varredura/e-mail automaticamente em cada renderização.

## 5. Processo 4 — Parecer executivo, PDF e memorial dinâmico

**Objetivo:** produzir um documento para download, respeitando a origem de dados de cada modalidade. **Início:** `Criar Relatório` no cabeçalho e seleção do tipo de relatório. **Modalidades:** executivo personalizado local e memorial técnico remoto.

```mermaid
flowchart TD
    subgraph U4["Raia: Usuário"]
        S4(("Início: Criar Relatório / Gerar Memorial"))
        EDIT4["Selecionar blocos, perfil editorial\nAutor, empresa, cenários e pareceres"]
        DOWN4["Clicar em baixar arquivo"]
        END4(("Fim: PDF entregue ao navegador"))
    end
    subgraph F4["Raia: Streamlit"]
        OPEN4["open_relatorio / render_dialog\n_render_report_body"]
        TYPE4{"Tipo de relatório?"}
        INIT4["block_options / default_block_notes\n_ensure_report_defaults"]
        VALID4{"Há blocos selecionados?"}
        WARN4["Exibir erro e manter formulário"]
        QUEUE4["_build_notes\nGuardar payload em _cti_report_pending\nst.rerun"]
        FLUSH4["flush_pending_pdf fora do st.dialog\n_gerar_pdf / _df_relatorio / _frames_relatorio"]
        MEMUI4["_render_memorial\nMontar scenario e year"]
        CUSTOM4{"has_custom_data?"}
        BLOCK4["Avisar: memorial usa base da API\nOrientar uso do executivo personalizado"]
        POST4["post_pdf /api/v1/relatorio/memorial\ntimeout=120"]
        PREVIEW4["Guardar custom_report_pdf\n_pdf_para_imagens e pré-visualização"]
        SNAP4["Validar application/pdf e prefixo %PDF-\nGuardar memorial_api_download por filtros"]
        BUTTON4["st.download_button\nBytes dinâmicos e nome do arquivo"]
        ERR4["Exibir diagnóstico\nLimpar pendência ou download inválido"]
    end
    subgraph SVC4["Raia: Serviços Python no processo Streamlit"]
        GEN4["custom_report_service.generate_custom_report_pdf\nscenario, selected_blocks, notes, author, profile\ncompany_name, comparison_scenarios\nskip_charts=True, use_llm=False"]
        INS4["insights_from_tables\nmerge_notes_with_insights"]
        NOTE4{"Texto editado não vazio\ne diferente do automático?"}
        REPLACE4["Substituir integralmente\no parecer do mesmo bloco"]
        KEEP4["Manter parecer automático"]
        PDF4["Montar blocos ReportLab\nHelpers de report_generator\nSimpleDocTemplate e BytesIO"]
    end
    subgraph API4["Raia: FastAPI e serviços da API"]
        ROUTE4["report_router.memorial / MemorialIn\nscenario=Todos por padrão\nyear=None ou inteiro entre 1 e 127"]
        LOAD4["prepare_dashboard_data\nBase própria da API"]
        MEM4["gerar_memorial_pdf(df, ranking, scenario, year)\nValidar filtros disponíveis\nCalcular tabelas antes de filtrar ano\nvarrer_riscos com ranking integral"]
        RES4["ReportLab em memória\nResponse application/pdf\nattachment; Cache-Control:no-store"]
        BAD4["422: ValueError / validação\n503: OSError ou RuntimeError"]
    end
    S4 --> OPEN4 --> TYPE4
    TYPE4 -->|Executivo| INIT4 --> EDIT4 --> VALID4
    VALID4 -->|Não| WARN4 --> EDIT4
    VALID4 -->|Sim| QUEUE4 --> FLUSH4 --> GEN4 --> INS4 --> NOTE4
    NOTE4 -->|Sim| REPLACE4 --> PDF4
    NOTE4 -->|Não| KEEP4 --> PDF4
    PDF4 --> PREVIEW4 --> BUTTON4
    FLUSH4 -->|"Exceção na geração"| ERR4
    TYPE4 -->|Memorial| MEMUI4 --> CUSTOM4
    CUSTOM4 -->|Sim| BLOCK4
    CUSTOM4 -->|Não| POST4
    POST4 -. "HTTP JSON: scenario e year" .-> ROUTE4
    ROUTE4 --> LOAD4 --> MEM4 --> RES4
    LOAD4 -->|"Base indisponível"| BAD4
    MEM4 -->|"Filtro inválido ou erro tratado"| BAD4
    RES4 -. "Resposta binária" .-> SNAP4 --> BUTTON4
    BAD4 -. "Resposta de erro" .-> ERR4
    POST4 -->|"Falha de rede ou PDF inválido"| ERR4
    BUTTON4 --> DOWN4 --> END4
```

### Contratos, regras e resultados

- **Executivo:** o payload em `st.session_state[PENDING_KEY]` contém `scenario`, `selected_blocks`, `notes`, `author`, `profile`, `company_name`, `comparison_scenarios` e `filename`. `_gerar_pdf()` importa o serviço do pacote Backend localmente; não envia esse payload por HTTP a `report_generator.py`.
- `generate_custom_report_pdf()` constrói seu próprio documento e reutiliza layout de `report_generator.py`; não é uma chamada obrigatória a `generate_executive_pdf()`. Usa tabelas preparadas `_dre`, `_break_even_df`, `_ltv_df` e até três cenários extras. A base customizada é aceita nesse caminho.
- `merge_notes_with_insights()` substitui integralmente o texto automático do bloco quando há texto diferente e não vazio. Campo vazio ou igual ao automático conserva a sugestão; não concatena pareceres indiscriminadamente.
- `profile` pode ser CEO, CFO ou CTO; é perfil editorial. CTO não é função autenticável. O executivo não recebe `year` para filtrar a base, mesmo com ano selecionado no painel.
- **Memorial:** `POST /api/v1/relatorio/memorial`, corpo `{"scenario":"Todos","year":null}` ou cenário/ano disponível. Os filtros também são validados contra a base pelo serviço. DRE, break-even, solvência e métricas comerciais são calculados para o cenário; o risco continua consolidado sobre todos os cenários. A geração não envia e-mail.
- Alterar filtros invalida o snapshot `memorial_api_download`. Em erro de geração executiva, `flush_pending_pdf()` remove a pendência e armazena diagnóstico para exibição. O fluxo normal usa bytes em memória e não exige salvar PDF no disco do servidor.
- Estes dois caminhos produzem PDF por ReportLab. A criação offline de DOCX em `PI4/scripts/gerar_memorial_cti.py` é outro processo, não uma etapa do download dinâmico.

## 6. Processo 5 — Consulta ao assistente financeiro IA / RAG

**Objetivo:** responder perguntas com o contexto permitido da base ativa e a documentação indexada. **Início:** envio de pergunta no chat do painel. **Entradas:** pergunta, histórico, idioma, cenário, ano, persona, role, DataFrames e KPIs. **Saída:** resposta textual na conversa e eventual atalho de navegação.

```mermaid
flowchart TD
    subgraph U5["Raia: Usuário"]
        S5(("Início: enviar pergunta no chat"))
        END5(("Fim: ler resposta e eventual atalho"))
    end
    subgraph F5["Raia: Streamlit / assistente"]
        ASK5["panel.gerar_resposta_ia\nPergunta e contexto do dataset ativo"]
        GET5["context._carregar_engine\nCache de recurso por fingerprint do ranking"]
        CONT5["contexto_dataset_ativo e _contexto_foco\nFiltros, cartões, DRE, KPIs e role"]
        CALL5["engine.ask(question, lang, history, api_key\nextra_context, cena_sel, user_role)"]
        VIEW5["Exibir resposta no histórico\nDetectar intenção e oferecer navegação permitida"]
        ERROR5["Exibir mensagem de falha do motor"]
    end
    subgraph R5["Raia: Motor RAG local compartilhado"]
        CACHE5{"Motor já cacheado?"}
        DOC5["RagEngine.from_ranking\ndocs_manuais, docs_glossario, docs_cenarios\nDocumentos financeiros e metadados"]
        EMB5["TfidfEmbeddings.fit / embed_documents\nGerar vetores normalizados"]
        INDEX5{"faiss_index disponível?"}
        FAISS5["Manter índice FAISS"]
        NUMPY5["Fallback de busca por NumPy"]
        GUIDE5{"_escolher_guia encontra atalho local?"}
        LOCAL5["_resposta_sem_llm\nResposta do guia local"]
        RBAC5{"question_is_blocked?"}
        DENY5["deny_message\nSem recuperação ou inferência"]
        SEARCH5["retrieve(query, k=8, cena_sel, user_role)\ndocument_allowed / embed_query\nBusca vetorial e prioridade_fonte"]
        SAN5["Compor trechos e contexto ativo\nsanitize_context por role"]
        KEY5{"resolve_api_key disponível?"}
        NOAI5["_resposta_sem_llm\nSanitizar resposta local"]
        CLEAN5["sanitize_answer\nRetornar resposta e fontes"]
    end
    subgraph EXT5["Raia: Serviço Gemini"]
        LLM5["answers.gerar_llm\nHistórico recente, contexto e regras de perfil\nTentar modelos de GEMINI_MODELS"]
        OK5{"Algum modelo respondeu?"}
        FALL5["Retornar mensagem de contingência\nTodos os modelos falharam"]
    end
    S5 --> ASK5 --> GET5 --> CACHE5
    CACHE5 -->|Não| DOC5 --> EMB5 --> INDEX5
    INDEX5 -->|Sim| FAISS5 --> CONT5
    INDEX5 -->|Não| NUMPY5 --> CONT5
    CACHE5 -->|Sim| CONT5
    GET5 -->|"Erro de inicialização"| ERROR5 --> END5
    CONT5 --> CALL5 --> GUIDE5
    GUIDE5 -->|Sim| LOCAL5 --> VIEW5
    GUIDE5 -->|Não| RBAC5
    RBAC5 -->|Sim| DENY5 --> VIEW5
    RBAC5 -->|Não| SEARCH5 --> SAN5 --> KEY5
    KEY5 -->|Não| NOAI5 --> VIEW5
    KEY5 -->|Sim| LLM5 --> OK5
    OK5 -->|Sim| CLEAN5 --> VIEW5
    OK5 -->|Não| FALL5 --> CLEAN5
    VIEW5 --> END5
```

### Particularidades do motor e entrada alternativa HTTP

A indexação ocorre quando o recurso precisa ser construído, não a cada pergunta. `from_ranking()` inclui documentos detalhados por cenário apenas para ranking com até 80 linhas; bases maiores usam documentos resumidos. Ausência de arquivos documentais não elimina o contexto de KPIs do painel; o motor informa a limitação conforme o ramo de resposta. Falhas de montagem do contexto visual geram um contexto resumido de contingência.

O código verifica o guia local **antes** de `question_is_blocked()` em `ask()`; o diagrama preserva essa ordem. A recuperação filtra documentos por role e sanitiza contexto. Com chave ausente, a resposta é local. Com chave, `gerar_llm()` tenta os modelos configurados e usa mensagem de contingência se todos falharem. Não se deve representar toda resposta como obrigatoriamente gerada por Gemini.

A interface principal chama `RagEngine` por import local. Existe também a seguinte entrada independente:

| Etapa HTTP | Contrato real |
|---|---|
| Recepção | `POST /api/chat`, `ChatIn(message, session_id=None, user_role=None)` |
| Serviço | `chat_service.responder_chat(message, session_id, user_role)`; mensagem vazia retorna orientação sem carregar motor |
| Inicialização | `_rag()` cria `CTIRag` sob `Lock`; `CTIRag` reutiliza `RagEngine.from_ranking()` |
| Dados | `_carregar_ranking()` lê cache da API; sem cache na Render retorna ranking vazio; fora dela pode usar CSV e `montar_indicadores()` |
| Resposta | `ChatOut(response, sources)`; `_sessoes` guarda últimas 12 mensagens por sessão em memória |
| Limite | `user_role` vem do corpo, sem validação por token; esta entrada não recebe o dataset importado na sessão Streamlit |

## 7. Infraestrutura, contingências e relação entre os processos

| Condição | Resultado de negócio e implementação |
|---|---|
| Cache frontend pronto | Processo 1 libera a base; processo 2 reutiliza `st.cache_data` e os Parquets |
| Cache ausente fora da Render | Pipeline lê CSV, calcula indicadores e tenta gravar caches |
| Cache ausente na Render | Pipeline bloqueia CSV em runtime; painel mostra diagnóstico; memorial pode responder 503; alerta em background registra falha |
| Parquets presentes apenas no frontend | Não atendem à API: `render.yaml` executa precompute apenas no build do frontend, sem volume compartilhado declarado |
| Supabase desativado | Dados analíticos permanecem locais; autenticação usa SQLite. `db/database.init_db()` contém contingência PostgreSQL → SQLite, mas a flag atual já seleciona SQLite |
| SMTP indisponível | Resultado de envio contém diagnóstico; controller pode tentar execução local. Não existe garantia de entrega se a rede/configuração falhar nos dois processos |
| API indisponível | Login pode validar localmente; executivo e chat principal continuam com serviços locais quando os respectivos dados/dependências estão disponíveis; memorial depende da API |
| Serviço reiniciado | Históricos de chat e debounce em memória não constituem persistência durável; bancos e caches dos serviços não são sincronizados automaticamente |

A implantação principal está em `render.yaml`: `cti-frontend` executa Streamlit e precompute; `cti-api` executa Uvicorn. `start.sh` oferece uma execução alternativa conjunta, com FastAPI interna e Streamlit público. Os diagramas identificam o processo que executa cada tarefa, sem pressupor que a implantação foi realizada ou validada remotamente.

## 8. Rastreabilidade da especificação

| Processo / assunto | Fontes inspecionadas |
|---|---|
| Raias e execução | `PI4/Frontend/app.py`, `PI4/Backend/main.py`, `runtime.py`, `render.yaml`, `start.sh` |
| Processo 1 | `Frontend/src/controllers/auth.py`, `bootstrap.py`, `sidebar.py`, `navigation.py`; `Backend/routers/auth_router.py`, `users.py`; `Backend/db/auth.py`, `database.py`, `models.py` |
| Processo 2 | `Frontend/src/controllers/data_input.py`; `Backend/services/dashboard_pipeline.py`, `dashboard_cache.py`, `metrics_calculator.py`, `scenario_filter.py`; `Backend/data_loader/*`; `Backend/metrics/financial_kpis.py`, `commercial_kpis.py`; `Frontend/src/views/persona_tabs/common.py` |
| Processo 3 | `Frontend/src/controllers/ops_menu.py`; `Backend/routers/email.py`, `auth_router.py`; `Backend/services/risk_alerts.py`, `email_service.py`, `risk_report.py` |
| Processo 4 | `Frontend/src/views/report.py`, `controllers/modals.py`; `Backend/routers/report_router.py`; `Backend/services/custom_report_service.py`, `report_insights.py`, `report_generator.py`, `memorial_report.py` |
| Processo 5 | `Frontend/src/views/ai_assistant/panel.py`, `context.py`; `Frontend/src/models/rag_engine/engine.py`, `embeddings.py`, `documents.py`, `rbac.py`, `answers.py`; `Backend/rag_engine.py`, `routers/chat_router.py`, `services/chat_service.py` |
| Base e preparação | `Backend/Cti.csv`, `Backend/scripts/precompute_cache.py`, `PI4/scripts/precompute_cache.py` |

A especificação foi construída por inspeção estática e conferência da volumetria do CSV. Não implica execução de SMTP, Gemini, implantação Render ou nova simulação. O documento mantém explícitas as diferenças entre a descrição de negócio solicitada e os mecanismos presentes no código.
