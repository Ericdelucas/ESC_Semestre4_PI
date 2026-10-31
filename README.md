# FECAP - Fundação de Comércio Álvares Penteado

<p align="center">
<a href="https://www.fecap.br/"><img src="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRhZPrRa89Kma0ZZogxm0pi-tCn_TLKeHGVxywp-LXAFGR3B1DPouAJYHgKZGV0XTEf4AE&usqp=CAU" alt="FECAP - Fundação de Comércio Álvares Penteado" border="0"></a>
</p>

# ESC

---

## Integrantes: <a href="https://www.linkedin.com/in/eric-de-lucas-silva/">Eric De Lucas Silva</a>, <a href="https://www.linkedin.com/in/stephanie-macedo-da-silva/">Stephanie Macedo da Silva</a> e <a href="https://www.linkedin.com/in/en-hsiang-chien-53b550381/">En Hsiang Chien</a>.

## Professores Orientadores: <a href="https://www.linkedin.com/in/eduardo-savino/">Eduardo Savino Gomes</a>, <a href="https://www.linkedin.com/in/luisspires/">Luis Fernando dos Santos Pires</a>, <a href="https://www.linkedin.com/in/professorrodnil/">Rodnil da Silva Moreira Lisboa</a> e Mauricio Lopes Da Cunha.

---

## Descrição

<p align="center">
<a href="https://ibb.co/Q77D4spN"><img src="https://i.ibb.co/0ppsxPmM/Captura-de-tela-2026-10-20-210842.png" alt="Captura-de-tela-2026-10-20-210842" border="0"></a><br>
Imagem do dashboard
</p>

O projeto ESC consiste no desenvolvimento de um dashboard preditivo e simulador de cenários financeiros criado em Python para otimizar a gestão e análise de riscos da CTI. A solução centraliza dados dispersos e substitui rotinas manuais por um dashboard integrado, ágil e visual.

Na prática, a ferramenta automatiza o cálculo de indicadores essenciais como DRE, fluxo de caixa, liquidez e ponto de equilíbrio e permite simular diferentes cenários operacionais em tempo real. Além disso, oferece visões personalizadas por perfil de usuário (como CEO e CFO) e conta com um assistente de inteligência artificial para apoiar a diretoria na tomada de decisões estratégicas de forma rápida.

* 🌐 **Acesse o sistema online:** [Clique aqui para ir ao dashboard (Render)](https://esc-semestre4-pi.onrender.com/)
* 🎥 **Demonstração em Vídeo:** [Assistir ao vídeo explicativo no Google Drive](https://drive.google.com/file/d/1Ujb5-lE7LsLN3bLuT_D8wTVIMSdrcVOs/view?usp=sharing)

---

## 🛠 Estrutura de Pastas
<pre>
C:.
├───documentos
│   ├───Entrega 1
│   │   ├───Análise Inferencial de Dados
│   │   ├───Contabilidade e Finanças
│   │   ├───Engenharia de Software e Arquitetura de Sistemas
│   │   │   └───ES e ML
│   │   └───Projeto Interdisciplinar Ciência de Dados
│   └───Entrega 2
│       ├───Análise Inferencial de Dados
│       ├───Contabilidade e Finanças
│       ├───Engenharia de Software e Arquitetura de Sistemas
│       └───Projeto Interdisciplinar Ciência de Dados
├───imagens
└───src
    ├───Entrega 1
    │   ├───Backend
    │   │   ├───cache
    │   │   └───documentos
    │   └───Frontend
    │       ├───.streamlit
    │       └───src
    │           ├───config
    │           ├───controllers
    │           ├───models
    │           └───views
    └───Entrega 2
        ├───Backend
        │   ├───audit
        │   ├───cache
        │   ├───data_loader
        │   │   └───__pycache__
        │   ├───db
        │   │   └───__pycache__
        │   ├───documentos
        │   │   ├───balanco
        │   │   ├───cenarios
        │   │   ├───dre
        │   │   ├───fluxo_caixa
        │   │   ├───graficos
        │   │   ├───ia
        │   │   ├───indicadores
        │   │   └───visao_geral
        │   ├───metrics
        │   │   └───__pycache__
        │   ├───relatorios
        │   ├───routers
        │   │   └───__pycache__
        │   ├───scripts
        │   ├───services
        │   │   └───__pycache__
        │   ├───tests
        │   │   └───__pycache__
        │   └───__pycache__
        └───Frontend
            ├───.streamlit
            ├───src
            │   ├───components
            │   │   ├───formula_blocks
            │   │   └───__pycache__
            │   ├───config
            │   │   └───__pycache__
            │   ├───controllers
            │   │   ├───charts
            │   │   │   └───__pycache__
            │   │   ├───kpis
            │   │   │   └───__pycache__
            │   │   └───__pycache__
            │   ├───models
            │   │   ├───analytics
            │   │   │   └───__pycache__
            │   │   ├───financial_metrics
            │   │   │   └───__pycache__
            │   │   ├───formatting
            │   │   │   └───__pycache__
            │   │   ├───rag_engine
            │   │   │   └───__pycache__
            │   │   └───__pycache__
            │   ├───views
            │   │   ├───ai_assistant
            │   │   │   └───__pycache__
            │   │   ├───persona_tabs
            │   │   │   └───__pycache__
            │   │   └───__pycache__
            │   └───__pycache__
            └───__pycache__
</pre>


<details>
<summary><strong>Frontend</strong> (clique para ver a árvore)</summary>
<pre>
├── Frontend
│   ├── analise.ipynb
│   ├── app.py
│   ├── chat_component.py
│   ├── chat_widget.html
│   ├── organizando.ipynb
│   ├── Procfile
│   ├── requirements_dashboard.txt
│   ├── requirements.txt
│   └── src
│       ├── components
│       ├── config
│       ├── controllers
│       ├── models
│       └── views
</pre>
</details>

<details>
<summary><strong>Backend</strong> (clique para ver a árvore)</summary>
<pre>
├── Backend
│   ├── audit
│   ├── cache
│   ├── Cti.csv
│   ├── data_audit.py
│   ├── data_loader
│   ├── db
│   ├── documentos
│   ├── main.py
│   ├── metrics
│   ├── Procfile
│   ├── rag_engine.py
│   ├── render.yaml
│   ├── requirements.txt
│   ├── routers
│   ├── services
│   └── tests
</pre>
</details>

---

## 💻 Configuração para Desenvolvimento

Para abrir e executar este projeto localmente, certifique-se de ter as seguintes ferramentas instaladas:

* [Python 3.10+](https://www.python.org/)
* [Git](https://git-scm.com/)
* [Visual Studio Code](https://code.visualstudio.com/)

### Passo a Passo

### 1. Clonar o repositório e criar o ambiente virtual

```bash
git clone https://github.com/Ericdelucas/ESC_Semestre4_PI.git
cd ESC_Semestre4_PI
python -m venv .venv
```

Ative o ambiente virtual conforme seu sistema:

**Windows (PowerShell):**

```powershell
.\.venv\Scripts\Activate.ps1
```

**Linux / macOS:**

```bash
source .venv/bin/activate
```

### 2. Instalar as dependências

Na raiz do repositório, com o ambiente virtual ativo:

```bash
python -m pip install -r "src/Entrega 1/Frontend/requirements_dashboard.txt"
python -m pip install -r "src/Entrega 1/Backend/requirements.txt"
```

### 3. Configurar a IA (opcional)

Para habilitar as respostas geradas pelo Gemini, copie `src/Entrega 1/Backend/.env.example` para `src/Entrega 1/Backend/.env` e preencha sua chave:

```dotenv
GOOGLE_API_KEY=sua_chave_aqui
```

A chave é opcional para usar o dashboard e suas análises financeiras. Não versione o arquivo `.env` com credenciais.

### 4. Terminal 1 — Backend FastAPI

Na raiz do repositório, com o ambiente virtual ativo:

```bash
cd "src/Entrega 1"
python -m uvicorn Backend.main:app --reload --port 8000
```

Mantenha este terminal aberto. A API estará em [http://localhost:8000](http://localhost:8000), com documentação em [http://localhost:8000/docs](http://localhost:8000/docs) e verificação de saúde em [http://localhost:8000/api/health](http://localhost:8000/api/health).

### 5. Terminal 2 — Frontend Streamlit

Abra outro terminal na raiz do repositório e ative o mesmo ambiente virtual usando o comando do seu sistema indicado no passo 1. Em seguida:

```bash
cd "src/Entrega 1/Frontend"
python -m streamlit run app.py --server.port 8501
```

Acesse o dashboard em [http://localhost:8501](http://localhost:8501). Mantenha os dois terminais abertos: o chat da interface utiliza a API em `http://localhost:8000`.

## Licença e Referências

### Licença

ESC © 2026 por Eric De Lucas Silva, Stephanie Macedo da Silva, En Hsiang Chien e FECAP. Este projeto está licenciado sob a [Creative Commons Atribuição 4.0 Internacional (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/).

### Referências

1. **CTI Global.** [Site institucional](https://ctiglobal.com/).
2. **Repositório Institucional da UFERSA.** [Trabalho acadêmico utilizado como referência no projeto (PDF)](https://repositorio.ufersa.edu.br/bitstreams/6e642d4f-ce5d-4270-b88a-e4cf1caf7f6d/download).
3. **Repositório Institucional da UFSC.** [O Papel dos Dashboards no FP&A Estratégico: Evidências de um Estudo de Casos Múltiplos (PDF)](https://repositorio.ufsc.br/bitstream/handle/123456789/274297/O%20Papel%20dos%20Dashboards%20no%20FP&A%20Estrat%C3%A9gico%20Evid%C3%AAncias%20de%20um%20Estudo%20de%20Casos%20M%C3%BAltiplos.pdf?sequence=1).
