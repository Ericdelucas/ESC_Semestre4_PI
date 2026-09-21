# Inventário do PI4

O que existe dentro de `PI4/`, pasta por pasta e arquivo por arquivo. Números medidos em 21 de setembro de 2026.

`__pycache__/` aparece depois de rodar o Python. É bytecode gerado (`.pyc`). Não é código-fonte. O `.gitignore` manda o Git ignorar essa pasta.

---

## Pasta `PI4/`

Raiz do trabalho deste semestre. Tem três arquivos de configuração e duas pastas: `Backend` e `Frontend`.

### `PI4/.env`

Arquivo local, fora do Git. Três linhas:

```text
# Copie para .env e preencha. Não versionar o .env.
GOOGLE_API_KEY=
```

A variável está vazia. É a chave do Gemini. A API e o motor de busca leem este arquivo.

### `PI4/.env.example`

Igual ao `.env`, mas este pode ir para o Git. Serve de modelo para quem clona o repositório criar o `.env`.

### `PI4/.gitignore`

Lista do que o Git não versiona:

- `.venv/` — ambiente virtual
- `__pycache__/` e `*.pyc` — bytecode
- `cache/` — os Parquet gerados
- `.env` — a chave
- `.streamlit/secrets.toml` — segredo do Streamlit, se existir

### `PI4/README.md`

Texto de como subir o projeto. 74 linhas. Diz para instalar os dois `requirements`, copiar o `.env.example`, subir a API na porta 8000 com Uvicorn e o dashboard na 8501 com Streamlit. No final há um desenho curto da estrutura: `Backend/` e `Frontend/`.

---

## Pasta `PI4/Backend/`

Servidor do chat e os dados. Não desenha gráfico. Quem calcula os indicadores é o código em `Frontend/src/models/`, importado daqui.

Arquivos:

- `.env.example`
- `Cti.csv`
- `main.py`
- `rag_engine.py`
- `requirements.txt`
- pasta `cache/`
- pasta `documentos/`

### `Backend/.env.example`

Modelo da chave só desta pasta:

```text
# Copie para Backend/.env e preencha. Não versionar o .env.
GOOGLE_API_KEY=
```

Não existe `Backend/.env` no disco. A chave, se for preenchida, está prevista em `PI4/.env` ou neste caminho.

### `Backend/requirements.txt`

Pacotes da API, um por linha, com versão mínima:

- fastapi
- uvicorn
- pandas
- numpy
- langchain-core
- langchain-text-splitters
- scikit-learn
- faiss-cpu
- google-genai
- pypdf
- python-dotenv
- pyarrow

### `Backend/Cti.csv`

Base bruta. Cerca de 66 MB. Sem linha de cabeçalho. Cada linha tem quatro campos, separados por vírgula:

1. `ANO` — texto `Ano 1` até `Ano 12`
2. `CENA` — texto `Total Cen_00001` e os demais cenários
3. `CONTA` — nome da conta. Começa com `BAL -` (balanço), `DRE -` (resultado) ou `FLU -` (fluxo)
4. `VALOR` — número em formato brasileiro, entre aspas quando tem ponto de milhar. Exemplo: `"1.205.264.965,52"`. Pode ser negativo.

A primeira linha real é:

`Ano 1,Total Cen_00001,,"0,025138815"`

A conta dessa primeira linha veio vazia no arquivo. As seguintes trazem contas como `BAL - Total do Ativo`, `BAL - Disponível`, `BAL - Contas a Receber - Clientes`.

O Parquet limpo, gerado a partir deste CSV, tem 1.002.000 linhas. São 1.200 cenários.

### `Backend/main.py`

Programa da API. O que tem dentro:

- `load_dotenv` em `Backend/.env` e em `PI4/.env`, antes de importar o resto.
- `app = FastAPI(title="CTI Assistente")`, com CORS aberto para qualquer origem.
- Classe `ChatIn`: campos `message` (str) e `session_id` (str ou vazio).
- Classe `ChatOut`: campos `response` (str) e `sources` (lista de str).
- Dicionário `_sessoes`: histórico em memória, no máximo 12 mensagens por sessão.
- Função `_rag()`: cria um `CTIRag` na primeira chamada e reutiliza depois.
- Rota `GET /api/health`: devolve `{"status":"ok"}`.
- Rota `POST /api/chat`: lê a mensagem, chama `CTIRag.responder`, grava a troca no histórico e devolve texto e fontes. Mensagem vazia devolve o aviso "Escreva uma pergunta sobre os cenários da CTI."

Sobe com:

`py -m uvicorn Backend.main:app --host 127.0.0.1 --port 8000`

a partir da pasta `PI4`.

### `Backend/rag_engine.py`

Ponte entre a API e o motor que está em `Frontend/src/models/rag_engine.py`. O que tem dentro:

- Caminhos fixos: `Cti.csv`, `documentos/`, `cache/`, todos relativos a esta pasta.
- `load_dotenv` de novo, nos dois `.env`.
- Coloca `PI4/Frontend` no `sys.path` para importar `src.models`.
- Classe `CTIRag`:
  - no `__init__` carrega o ranking e cria `RagEngine.from_ranking`
  - `responder(message, history)` chama `engine.ask` em português, com a chave que `resolve_api_key()` achar, sem cenário em foco e sem texto extra
- Função `_carregar_ranking`: se `cache/ranking.parquet` existir e for mais novo que o CSV, lê o Parquet. Senão lê o CSV com `load_cti_csv` e calcula com `montar_indicadores`.

---

## Pasta `PI4/Backend/cache/`

Três arquivos Parquet. São cópia já processada do CSV, para o painel não reler 66 MB toda vez. Se o CSV for alterado e ficar com data mais nova, o código regrava estes arquivos. A pasta está no `.gitignore`.

### `cache/cti_limpo.parquet`

4,5 MB. 1.002.000 linhas. 5 colunas:

| Coluna | O que é |
|---|---|
| `ANO` | texto original, `Ano 1` … `Ano 12` |
| `CENA` | `Total Cen_00001` etc. |
| `CONTA` | nome da conta, espaços já normalizados |
| `VALOR` | número de verdade, vírgula brasileira já convertida |
| `ano_num` | inteiro 1 a 12, extraído de `ANO` |

Quem grava: `load_cti_csv` em `Frontend/src/models/loaders.py`. Quem lê de novo: a mesma função, se o Parquet for mais novo que o CSV.

### `cache/indicadores.parquet`

3,0 MB. 14.400 linhas. Isso é 1.200 cenários × 12 anos. 38 colunas.

Identificação: `ANO`, `ano_num`, `CENA`.

Contas somadas a partir do CSV: `ativo_circ`, `contas_receber`, `creditos_tributarios`, `disponivel`, `distribuicao`, `dre_custos`, `dre_receita`, `ebitda`, `emprestimos_cp`, `encargos_sociais`, `estoques`, `fornecedores`, `geracao_caixa`, `investimentos`, `passivo_circ`, `resultado`, `saldo_final`, `total_ativo`, `total_passivo`, `tributos_a_pagar`.

Indicadores calculados: `ACO`, `PCO`, `NCG`, `Saldo_Tesouraria`, `PMR`, `PME`, `PMP`, `Ciclo_Financeiro`, `rentabilidade`, `liquidez`, `risco`, `pressao_invest`, `dist_abs`, `caixa_mag`, `caixa_final_sinal`.

Quem grava: `carregar_pipeline` em `bootstrap.py`, depois de `montar_indicadores`. Os gráficos de evolução (NCG no tempo, prazos, faixa, comparação) leem este quadro.

### `cache/ranking.parquet`

164 KB. 1.200 linhas, uma por cenário. 24 colunas:

`CENA`, `rentabilidade`, `liquidez`, `risco`, `NCG`, `Saldo_Tesouraria`, `Ciclo_Financeiro`, `receita`, `resultado`, `ebitda`, `pressao_invest`, `dist_abs`, `liquidez_acumulada`, `caixa_ano12`, `disponivel_ano12`, `Alta rentabilidade`, `Retorno moderado`, `Alta liquidez`, `Baixa liquidez`, `Baixo risco`, `Alto risco`, `selo`, `ano_encerramento`, `rotulo`.

As colunas com nome de frase (`Alta rentabilidade`, `Baixo risco`…) são verdadeiro ou falso. `selo` é o rótulo final do cenário. `ano_encerramento` é 12. `rotulo` é o nome curto do cenário para a tela.

Quem usa: mapeamento, distribuição, KPIs do topo, e o índice do chat (um parágrafo por linha).

---

## Pasta `PI4/Backend/documentos/`

Textos que o chat pode ler. Hoje só há um arquivo. PDF ou Markdown novos colocados aqui entram na busca, desde que o filtro de transcrição não os descarte.

### `documentos/manual_executivo_cti.md`

47 linhas. Manual curto em Markdown. Seções:

1. Título "Manual executivo CTI — leitura dos cenários". Diz que a base tem cerca de 1.200 cenários em 12 anos, perfil de concessão.
2. "O que o painel responde" — cinco perguntas: NCG, saldo de tesouraria, ciclo financeiro, mapa risco × retorno, chance de caixa negativo.
3. Tabela de fórmulas: NCG, saldo de tesouraria, PMR, PME, PMP, ciclo, liquidez corrente, rentabilidade, risco.
4. Lista dos seis selos de negócio.
5. "Como usar o assistente" — exemplos de pergunta e a indicação de colocar PDFs nesta pasta.

O motor de busca marca os pedaços deste arquivo como tipo `manual_executivo` e dá prioridade a eles na ordenação.

---

## Pasta `PI4/Frontend/`

O site. Streamlit. O pacote Python se chama `src` e mora aqui dentro.

Arquivos na raiz desta pasta:

- `analise.ipynb`
- `app.py`
- `chat_component.py`
- `chat_widget.html`
- `organizando.ipynb`
- `requirements_dashboard.txt`
- pasta `.streamlit/`
- pasta `src/`

### `Frontend/requirements_dashboard.txt`

Pacotes do painel:

- streamlit
- plotly
- pandas
- numpy
- openpyxl
- pyarrow
- seaborn
- matplotlib
- langchain-core
- langchain-text-splitters
- scikit-learn
- faiss-cpu
- google-genai
- pypdf
- python-dotenv

### `Frontend/app.py`

Ponto de entrada do dashboard. O que tem dentro:

- `st.set_page_config` com layout largo, título "Dashboard CTI", ícone de gráfico.
- Um bloco `<style>` que força branco no valor e no rótulo de `st.metric`.
- Dicionário `VIEW_RENDERERS`. Chave da aba → função:
  - `capital_giro` → `views/capital_giro.py`
  - `prazos` → `views/prazos_ciclo.py`
  - `mapeamento` → `views/mapeamento_risco.py`
  - `distribuicao` → `views/distribuicao.py`
  - `faixa` → `views/faixa_risco.py`
  - `comparar` → `views/comparar.py`
  - `como_ler` → `views/como_ler.py`
- `render_analises`: desenha o menu de abas, o expander de auditoria e a view escolhida. Rodapé com `app.footer`.
- `render_pagina`: cabeçalho e depois as análises.
- `main`: idioma, carga dos dados, barra lateral, persona, contexto, página, e por último `render_floating_chat()`.

Sobe com `py -m streamlit run Frontend/app.py` a partir de `PI4`, ou `py -m streamlit run app.py` de dentro de `Frontend`. Porta usual: 8501.

### `Frontend/chat_component.py`

Uma função, `render_floating_chat`. Lê o HTML ao lado e manda o Streamlit desenhar um componente customizado. O CSS deste arquivo prende o container desse componente no canto inferior direito: 380 px de largura, 540 px de altura, `z-index` alto, para o chat ficar por cima dos gráficos sem empurrar o layout.

### `Frontend/chat_widget.html`

Página HTML do chat, sozinha dentro do iframe. Peças:

- `#cti-chat-widget` — caixa que limita o CSS, para o estilo não vazar para o dashboard.
- `#fab` — botão redondo do robô, fixo em baixo à direita. Abre e fecha o painel.
- `#panel` — janela da conversa: título, lista de mensagens, campo de texto, botão enviar.
- JavaScript que faz `POST` em `http://localhost:8000/api/chat` com `message` e `session_id`, e escreve a resposta na lista.

### `Frontend/analise.ipynb`

Notebook Jupyter, cerca de 24 KB. Rascunho de análise da base. O `app.py` não importa este arquivo. Não entra no ar quando o dashboard sobe.

### `Frontend/organizando.ipynb`

Notebook Jupyter, cerca de 38 KB. Nele a base foi separada em balanço, DRE e fluxo de caixa. A função `separar_demonstrativos` em `loaders.py` repete essa separação no código. O dashboard também não importa este notebook.

---

## Pasta `PI4/Frontend/.streamlit/`

Configuração que o Streamlit lê sozinho ao subir `app.py`.

### `.streamlit/config.toml`

Três blocos:

- `[browser]` — `gatherUsageStats = false`
- `[server]` — `headless = true` (não abre o navegador sozinho)
- `[theme]` — `base = "dark"`, cor primária `#1F4E45`, fundo `#0E1117`, fundo secundário `#262730`, texto `#FAFAFA`

### `.streamlit/credentials.toml`

Criado pelo Streamlit. Conteúdo:

```toml
[general]
email = ""
```

Não guarda a chave do Gemini. O e-mail está vazio.

---

## Pasta `PI4/Frontend/src/`

Código do painel, dividido em quatro pastas: `config`, `controllers`, `models`, `views`.

### `src/__init__.py`

Uma linha de docstring: "Pacote raiz do painel CTI." Existe para o Python tratar `src` como pacote.

---

## Pasta `PI4/Frontend/src/config/`

Constantes, frases da tela e textos de ajuda. Não lê o CSV.

### `config/__init__.py`

O que está declarado:

Caminhos:

- `PI4`, `ROOT`, `BACKEND`
- `CSV_PATH` = `Backend/Cti.csv`
- `CACHE_DIR` = `Backend/cache`
- `DOCS_DIR` = `Backend/documentos`
- `REPO_DOCS_DIR` = pasta `documentos` ao lado de `PI4`, na raiz do repositório
- `VENV_PY` = `PI4/.venv/bin/python` (caminho de Linux; nesta máquina o Python é o `py` do Windows)

Cores hex: `COR`, `COR_SUAVE`, `COR_ALERTA`, `COR_OK`, `COR_ANCORA`, `COR_AMARELO`, `COR_LARANJA`, `COR_ROXO`, `COR_VERMELHO`, `COR_VERDE_ESCURO`, `COR_VERDE_CLARO`.

`SELOS_NEGOCIO`: lista com os seis nomes em português.

`CORES_SELO`: um hex para cada selo.

`PERSONAS`: `ceo`, `cfo`, `acionistas`, `docente`.

`NAV_KEYS`: `capital_giro`, `prazos`, `mapeamento`, `distribuicao`, `faixa`, `comparar`, `como_ler`.

`METRICAS_NUVEM`: quatro métricas e se "maior é melhor":

- caixa disponível → coluna `disponivel`, maior é melhor
- geração de caixa → `geracao_caixa`, maior é melhor
- tesouraria → `Saldo_Tesouraria`, maior é melhor
- NCG → `NCG`, maior não é melhor

`CORES_COMPARA`: três cores para as curvas da aba comparar.

`CONTAS_RECEBER`: três contas do balanço que viram a coluna `contas_receber`.

`PECAS_CONTAS`: dicionário do nome interno para a conta do CSV. As chaves são `estoques`, `creditos_tributarios`, `fornecedores`, `encargos_sociais`, `tributos_a_pagar`, `disponivel`, `emprestimos_cp`, `ativo_circ`, `passivo_circ`, `total_ativo`, `total_passivo`, `dre_receita`, `dre_custos`, `resultado`, `ebitda`, `geracao_caixa`, `investimentos`, `distribuicao`, `saldo_final`.

### `config/i18n.py`

Dois dicionários grandes, `STRINGS["pt"]` e `STRINGS["en"]`. Cada chave é um texto da interface. Grupos de chave que existem:

- `lang.*` — rótulo do seletor de idioma
- `persona.*` — CEO, CFO, Acionistas, Poder Docente, e também os rótulos antigos Visão Geral e Poder Concedente
- `nav.*` — nome de cada aba
- `kpi.*` — nome de cada indicador do topo
- `persona.blurb.*` — frase de uma linha embaixo dos KPIs
- `stake.*` — títulos que sobraram da visão exclusiva por perfil (o menu de abas atual não usa esses blocos como página)
- `chart.*`, `table.*` — eixos e percentis
- `txt.ncg.*`, `txt.treasury.*`, `txt.cycle.*`, `txt.bank.*` — frases de alerta
- `map.*` — textos do gráfico de risco × retorno, inclusive `map.focus.ceo`, `.cfo`, `.acionistas`, `.docente`
- `dist.*`, `faixa.*`, `cmp.*`, `ai.*`, `app.footer`, `sidebar.*`, `header.*`, `filter.*`, `fmt.*`, `selo.*`

Funções:

- `get_lang` / `set_lang` — idioma guardado em `st.session_state["lang"]`, padrão `pt`
- `t(chave)` — devolve a frase e preenche `{placeholders}`
- `get_text` — apelido de `t`
- `translate_selo` — troca o nome português do selo pela versão do idioma ativo

### `config/glossary.py`

Dicionário `GLOSSARIO` com as mesmas chaves em `pt` e `en`. São os parágrafos do ícone de interrogação: o que é NCG, tesouraria, ciclo, liquidez, risco, rentabilidade, PMR, PME, PMP, percentis, o que o filtro de ano faz, o que o seletor de persona faz.

Funções: `glossary`, `help_text`, `help_join`. `help_text` devolve `None` se a chave não existir, para o widget não mostrar um `?` vazio.

---

## Pasta `PI4/Frontend/src/models/`

Conta, classifica e formata. Não chama `streamlit` para desenhar aba (o `rag_engine` importa bibliotecas de IA, não widgets).

### `models/__init__.py`

Não importa os módulos na hora em que o pacote abre. Tem `__getattr__`: se alguém pede `src.models.fmt_rs`, aí sim carrega `formatting.py`. O mesmo para funções de `analytics`, `classifiers` e `loaders`. A lista pública está em `__all__`.

### `models/loaders.py`

Funções:

- `parse_valor_br` — tira ponto de milhar e troca vírgula por ponto. `"1.205.264.965,52"` vira número.
- `normalizar_conta` — um espaço só entre as palavras do nome da conta.
- `magnitude` — valor absoluto. O balanço mistura sinal de débito e de crédito.
- `load_cti_csv` — lê `cti_limpo.parquet` se ele for mais novo que o CSV. Senão lê o CSV com `header=None` e nomes `ANO`, `CENA`, `CONTA`, `VALOR`, limpa, cria `ano_num`, grava o Parquet.
- `separar_demonstrativos` — devolve um dicionário com três DataFrames: `BP` (contas `BAL -`), `DRE` (`DRE -`), `DFC` (`FLU -`).
- `soma_contas` — soma uma lista de nomes de conta por ano e cenário.

### `models/analytics.py`

Funções:

- `_mapa_contas` — liga cada string do CSV (`BAL - Disponível`, etc.) ao nome curto (`disponivel`).
- `montar_indicadores` — filtra o CSV nessas contas, faz pivot, preenche zero onde a conta não apareceu, e calcula:
  - `ACO` = clientes + estoques + créditos tributários (em módulo)
  - `PCO` = fornecedores + encargos + tributos (em módulo)
  - `NCG` = ACO − PCO
  - `Saldo_Tesouraria` = disponível − empréstimos de curto prazo
  - `PMR`, `PME`, `PMP` em dias
  - `Ciclo_Financeiro` = PMR + PME − PMP
  - `liquidez` = ativo circulante / passivo circulante
  - `rentabilidade` = resultado / receita
  - `risco` = passivo total / ativo total
  - em seguida chama `classificar_cenarios`
  - devolve a tupla `(indicadores, ranking)`
- `resumo_envelope` — por ano, mínimo, máximo, mediana e média de uma coluna, para a aba faixa de risco
- `resumo_estatistico` — média, mediana, desvio, mínimo, máximo de uma série
- `cenas_por_percentil` — qual cenário cai em cada percentil
- `probabilidade_caixa_negativo` — percentual de cenários com `caixa_ano12` < 0

### `models/classifiers.py`

Uma função, `classificar_cenarios`. Recebe o ranking e devolve o mesmo quadro com colunas booleanas e a coluna `selo`.

Corta a distribuição em quartis de rentabilidade, liquidez e risco, e no percentil 75 de pressão de investimento, distribuição e disponibilidade. Atribui, nesta ordem, um dos seis selos listados em `SELOS_NEGOCIO`. O primeiro critério que bater fica.

### `models/formatting.py`

Funções de texto:

- `fmt_rs` — reais, com "mi" ou "bi" quando o número é grande. Respeita PT/EN.
- `fmt_dias` — "12,3 dias"
- `fmt_pct` — a função espera proporção (0,15 vira 15%). O código multiplica por 100.
- `texto_ncg` — frase se a NCG come caixa, gera caixa ou está zerada
- `texto_tesouraria` — frase se o saldo cobre ou não
- `texto_ciclo` — frase se o ciclo passa de 30 dias, é moderado ou é negativo
- `cena_id` — tira o número de `Total Cen_00001`
- `cena_rotulo` — rótulo mostrado no select
- `cena_sort_key` — ordena cenário 2 antes de cenário 10
- `melhor_entre` — diz qual dos dois números é o melhor, conforme a métrica
- `cenas_padrao_comparacao` — sugere quais cenários já vêm marcados na aba comparar

### `models/rag_engine.py`

Motor de busca e de resposta. O que tem dentro:

Classe `TfidfEmbeddings`: vetor TF-IDF local, até 768 termos, unigramas e bigramas. Não chama API para buscar.

Funções de apoio: `resolve_api_key` (lê `GOOGLE_API_KEY` ou `GEMINI_API_KEY`), `_rs`, `_pct`, `_dias`, `_ler_pdf`.

`_parece_transcricao`: verdadeiro se o nome do arquivo casa com aula, transcrição, reunião, anotação, ou se o começo do texto tem várias marcas de fala ("professor", "né?", "beleza").

`_iter_arquivos_doc`: lista `.md`, `.txt`, `.markdown` e `.pdf` só em `Backend/documentos` e na pasta `documentos` da raiz do repositório. Ignora arquivo maior que 12 MB e o nome placeholder "venha para a fecap!". Não percorre `Estudo_do_caso/`.

`_docs_manuais`: corta esses arquivos em pedaços de 900 caracteres. Pedaço do manual executivo recebe `tipo = manual_executivo`.

`_docs_glossario`: um documento só, com o glossário PT e EN.

`_docs_cenarios`: a partir do ranking, gera

- 1 documento resumo (médias e probabilidade de caixa negativo)
- 1 documento por selo
- 1 documento por cenário (1.200)

`build_focus_context`: parágrafo do cenário e do ano que estão filtrados na tela. A API em `Backend/rag_engine.py` não envia esse parágrafo. O chat em `views/ai_assistant.py` envia.

Classe `RagEngine`:

- `from_ranking` junta cenários + glossário + manuais, vetoriza e monta índice FAISS (se a biblioteca existir; senão compara vetor com numpy)
- `retrieve` busca e depois soma um bônus: manual executivo +0,45, resumo +0,35, selo +0,25, cenário +0,12
- `ask` recupera trechos, junta as fontes, e ou chama o Gemini ou devolve o texto de fallback

`_resposta_extrativa`: título "Trechos Selecionados da Documentação CTI", até quatro parágrafos que contenham NCG, tesouraria, selo, EBITDA, liquidez, caixa, rentabilidade, ciclo, risco ou receita, e a dica da `GOOGLE_API_KEY`.

`_gerar_llm`: tenta `gemini-2.0-flash`, depois `gemini-1.5-flash`, depois `gemini-2.5-flash`. O prompt manda responder só com o contexto, em tom de consultor, priorizando NCG, tesouraria, ciclo e risco.

No import do módulo, `load_dotenv` lê `Backend/.env`, `PI4/.env` e o `.env` da pasta pai do repositório.

---

## Pasta `PI4/Frontend/src/controllers/`

Monta pedaços da página Streamlit: barra, cabeçalho, KPI, gráfico. A conta em si fica em `models`.

### `controllers/__init__.py`

Igual ao de `models`: `__getattr__` carrega a função só quando alguém pede. Expõe funções de `charts`, `headers`, `kpis`, `resilience`, `sidebar` e `render_ai_layout`.

### `controllers/bootstrap.py`

- Classe `AppContext`. Campos: `df`, `ind`, `ranking`, `mapa_rotulo`, `n_cenarios`, `ano_enc`, `p_ruina`, `ano_sel`, `cena_sel`, `anos`, `cenas`, `persona`, `foco`, `foco_ano`, `k`.
- `carregar_pipeline`: se os três Parquet estiverem mais novos que o CSV, lê os três. Senão roda `load_cti_csv` + `montar_indicadores` e grava `indicadores.parquet` e `ranking.parquet`. Decorada com `st.cache_resource`.
- `carregar_estado`: se o CSV não existir, mostra erro e devolve `None`.
- `montar_contexto`: filtra `ind` no cenário escolhido e, se o ano não for "Todos", naquele ano. Tira a média das colunas de KPI que existirem. A lista média é NCG, Saldo de Tesouraria, Ciclo, PMR, PME, PMP, liquidez, rentabilidade, risco, resultado, ebitda, dre_receita.
- `render_cabecalho`: título, subtítulo com o cenário, banner de auditoria, frase "média de todos os anos" ou "média do ano N", a fileira de KPIs da persona, e `st.info` com `persona.blurb.<persona>`. Se a persona for `cfo`, ainda mostra as frases de NCG, tesouraria e ciclo.

### `controllers/sidebar.py`

- `render_language_selector`: select na barra, opções vindas de `LANG_OPTIONS`. Se mudar, grava o idioma e faz `st.rerun`.
- `render_sidebar`: select de ano (valor interno `__all__` para "Todos") e select de cenário. Embaixo, nome do CSV, quantidade de linhas, de cenários e de anos. Devolve ano, cenário, lista de anos e lista de cenários.
- `render_persona`: controle segmentado com os quatro rótulos. Guarda o id em `st.session_state["persona_id"]`. Se achar `geral`, troca para `ceo`. Se achar `concedente`, troca para `docente`. A chave do widget é `persona_visao_v2_` mais o idioma, para não reaproveitar o controle antigo.

### `controllers/kpis.py`

- Constante CSS `_KPI_FORCE_CSS` para cor branca do `st.metric`.
- `card_selo_html`: HTML de um cartão com a cor do selo, o nome traduzido e a quantidade de cenários.
- `kpis_por_persona`:
  - `ceo`: probabilidade de caixa negativo (percentual de `caixa_ano12` < 0), rentabilidade média do ranking, selo mais frequente
  - `cfo`: NCG, tesouraria, ciclo, liquidez, formatados, com texto de ajuda
  - `acionistas`: margem EBITDA (ebitda / receita), rentabilidade média como "retorno esperado", selo cuja rentabilidade média é a maior
  - qualquer outro id, na prática `docente`: quantidade de linhas do ranking, ano de encerramento, R² (correlação de EBITDA com resultado, ao quadrado), coeficiente de variação do caixa do ano 12
- `render_metric_card` e `render_kpi_row`: desenham `st.metric`. O `help` do metric é o tooltip.

### `controllers/charts.py`

Funções que devolvem figura Plotly ou preparam a tabela do gráfico:

- `recorte_label` — "Todos" ou o número do ano, no idioma ativo
- `titulo_filtro` — assunto + cenário + ano, para o título do gráfico
- `serie_temporal_plotavel` — fica só com `ano_num` e as colunas pedidas, ordenado, sem linha sem ano
- `ancorar_ano_temporal` — marca o ano filtrado na linha
- `figura_envelope` — faixa entre cenários (pior, mediana, melhor) ao longo dos anos
- `figura_histograma_ano` — histograma de uma métrica num ano
- `figura_histograma_caixa_final` — histograma do caixa do ano 12

### `controllers/headers.py`

- `recorte_label` — o mesmo papel do de charts, para o banner
- `banner_auditoria_filtro` — faixa no topo dizendo qual cenário e qual ano estão ativos
- `expander_auditoria_base` — sanfona com uma amostra da base bruta naquele filtro
- `render_titulo` — título principal do painel
- `heading_with_help` — título de seção mais o `?` do glossário

### `controllers/resilience.py`

- `safe_render(rótulo, função, argumentos)`: executa a função. Se der erro, mostra `st.error` com o tipo da exceção e uma sanfona com o traceback. O resto da página segue.
- `resilient_view(rótulo)`: decorador que faz a mesma coisa em volta do `render` de uma aba.

### `controllers/ai_sidebar_right.py`

Painel de chat como coluna à direita, não como botão flutuante. Funções: `_painel_aberto`, `_abrir`, `render_ai_layout`. O CSS fixa uma alça na borda direita. O `app.py` atual não chama `render_ai_layout`. Quem abre o chat na tela é `chat_component.py`. Este arquivo continua no projeto e é exportado por `controllers/__init__.py`.

---

## Pasta `PI4/Frontend/src/views/`

Uma aba da tela por arquivo. Quase todos têm uma função `render`, protegida por `@resilient_view`.

### `views/__init__.py`

Importa os oito módulos: `ai_assistant`, `capital_giro`, `comparar`, `como_ler`, `distribuicao`, `faixa_risco`, `mapeamento_risco`, `prazos_ciclo`. O `__all__` repete esses nomes. `app.py` não usa este `__init__` para achar as abas; ele importa cada módulo pelo nome.

### `views/capital_giro.py`

Aba Capital de giro.

- `_grafico_evolucao`: linha de NCG e de saldo de tesouraria nos 12 anos do cenário filtrado.
- `_grafico_composicao`: barras do que compõe o giro naquele ano (as peças do ativo e do passivo operacional que existem no recorte).
- `render(foco, foco_ano, cena_sel, ano_sel)`: título com ajuda e os dois gráficos.

### `views/prazos_ciclo.py`

Aba Prazos e ciclo.

- `_grafico_prazos`: linhas de PMR, PME, PMP e ciclo financeiro.
- `render`: quatro `render_metric_card` (os quatro prazos) e o gráfico.

### `views/mapeamento_risco.py`

Aba Mapeamento de risco × retorno.

- `_scatter`: gráfico de pontos. X = `risco`, Y = `rentabilidade`, cor = `selo`, usando `CORES_SELO`.
- `render`: cartões com a contagem de cada selo, o scatter, busca de um cenário, e um comparativo do cenário escolhido com outro. A legenda de ênfase sai de `map.focus.<persona>`.

### `views/distribuicao.py`

Aba Distribuição e probabilidades.

- `_boxplot`: caixa do caixa no ano de encerramento, com os quartis.
- `render`: cards (probabilidade de caixa negativo e leitura de percentis), histograma vindo de `figura_histograma_caixa_final`, e o boxplot. Os textos `dist.*` falam da cauda P5/P95.

### `views/faixa_risco.py`

Aba Faixa de risco.

- `render`: select da métrica (`METRICAS_NUVEM`), cards de mediana, média, pior e melhor (`resumo_envelope`), o gráfico envelope e o histograma de um ano.

### `views/comparar.py`

Aba Comparar cenários.

- `render`: multiselect de 2 ou 3 cenários, select da métrica, linhas sobrepostas com `CORES_COMPARA`, e cards lado a lado (caixa, NCG, tesouraria, liquidez, ciclo) de cada cenário escolhido.

### `views/como_ler.py`

Aba Como ler estes números.

- `render`: só texto. Usa `n_cenarios`, o rótulo do cenário, a série `k`, o ano de encerramento e `p_ruina` para preencher as frases do i18n. Não cria gráfico.

### `views/ai_assistant.py`

Chat desenhado com widgets do Streamlit, não com o HTML flutuante. Funções:

- `_fingerprint`: string com a quantidade de cenários e a média do caixa, para invalidar o cache se o ranking mudar.
- `_carregar_engine`: `RagEngine.from_ranking`, com `st.cache_resource`.
- `_chave_api`: procura a chave na sessão, no ambiente e no `secrets.toml`.
- `_contexto_foco`: chama `build_focus_context` com o cenário e o ano da tela.
- `render_chat_panel`: histórico na sessão, campo de pergunta, resposta, lista de fontes.
- `render_chat` e `render`: atalhos para o mesmo painel.

`app.py` não coloca esta view no menu de abas. `ai_sidebar_right.py` é quem a chama. O botão do robô que está no ar usa o HTML e a porta 8000, e portanto passa por `Backend/rag_engine.py`, que usa o mesmo `RagEngine` mas sem o contexto do filtro da tela.
