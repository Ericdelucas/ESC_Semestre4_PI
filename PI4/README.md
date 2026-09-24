# ESC_Semestre4_PI · PI4

Painel financeiro CTI. O dashboard fica em `Frontend` e a API do chat em `Backend`.

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

Confirme em [http://localhost:8000/api/health](http://localhost:8000/api/health). A resposta esperada é `{"status":"ok"}`. Deixe esse terminal aberto.

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

PDFs e Markdown extras para o assistente ficam em `Backend/documentos/`.

## Estrutura

```
PI4/
  Backend/     # FastAPI, Cti.csv, documentos, cache
  Frontend/    # Streamlit, src (config, controllers, models, views)
```

## Visões por perfil

- **CEO - Visão estratégica:** receita, resultado, EBITDA, custos e capacidade de investir.
- **CFO - Gestão financeira:** capital de giro, tesouraria, empréstimos e evolução de caixa.
- **Acionistas - Retorno e risco:** lucro, margem líquida, crescimento, distribuições e sustentação do caixa.
- **Poder concedente - Sustentabilidade da concessão:** liquidez, continuidade financeira, investimentos e anos críticos.

Cada perfil abre uma visão própria e oferece análises detalhadas relevantes ao cargo.
Os cartões mostram médias anuais quando o filtro está em Todos; gráficos e tabelas respeitam o período selecionado.
A variação anual usa o ano anterior do mesmo cenário, inclusive quando apenas um ano está selecionado.
A frequência de cenários com sinais financeiros considera caixa final negativo, liquidez abaixo de 1 ou geração de caixa negativa, com pesos iguais; não representa probabilidade de falência.
