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

<h3> 📖 Tutorial de como acessar o dashboard</h3>

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

## 💻 Configuração para Desenvolvimento

Descreva como instalar todas as dependências para desenvolvimento e como rodar um test-suite automatizado de algum tipo. Se necessário, faça isso para múltiplas plataformas.

Para abrir este projeto você necessita das seguintes ferramentas:

-<a href="https://godotengine.org/download">GODOT</a>

```sh
make install
npm test
Coloque código do prompt de comnando se for necessário
```

## 📋 Licença/License
Utilize o link <https://chooser-beta.creativecommons.org/> para fazer uma licença CC BY 4.0.

## 🎓 Referências

Aqui estão as referências usadas no projeto.

1. <https://github.com/iuricode/readme-template>
2. <https://github.com/gabrieldejesus/readme-model>
3. <https://chooser-beta.creativecommons.org/>
4. <https://freesound.org/>
5. <https://www.toptal.com/developers/gitignore>
6. Músicas por: <a href="https://freesound.org/people/DaveJf/sounds/616544/"> DaveJf </a> e <a href="https://freesound.org/people/DRFX/sounds/338986/"> DRFX </a> ambas com Licença CC 0.
