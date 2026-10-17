# ESC_Semestre4_PI · PI4

Painel financeiro CTI. O dashboard fica em `Frontend` e a API do chat em `Backend`.

A [documentação técnica da Entrega 2](DOCUMENTATION.md) apresenta arquitetura, pipeline de dados, fórmulas dos indicadores e limitações da infraestrutura.

## Passo a passo para iniciar no Linux

Use `python3` para criar o ambiente e o Python desse ambiente para instalar e executar.
No Linux, `py` pode ser outro programa e não aceitar `-m`.

### 1. Entrar na pasta do projeto

A partir da raiz do repositório:

```bash
cd PI4
```

Se o terminal já está em `ESC_Semestre4_PI/PI4`, continue dali, sem repetir `cd PI4`.

### 2. Preparar o ambiente e instalar as dependências

```bash
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r Frontend/requirements.txt
```

`Frontend/requirements.txt` já inclui `Backend/requirements.txt`, instalando as
dependências dos dois serviços. A instalação precisa de acesso à internet.

Se a criação do ambiente falhar com `ensurepip is not available`, instale o
suporte a ambientes virtuais no Ubuntu/Debian e repita os três comandos acima:

```bash
sudo apt update
sudo apt install python3-venv
```

Se a mensagem do Python pedir um pacote específico, como `python3.14-venv`,
instale a versão indicada. Um ambiente criado com `--without-pip` também precisa
desse suporte: depois da instalação, execute novamente `python3 -m venv .venv`.

### 3. Subir a API (terminal 1, dentro de PI4)

```bash
.venv/bin/python -m uvicorn Backend.main:app --host 127.0.0.1 --port 8000
```

Deixe esse terminal aberto. Confira [http://localhost:8000/](http://localhost:8000/):
a resposta esperada é `{"status":"online","message":"API CTI Backend Ativa"}`.
O diagnóstico detalhado fica em [http://localhost:8000/api/v1/health](http://localhost:8000/api/v1/health)
e pode informar `degraded` quando alguma dependência estiver indisponível.

### 4. Subir o dashboard (terminal 2, também dentro de PI4)

Abra outro terminal na pasta `PI4` e execute:

```bash
.venv/bin/python -m streamlit run Frontend/app.py --server.address 127.0.0.1 --server.port 8501
```

Abra [http://localhost:8501](http://localhost:8501). Os dois processos precisam
continuar rodando; `Ctrl+C` encerra o serviço no respectivo terminal. Não cole os
dois comandos de inicialização em sequência no mesmo terminal: o primeiro fica
ocupado executando a API.

O chat é o botão do robô no canto inferior direito. Ele envia as perguntas para
`http://localhost:8000/api/chat`. A primeira pergunta pode demorar mais durante a
preparação do índice. Se houver `BACKEND_URL`, `API_URL` ou `CTI_API_URL` configurada,
confira se aponta para a API local durante o desenvolvimento.

PDFs e Markdown extras para o assistente ficam em `Backend/documentos/`
(incluindo subpastas). O índice RAG varre `**/*.md` e `**/*.pdf`.

## Para iniciar nas próximas vezes

Com as dependências instaladas, execute somente os comandos abaixo. Os dois
terminais devem estar na pasta `PI4`; não é necessário ativar a `.venv`, pois os
comandos já usam o Python dela diretamente.

**Terminal 1 — backend:**

```bash
.venv/bin/python -m uvicorn Backend.main:app --host 127.0.0.1 --port 8000
```

**Terminal 2 — frontend:**

```bash
.venv/bin/python -m streamlit run Frontend/app.py --server.address 127.0.0.1 --server.port 8501
```

**Dashboard:** http://localhost:8501

**API:** http://localhost:8000

### Configurar a chave da IA (opcional)

Sem a chave o chat ainda responde com trechos dos documentos. Com a chave, o Gemini gera a resposta.
Copie o exemplo somente se ainda não tiver `.env`, preservando configurações existentes:

```bash
cp -n .env.example .env
```

Abra `PI4/.env` e preencha:

```text
GOOGLE_API_KEY=sua_chave_aqui
```

A chave sai do [Google AI Studio](https://aistudio.google.com/apikey).

## Diagnóstico rápido

Execute dentro de `PI4`:

```bash
.venv/bin/python --version
.venv/bin/python -m pip --version
.venv/bin/python -m pip check
```

- `No module named pip`: conclua a preparação do ambiente na etapa 2.
- `No module named fastapi`, `uvicorn` ou `streamlit`: repita a instalação da etapa 2.
- `Address already in use`: já existe um processo usando a porta indicada;
  encerre o servidor anterior com `Ctrl+C` no terminal em que foi iniciado.
- Erro de instalação de uma dependência: guarde a primeira mensagem de erro do
  `pip`; trocar apenas o comando de inicialização não resolve uma instalação incompleta.

## Memorial técnico dinâmico no dashboard

Com a API e o Streamlit ativos, selecione cenário e ano no dashboard e abra
**Criar Relatório → Memorial técnico CTI → Gerar Memorial CTI (PDF)**.
Depois clique em **Baixar Memorial CTI**. O relatório executivo personalizado
continua disponível na opção ao lado.

O frontend chama `POST /api/v1/relatorio/memorial` com JSON, por exemplo:

```json
{"scenario": "Total Cen_00001", "year": 1}
```

Use `"scenario": "Todos"` para médias por ano/conta e `"year": null` para
apresentar todos os anos separadamente. A API lê a base ativa do pipeline
CSV/Parquet, recalcula os indicadores por requisição e responde
`application/pdf` com `Content-Disposition: attachment`. Não depende de PDF
pré-gerado nem grava o arquivo em disco. Trocar filtros invalida o download
anterior no painel. O layout segue o modelo do professor, sem seus dados.

O memorial inclui DRE/KPIs, cenários e eficiência comercial, risco consolidado
e solvência/retorno. A seção de risco usa todos os cenários; as demais seguem
os filtros enviados. Fontes de dados, registros, horizonte e filtros aparecem
no cabeçalho. Bases importadas somente no Streamlit devem usar o relatório
executivo personalizado; o memorial da API usa a base CTI do servidor.

Na Render, gere o cache também no serviço do Backend caso não esteja incluído
no artefato: `python Backend/scripts/precompute_cache.py` após a instalação.
O novo endpoint depende do pipeline analítico no próprio serviço da API.

## Relatório da varredura de riscos

No menu `⋮`, execute **Varrer Riscos do Modelo Financeiro**. Após o resultado,
clique em **Gerar relatório da varredura (PDF)** e em **Baixar relatório de riscos**.
O PDF apresenta os valores da varredura e as faixas favoráveis, de atenção e
críticas, sem alterar métricas nem enviar e-mail. A simulação de envio não é
usada para classificar o risco financeiro.

A cópia gerada nesta entrega está em
`Backend/relatorios/Relatorio_Riscos_Financeiros_CTI.pdf`.
O download pelo painel usa o resultado da varredura em memória.

## Estrutura

```text
PI4/
  Backend/     # FastAPI, Cti.csv, documentos, cache
  Frontend/    # Streamlit, src (config, controllers, models, views)
```

## Deploy na Render

O `render.yaml` na raiz define dois Web Services independentes, ambos com
**Root Directory `PI4`**. O Frontend ainda importa modulos e dados de `Backend`
para os calculos locais; por isso, nao use `PI4/Frontend` como Root Directory.
A Render nao disponibiliza arquivos fora do Root Directory:
https://render.com/docs/monorepo-support

| Servico | Build Command | Start Command |
| --- | --- | --- |
| Backend | `pip install -r Backend/requirements.txt` | `cd Backend && uvicorn main:app --host 0.0.0.0 --port $PORT` |
| Frontend | `pip install -r Frontend/requirements.txt && python Backend/scripts/precompute_cache.py` | `cd Frontend && streamlit run app.py --server.port $PORT --server.address 0.0.0.0` |

O precompute gera o cache no proprio servico do Frontend, sem depender do disco
do Backend. Os arquivos `Cti.csv`, `documentos/` e `cache/` usam caminhos baseados
em `__file__`, independentes do diretorio de execucao.

No painel Render, configure:

- **Frontend:** `BACKEND_URL=https://<seu-backend>.onrender.com`.
  `API_URL` e `CTI_API_URL` tambem sao aceitos, nessa ordem de prioridade apos
  `BACKEND_URL`. Sem configuracao, usa `http://localhost:8000`.
- **Backend:** `FRONTEND_URL=https://<seu-frontend>.onrender.com`.
  `CORS_ORIGINS` aceita outras origens separadas por virgula. O CORS existente
  continua aceitando HTTPS em `*.onrender.com` e origens locais.
- Configure as variaveis de banco, IA e SMTP necessarias no servico que as usa.
  Nao commite `.env`. Variaveis do painel tem prioridade sobre os arquivos `.env`.

Para publicar somente a API com Root Directory `PI4/Backend`, use Build
`pip install -r requirements.txt` e Start
`uvicorn main:app --host 0.0.0.0 --port $PORT`.
O `Backend/Procfile` e o `Backend/render.yaml` documentam essa alternativa.

Verifique o Backend em `/api/v1/health` e o Frontend em `/_stcore/health`.
O `start.sh` e o `Procfile` da raiz permanecem como alternativa legada de
servico unificado; nao sao usados pelo novo blueprint.
