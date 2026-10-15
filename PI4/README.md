# ESC_Semestre4_PI · PI4

Painel financeiro CTI. O dashboard fica em `Frontend` e a API do chat em `Backend`.

A [documentação técnica da Entrega 2](DOCUMENTATION.md) apresenta arquitetura, pipeline de dados, fórmulas dos indicadores e limitações da infraestrutura.

## Passo a passo para iniciar

Abra dois terminais. Os comandos abaixo partem da pasta `PI4`.

### 1. Entrar na pasta do projeto

```bash
cd PI4
```

### 2. Instalar as dependências

```bash
py -m pip install -r Frontend/requirements_dashboard.txt
py -m pip install -r Backend/requirements.txt
```

### 3. Configurar a chave da IA (opcional)

Sem a chave o chat ainda responde com trechos dos documentos. Com a chave, o Gemini gera a resposta.

```bash
copy .env.example .env
```

Abra `PI4/.env` e preencha:

```text
GOOGLE_API_KEY=sua_chave_aqui
```

A chave sai do [Google AI Studio](https://aistudio.google.com/apikey).

### 4. Subir a API do chat (terminal 1)

```bash
py -m uvicorn Backend.main:app --host 127.0.0.1 --port 8000
```

Confirme em [http://localhost:8000/](http://localhost:8000/) ou [http://localhost:8000/api/v1/health](http://localhost:8000/api/v1/health). A resposta esperada é `{"status":"online","message":"API CTI Backend Ativa"}`. Deixe esse terminal aberto.

### 5. Subir o dashboard (terminal 2)

```bash
py -m streamlit run Frontend/app.py
```

Ou, de dentro de `Frontend`:

```bash
cd Frontend
py -m streamlit run app.py
```

### 6. Abrir no navegador

O Streamlit mostra o endereço, em geral [http://localhost:8501](http://localhost:8501).

O chat é o botão do robô no canto inferior direito. Ele envia as perguntas para `http://localhost:8000/api/chat`. A primeira pergunta demora mais, porque o índice dos cenários é montado nesse momento.

PDFs e Markdown extras para o assistente ficam em `Backend/documentos/` (incluindo subpastas). O índice RAG varre `**/*.md` e `**/*.pdf`.

## Estrutura

```
PI4/
  Backend/     # FastAPI, Cti.csv, documentos, cache
  Frontend/    # Streamlit, src (config, controllers, models, views)
```

### para rodar tudo de uma vez em computador novo

```
cd PI4
py -m pip install -r Frontend/requirements_dashboard.txt
py -m pip install -r Backend/requirements.txt
copy .env.example .env
py -m uvicorn Backend.main:app --host 127.0.0.1 --port 8000
py -m streamlit run Frontend/app.py
```



```
cd PI4
copy .env.example .env
py -m uvicorn Backend.main:app --host 127.0.0.1 --port 8000
py -m streamlit run Frontend/app.py
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
