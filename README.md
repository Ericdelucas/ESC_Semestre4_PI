# FECAP - Fundação de Comércio Álvares Penteado

<p align="center">
<a href= "https://www.fecap.br/"><img src="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRhZPrRa89Kma0ZZogxm0pi-tCn_TLKeHGVxywp-LXAFGR3B1DPouAJYHgKZGV0XTEf4AE&usqp=CAU" alt="FECAP - Fundação de Comércio Álvares Penteado" border="0"></a>
</p>

# ESC


## Integrantes: <a href="https://www.linkedin.com/in/eric-de-lucas-silva/">Eric De Lucas Silva</a>, <a href="https://www.linkedin.com/in/stephanie-macedo-da-silva/">Stephanie Macedo da Silva</a> e <a href="https://www.linkedin.com/in/en-hsiang-chien-53b550381/">En Hsiang Chien</a>.

## Professores Orientadores: <a href="https://www.linkedin.com/in/eduardo-savino/">Eduardo Savino Gomes</a>, <a href="https://www.linkedin.com/in/luisspires/">Luis Fernando dos Santos Pires</a>, <a href="https://www.linkedin.com/in/professorrodnil/">Rodnil da Silva Moreira Lisboa</a> e <a href="https://www.linkedin.com/in/victorbarq/">Mauricio Lopes Da Cunha</a>.

## Descrição
<p align="center">
<a href="https://ibb.co/Q77D4spN"><img src="https://i.ibb.co/0ppsxPmM/Captura-de-tela-2026-10-20-210842.png" alt="Captura-de-tela-2026-10-20-210842" border="0"> </a>
Imagem do dashboard
</p>
<br>

O projeto ESC consiste no desenvolvimento de um dashboard preditivo e simulador de cenários financeiros criado em Python para otimizar a gestão e análise de riscos da CTI. A solução centraliza dados dispersos e substitui rotinas manuais por um dashboard integrado, ágil e visual.

Na prática, a ferramenta automatiza o cálculo de indicadores essenciais como DRE, fluxo de caixa, liquidez e ponto de equilíbrio e permite simular diferentes cenários operacionais em tempo real. Além disso, oferece visões personalizadas por perfil de usuário (como CEO e CFO) e conta com um assistente de inteligência artificial para apoiar a diretoria na tomada de decisões estratégicas de forma rápida.
<br>

## 🛠 Estrutura de pastas

<h3>Frontend</h3>
<details>
<summary><strong>clique aqui para ver o Tree</strong></summary>
<pre>
├── Frontend
│   ├── analise.ipynb
│   ├── app.py
│   ├── chat_component.py
│   ├── chat_widget.html
│   ├── organizando.ipynb
│   ├── Procfile
│   ├── __pycache__
│   │   └── chat_component.cpython-314.pyc
│   ├── requirements_dashboard.txt
│   ├── requirements.txt
│   └── src
│       ├── components
│       │   ├── header_component.py
│       │   ├── __init__.py
│       │   ├── kpi_cards_component.py
│       │   └── sidebar_filters.py
│       ├── config
│       │   ├── glossary.py
│       │   ├── i18n.py
│       │   ├── __init__.py
│       │   └── __pycache__
│       ├── controllers
│       │   ├── ai_sidebar_right.py
│       │   ├── auth.py
│       │   ├── bootstrap.py
│       │   ├── charts
│       │   ├── custom_analysis.py
│       │   ├── data_input.py
│       │   ├── headers.py
│       │   ├── __init__.py
│       │   ├── kpis
│       │   ├── local_api.py
│       │   ├── modals.py
│       │   ├── navigation.py
│       │   ├── ops_menu.py
│       │   ├── page_setup.py
│       │   ├── __pycache__
│       │   ├── resilience.py
│       │   ├── session_cookie.py
│       │   ├── sidebar.py
│       │   ├── stability.py
│       │   └── test_sandbox.py
│       ├── __init__.py
│       ├── models
│       │   ├── analytics
│       │   ├── api_client.py
│       │   ├── classifiers.py
│       │   ├── financial_metrics
│       │   ├── formatting
│       │   ├── __init__.py
│       │   ├── loaders.py
│       │   ├── __pycache__
│       │   └── rag_engine
│       ├── __pycache__
│       │   └── __init__.cpython-314.pyc
│       └── views
│           ├── ai_assistant
│           ├── capital_giro.py
│           ├── como_ler.py
│           ├── comparar.py
│           ├── distribuicao.py
│           ├── faixa_risco.py
│           ├── __init__.py
│           ├── mapeamento_risco.py
│           ├── persona_tabs
│           ├── prazos_ciclo.py
│           ├── __pycache__
│           └── report.py
</details>
</pre>

<h3>Backend</h3>
<details>
<summary><strong>clique aqui para ver o Tree</strong></summary>
<pre>
│   ├── Backend
│   │   ├── audit
│   │   ├── cache
│   │   ├── Cti.csv
│   │   ├── data_audit.py
│   │   ├── data_loader
│   │   ├── db
│   │   ├── diag.py
│   │   ├── documentos
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── metrics
│   │   ├── Procfile
│   │   ├── __pycache__
│   │   ├── rag_engine.py
│   │   ├── README.md
│   │   ├── relatorios
│   │   ├── render.yaml
│   │   ├── requirements.txt
│   │   ├── routers
│   │   ├── runtime.py
│   │   ├── scripts
│   │   ├── services
│   │   └── tests
</details>
</pre>
<br>

## 🛠 Instalação

<h2>Site:</h2>
<p><a href= "https://esc-semestre4-pi.onrender.com/">Click aqui para ir no site</a>
</p>
<br>

## 📖 Tutorial de como acessar o dashboard

<h3>1. Acesso ao repositório</h3>
<li>Acesse o repositório no README do GitHub</li>
<li>Navegue até a "🛠instalação" localize o link do site.</li>

<h3>2. Criação de conta</h3>
<li>Na tela inicial, selecione a opção “Cadastrar”</li>
<li>Preencha os campos solicitados (ex: e-mail, senha...)</li>
<li>Confirme o cadastro</li>

<h3>3. Login no sistema</h3>
<li>Retorne à tela de login</li>
<li>Insira e-mail e senha cadastrados</li>
<li>Clique em “Entrar”</li>
<br>

## 🎥Demonstração do Projeto

<p><a href= "https://drive.google.com/file/d/1Ujb5-lE7LsLN3bLuT_D8wTVIMSdrcVOs/view?usp=sharing">Click aqui para ver o vídeo</a>
<p>Assista ao vídeo abaixo para uma demonstração do dashboard e todas as suas funcionalidades.</p>

---

## 🛠️ Como Rodar o Projeto

### Prerequisitos e Ferramentas Necessárias

Antes de começar, certifique-se de ter as seguintes ferramentas instaladas em seu ambiente:

* [Visual Studio Code](https://code.visualstudio.com/) (Editor de código recomendado)
* [Python 3.10+](https://www.python.org/) (Necessário para o motor FastAPI e Streamlit)
* [Node.js](https://nodejs.org/) (Caso utilize dependências web auxiliares)
* [Git](https://git-scm.com/) (Para controle de versão)

---

### Passo a Passo para Execução

1. **Clonar e acessar o repositório:**
   ```bash
   git clone <https://github.com/Ericdelucas/ESC_Semestre4_PI.git>
   cd PI4

   Configurar o ambiente virtual Python:
Bash

python -m venv .venv

# No Linux / macOS:
source .venv/bin/activate

# No Windows (PowerShell):
.\.venv\Scripts\Activate.ps1

Instalar as dependências:
Bash

pip install -r requirements.txt

Configurar as variáveis de ambiente:
Certifique-se de que o arquivo .env esteja configurado na raiz do projeto (utilize o .env.example como modelo de referência, se necessário).

Executar a aplicação:

    Execução automática via script:
    Bash

    bash start.sh

    Ou execução manual dos serviços:

        Backend (FastAPI): uvicorn Backend.main:app --reload

        Frontend (Streamlit): streamlit run main.py

## 💻 Configuração para Desenvolvimento

## Passo a passo para iniciar

Abra dois terminais na raiz do repositório (`ESC_Semestre4_PI`) e entre na pasta `PI4` em cada um com `cd PI4`. Depois disso, execute os comandos abaixo dentro de `PI4`.

### 1. Entrar na pasta do projeto( Só para)

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

### 4. Ligar o backend — API FastAPI (terminal 1)

```bash
py -m uvicorn Backend.main:app --host 127.0.0.1 --port 8000
```

Confirme em [http://localhost:8000/](http://localhost:8000/) ou [http://localhost:8000/api/v1/health](http://localhost:8000/api/v1/health). A resposta esperada é `{"status":"online","message":"API CTI Backend Ativa"}`. Deixe esse terminal aberto.

### 5. Ligar o frontend — dashboard Streamlit (terminal 2)

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

<de>

## Estrutura

```
PI4/
  Backend/     # FastAPI, Cti.csv, documentos, cache
  Frontend/    # Streamlit, src (config, controllers, models, views)
```

## Comandos rápidos para ligar o projeto

Após instalar as dependências, abra dois terminais na raiz do repositório.

**Terminal 1 — backend:**

```powershell
cd PI4
py -m uvicorn Backend.main:app --host 127.0.0.1 --port 8000
```

**Terminal 2 — frontend:**

```powershell
cd PI4
py -m streamlit run Frontend/app.py
```
<details>
<summary><strong>Windows/linux/macOS</strong></summary>
<pre>
Configurar o ambiente virtual Python:
Bash

python -m venv .venv

# No Linux / macOS:
source .venv/bin/activate

# No Windows (PowerShell):
.\.venv\Scripts\Activate.ps1

Instalar as dependências:
Bash

pip install -r requirements.txt

Configurar as variáveis de ambiente:
Certifique-se de que o arquivo .env esteja configurado na raiz do projeto (utilize o .env.example como modelo de referência, se necessário).

Executar a aplicação:

    Execução automática via script:
    Bash

    bash start.sh

    Ou execução manual dos serviços:

        Backend (FastAPI): uvicorn Backend.main:app --reload

        Frontend (Streamlit): streamlit run main.py
</pre>
</details>

## 📋 Licença/License
<a href="https://github.com/2026-2-NCC4/Projeto8">ESC</a> © 2026 by <a href="https://www.linkedin.com/in/eric-de-lucas-silva/">Eric de Lucas Silva</a>,
<a href ="https://www.linkedin.com/in/stephanie-macedo-da-silva/">Stephanie Macedo da Silva</a>, 
<a href="https://www.linkedin.com/in/en-hsiang-chien-53b550381/">En Hsiang Chien</a> e
<a href= "https://www.linkedin.com/school/fecap/posts/?feedView=all"> FECAP </a> is licensed under <a href="https://creativecommons.org/licenses/by/4.0/">CC BY 4.0</a><img src="https://mirrors.creativecommons.org/presskit/icons/cc.svg" alt="" style="max-width: 1em;max-height:1em;margin-left: .2em;"><img src="https://mirrors.creativecommons.org/presskit/icons/by.svg" alt="" style="max-width: 1em;max-height:1em;margin-left: .2em;">

## 🎓 Referências

Aqui estão as referências usadas no projeto.

1. <https://ctiglobal.com/>
2. <https://repositorio.ufersa.edu.br/bitstreams/6e642d4f-ce5d-4270-b88a-e4cf1caf7f6d/download>
3. <https://repositorio.ufsc.br/bitstream/handle/123456789/274297/O%20Papel%20dos%20Dashboards%20no%20FP&A%20Estrat%C3%A9gico%20Evid%C3%AAncias%20de%20um%20Estudo%20de%20Casos%20M%C3%BAltiplos.pdf?sequence=1>