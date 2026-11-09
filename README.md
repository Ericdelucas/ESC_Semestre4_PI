# FECAP - Fundação de Comércio Álvares Penteado

<p align="center">
<a href="https://www.fecap.br/"><img src="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRhZPrRa89Kma0ZZogxm0pi-tCn_TLKeHGVxywp-LXAFGR3B1DPouAJYHgKZGV0XTEf4AE&usqp=CAU" alt="FECAP - Fundação de Comércio Álvares Penteado" border="0"></a>
</p>

# ESC

## Integrantes 

<p align="center">
  <img src="imagens/integrantes/logo.png" width="400" alt="Logo ESC Dashboard CTI">
</p>




<center>
<table width="600">
  <tr>
    <td align="center" valign="top" width="200">
      <a href="https://www.linkedin.com/in/eric-de-lucas-silva/">
        <img src="imagens/integrantes/eric.svg.png" width="150" height="150" alt="Imagem provisória de Eric De Lucas Silva"><br>
        <strong>Eric De Lucas Silva</strong>
      </a>
    </td>
    <td align="center" valign="top" width="200">
      <a href="https://www.linkedin.com/in/stephanie-macedo-da-silva/">
        <img src="imagens/integrantes/Stepha.jpeg" width="150" height="150" alt="Imagem provisória de Stephanie Macedo da Silva"><br>
        <strong>Stephanie Macedo da Silva</strong>
      </a>
    </td>
    <td align="center" valign="top" width="200">
      <a href="https://www.linkedin.com/in/en-hsiang-chien-53b550381/">
        <img src="imagens/integrantes/chien.jpeg" width="150" height="150" alt="Imagem provisória de En Hsiang Chien"><br>
        <strong>En Hsiang Chien</strong>
      </a>
    </td>
  </tr>
</table>

</center>

## Professores Orientadores: <a href="https://www.linkedin.com/in/eduardo-savino/">Eduardo Savino Gomes</a>, <a href="https://www.linkedin.com/in/luisspires/">Luis Fernando dos Santos Pires</a>, <a href="https://www.linkedin.com/in/professorrodnil/">Rodnil da Silva Moreira Lisboa</a> e Mauricio Lopes Da Cunha.

---

## Descrição

<p align="center">

<img src="imagens/dast.png"> 
<br>
Imagem do dashboard
</p>

O projeto ESC consiste no desenvolvimento de um dashboard preditivo e simulador de cenários financeiros criado em Python para otimizar a gestão e análise de riscos da CTI. A solução centraliza dados dispersos e substitui rotinas manuais por um dashboard integrado, ágil e visual.

Na prática, a ferramenta automatiza o cálculo de indicadores essenciais como DRE, fluxo de caixa, liquidez e ponto de equilíbrio e permite simular diferentes cenários operacionais em tempo real. Além disso, oferece visões personalizadas por perfil de usuário (como CEO e CFO) e conta com um assistente de inteligência artificial para apoiar a diretoria na tomada de decisões estratégicas de forma rápida.

* 🌐 **Acesse o sistema online:** [Clique aqui para ir ao dashboard (Render)](https://esc-semestre4-pi.onrender.com/)
* 🎥 **Demonstração em Vídeo:** [Assistir ao vídeo explicativo no Google Drive](https://drive.google.com/file/d/1kHEZbDkoGPPZ-bo2bGT8GERNwtJYDaoU/view?usp=sharing)

---

## 🛠 Estrutura de Pastas
<pre>
.
├── documentos
│   ├── Banner_FECAP_CCOMP4_ESC.pptx
│   ├── Documento - Projeto de Extensão - COM Empresa - 2026_2.docx
│   ├── Entrega 1
│   │   ├── Análise Inferencial de Dados
│   │   ├── Contabilidade e Finanças
│   │   ├── Engenharia de Software e Arquitetura de Sistemas
│   │   └── Projeto Interdisciplinar Ciência de Dados
│   ├── Entrega 2
│   │   ├── Análise Inferencial de Dados
│   │   ├── Contabilidade e Finanças
│   │   ├── Engenharia de Software e Arquitetura de Sistemas
│   │   └── Projeto Interdisciplinar Ciência de Dados
│   ├── README.md
│   └── Venha para a FECAP!.txt
├── imagens
│   ├── Captura de tela 2026-10-31 114755.png
│   ├── Captura de tela 2026-10-31 114829.png
│   ├── Captura de tela 2026-10-31 114905.png
│   ├── Captura de tela 2026-10-31 114923.png
│   ├── Captura de tela 2026-10-31 115013.png
│   ├── Captura de tela 2026-10-31 115034.png
│   ├── Captura de tela 2026-10-31 115052.png
│   └── Captura de tela 2026-10-31 115115.png
├── README copy.md
├── README.md
└── src
    ├── Entrega 1
    │   ├── Backend
    │   ├── Frontend
    │   └── Venha para a FECAP!.txt
    └── Entrega 2
        ├── Backend
        ├── Frontend
        └── Venha para a FECAP!.txt
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
