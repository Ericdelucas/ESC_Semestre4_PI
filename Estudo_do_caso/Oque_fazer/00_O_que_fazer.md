# O que fazer — CTI / Demonstrativo FECAP

Documento de planejamento do **Estudo do caso** (antes do desenvolvimento em `PI4`).
Base analisada: `base_de_dados/Demonstrativo Fecap v3.xlsx`  
Template: `templeit_PI/PI_4CCOMP_202602_CTI_Ciencia_de_Dados_v3-1.pdf`

---

## 1. O que o projeto é (e o que não é)

| É | Não é |
|---|---|
| Plataforma analítica de **planejamento financeiro** (case CTI) | Sistema ERP / contábil completo |
| Ciência de Dados: limpar → analisar → KPIs → dashboard na nuvem | App transacional com CRUD de lançamentos |
| Apoio à decisão com cenários, KPIs e regressão | Previsão “mágica” sem premissas documentadas |

**Parceira / tema:** CTI Global — gestão corporativa e planejamento financeiro.  
**Entrega central:** dashboard publicado (Streamlit/Dash/etc.) com **≥ 5 indicadores**, filtros, relatórios e rastreabilidade no GitHub.

### Pastas deste repositório

- `Estudo_do_caso/` — ler, planejar, documentar, explorar hipóteses.
- `PI4/` — desenvolver a solução (código, notebooks, dashboard, docs de engenharia).

---

## 2. O que a base de dados contém (auditoria inicial)

### Formato físico

- Arquivo Excel (~centenas de MB no XML interno), **1 aba**: `Demonstrativo Fecap v3.csv`.
- Layout **longo (tidy)** com 4 colunas:

| Coluna | Conteúdo | Exemplo |
|--------|----------|---------|
| A | Ano do horizonte | `Ano 1` … `Ano 12` |
| B | Cenário simulado | `Total Cen_00001` … `Total Cen_01200` |
| C | Conta do demonstrativo | `DRE - Receita`, `BAL - Disponível`, … |
| D | Valor numérico (R$) | ex.: receita ~6,7e9 no Cen_00001 / Ano 1 |

- Há linhas “cabeçalho” de cenário com valor em D **sem conta** (ex.: `0.025…` no Ano 1 / Cen_00001) — candidato a **taxa / probabilidade / parâmetro do cenário**; precisa confirmação com a CTI.
- Volume estimado: **~1.200 cenários × 12 anos × ~69 contas** → ordem de **~1 milhão de linhas** (arquivo grande; não abrir “no Excel e torcer” — processar com Python/Pandas em chunks ou Parquet).

### Famílias de contas (69 linhas)

1. **BAL — Balanço patrimonial**  
   Ativo (circulante, LP, permanente, outorga, depreciação/amortização…), Passivo (empréstimos, fornecedores, poder concedente…), Patrimônio Líquido.
2. **DRE — Demonstração do resultado**  
   Receita, Tributos, Custos, Depreciação/Amortização, Resultado Operacional, Resultado Financeiro, IR/CSLL, Resultado Líquido, **EBITDA**.
3. **FLU — Fluxo / caixa**  
   Saldo inicial/final, Receita, Tributos, Custos, Investimentos, Entradas, Despesas financeiras, Distribuição a acionistas, **Geração de Caixa**.

### Leitura de negócio (hipótese forte)

Perfil de **empresa de concessão / infraestrutura** (contas como *Outorga da Concessão*, *Obrigações com o Poder Concedente*, forte intangível e endividamento de LP).  
Os **1.200 cenários × 12 anos** apontam para **simulação de planejamento** (tipo Monte Carlo / stress de premissas), não para um único balanço histórico estático.

> Validar com professores/CTI: origem dos cenários, significado da coluna “parâmetro” sem conta, unidade (R$ corrente?), e se os anos são calendário ou ano de projeto.

---

## 3. O que o template exige (checklist do PI)

### Obrigatório no escopo

- [ ] Catálogo de fontes + dicionário de dados + qualidade
- [ ] Camadas **raw / staging / processed** (nunca sobrescrever o Excel original)
- [ ] Análise **descritiva** (média, mediana, moda, variância, desvio, histograma, boxplot)
- [ ] Análise **inferencial + regressão** (coeficientes, métricas, limitações)
- [ ] **KPIs financeiros** documentados (fórmula, unidade, interpretação) + planilha de validação
- [ ] Relatórios gerenciais (Word/PDF)
- [ ] **Dashboard na nuvem** com ≥ 5 indicadores, filtros e comparações
- [ ] Cenários / sensibilidade (desconto, custo, volume… — aqui os 1.200 cenários já ajudam)
- [ ] Exportação (CSV/XLSX/PDF quando fizer sentido)
- [ ] Engenharia: ágil, requisitos, UML (≥ 2 diagramas), GitHub

### Datas / entregas (do template — confirmar no calendário oficial)

- **E1 (parcial)** — ~25/set — descritiva + início do pipeline de dados  
- **E2 (final)** — ~06/nov — dashboard publicado + documento com empresa  
- UCs: Análise Inferencial, Contabilidade e Finanças, ES/Arquitetura, PI Ciência de Dados

### Stack sugerida (alinhada ao template)

Python · Pandas/NumPy · SciPy/Statsmodels/Sklearn · Matplotlib/Plotly · Streamlit ou Dash · Parquet/SQLite · GitHub · nuvem (Streamlit Cloud / Render / Azure / etc.)

---

## 4. O que conseguimos fazer **com esta base** (MVP realista)

### 4.1 Engenharia de dados (base de tudo)

1. Preservar o XLSX em `raw/`.
2. Converter para **Parquet/CSV longo** tipado: `ano`, `cenario_id`, `familia` (BAL|DRE|FLU), `conta`, `valor`.
3. Limpar nomes de contas (há espaços duplos: `BAL  - Patrimônio…`).
4. Tratar linhas sem `conta` (parâmetro do cenário) em tabela à parte.
5. Dicionário de dados + relatório de qualidade (nulos, duplicatas, balanço que não fecha, outliers).
6. Validar identidade contábil: Ativo ≈ |Passivo+PL|, coerência DRE ↔ FLU quando possível.

### 4.2 Análises descritivas

| Análise | Como usar os dados |
|---------|-------------------|
| Distribuição por conta | Histograma/boxplot de Receita, EBITDA, Lucro, Caixa **entre os 1.200 cenários** (por ano) |
| Evolução temporal | Série Ano 1→12 da mediana / P50 de cada KPI |
| Comparação de cenários | Cenário “base” vs pior / melhor / quartis |
| Estrutura do balanço | Composição % Ativo / Passivo ao longo do tempo |
| Dispersão do risco | Amplitude, CV, IQR de EBITDA e Geração de Caixa |
| Outliers | Cenários extremos (stress) |

### 4.3 KPIs financeiros possíveis (sem dado externo)

**Resultado / margem**

- Receita bruta / líquida (após tributos, se definirmos regra)
- Custos / Receita
- EBITDA e **Margem EBITDA**
- Resultado Operacional e margem
- Resultado Líquido e **Margem líquida**
- Resultado Financeiro / Despesas financeiras

**Balanço / solvência / liquidez**

- Liquidez corrente (Ativo Circulante / |Passivo Circulante|)
- Endividamento (Empréstimos / Ativo ou / PL)
- PL / Ativo
- Intangível / Ativo (peso da concessão)
- Disponível / Passivo Circulante (caixa imediato)

**Caixa / investimento**

- Geração de Caixa
- Saldo Final de caixa
- Investimentos (proxy de CAPEX)
- Distribuição a acionistas / Geração de Caixa
- Conversão: EBITDA → Caixa (quando as contas permitirem)

**Planejamento / risco (força desta base)**

- P10, P50, P90 (ou percentis) de cada KPI por ano
- Probabilidade de EBITDA &lt; 0, caixa &lt; 0, margem abaixo de meta
- Intervalo de confiança empírico via cenários (não confundir com IC clássico sem hipótese)
- Ranking de cenários por valor presente aproximado (se houver taxa; ver linha-parâmetro)

> CAC/LTV do template: **não aparecem** nesta base. Só fazem sentido se a CTI entregar dados de clientes/aquisição **ou** se forem **simulados** com premissas explícitas (e rotulados como simulação).

### 4.4 Regressão e inferência (compatível com a base)

Exemplos de perguntas e modelos:

1. **Receita vs Custos** (por ano, entre cenários) — elasticidade de custo.
2. **EBITDA ~ Receita + Despesas Financeiras + Investimentos**.
3. **Geração de Caixa ~ EBITDA + Investimentos + Resultado Financeiro**.
4. **Endividamento ~ Investimentos / Outorga** (se fizer sentido econômico).
5. Comparar coeficientes **Ano 1 vs Ano 12** (mudança de estrutura no horizonte).
6. Testes de diferença de médias/medianas entre grupos de cenários (ex.: tercis de receita).

Documentar sempre: pressupostos, R²/RMSE, resíduos, e que **correlação ≠ causalidade**.

### 4.5 Sensibilidade e cenários (RF11)

- Usar os **1.200 cenários prontos** como motor de sensibilidade.
- No dashboard: slider/filtro de ano + seleção de percentil + “modo executivo” (P50) vs “modo risco” (P10).
- Simulação extra (opcional): “e se custos +10%?” aplicando fator sobre a série processada (deixar claro que é *what-if* simplificado).

### 4.6 Dashboard — 5+ indicadores sugeridos (MVP)

1. Receita (P50) — evolução 12 anos  
2. Margem EBITDA (distribuição por cenários no ano selecionado)  
3. Resultado Líquido (P10 / P50 / P90)  
4. Geração de Caixa / Saldo Final  
5. Endividamento ou Liquidez corrente  
6. (bônus) Probabilidade de caixa negativo no horizonte  

Filtros: Ano, faixa de cenário, família BAL/DRE/FLU, conta.

### 4.7 Relatórios gerenciais a gerar

- Perfil da empresa e leitura do demonstrativo  
- Qualidade dos dados e transformações  
- Descritiva completa (UC Análise Inferencial — Entrega 1)  
- Dicionário de KPIs + planilha de validação (UC Contabilidade)  
- Relatório de regressão (Entrega 2 da UC)  
- Relatório final PI + recomendações de decisão para a CTI  

---

## 5. Perguntas de negócio que o painel pode responder

1. No horizonte de 12 anos, qual a **trajetória mediana** de receita, EBITDA e caixa?  
2. Quão **espalhado** é o resultado entre os 1.200 cenários (risco)?  
3. Em quantos % dos cenários o caixa ou o lucro ficam abaixo de zero / de uma meta?  
4. A estrutura de capital (dívida vs PL) melhora ou piora ao longo do tempo?  
5. Investimentos (CAPEX) acompanham a geração de caixa?  
6. Quais contas do BAL mais explicam a variação do EBITDA entre cenários?  
7. O resultado operacional sustenta as despesas financeiras?  

---

## 6. Limitações atuais (importante ser honesto no relatório)

- Não há (ainda) metadados oficiais dos cenários (o que muda entre Cen_00001 e Cen_01200).  
- Sem calendário real (2024, 2025…) — só “Ano 1…12”.  
- Sem dados de clientes, tickets, cupons, CAC/LTV, unidades de negócio ou produtos.  
- Passivo negativo na planilha parece **convenção de sinal** (crédito/débito); precisa padronizar no processed.  
- Arquivo muito grande → pipeline e amostragem para prototipar o dashboard.  
- Template cita “desconto/cupom” — mapear para variáveis **existentes** (custos, receita, investimentos) ou pedir dado complementar.

---

## 7. Próximas possibilidades — se tivermos **outras bases**

Tudo abaixo **amplia** o valor analítico (o template permite fontes externas desde que documentadas: origem, data, licença, variáveis, justificativa).

### 7.1 Outras empresas / peers (mesmo setor)

**Fontes:** CVM, B3, RI de CCR, EcoRodovias, Rumo, Aegea, etc.

| Possibilidade | Valor |
|---------------|--------|
| Benchmark de margem EBITDA / alavancagem | Situar o case CTI vs mercado |
| Peer multiples (EV/EBITDA simplificado, se houver preço) | Contexto de valuation |
| Comparação de estrutura de CAPEX e dívida | Recomendações de planejamento |

### 7.2 Mercado financeiro — Ibovespa, ações, índices

**Fontes:** B3, Yahoo Finance, Investing, Banco Central (SGS).

| Possibilidade | Valor |
|---------------|--------|
| Correlacionar desempenho do peer setorial com Ibovespa | Beta / sensibilidade de mercado |
| Comparar retorno de acionista (se houver distribuição) vs Ibovespa / IFIX | Custo de oportunidade |
| Usar retorno de mercado como fator em regressão | Modelo tipo “mercado + fundamentals” |

### 7.3 Macroeconomia — Selic, CDI, IPCA, câmbio, PIB

**Fontes:** BCB SGS, IBGE, IPEA Data.

| Possibilidade | Valor |
|---------------|--------|
| Trazer valores a **preços constantes** (deflacionar) | Leitura real do horizonte de 12 anos |
| Proxy de taxa de desconto (WACC simplificado com Selic + spread) | **VPL / valor presente** dos fluxos FLU |
| Estresse: choque de juros ↔ despesas financeiras | Sensibilidade macro |
| Câmbio se houver dívida em moeda estrangeira | Risco cambial (se a CTI confirmar) |

### 7.4 Dados setoriais de concessão / infraestrutura

**Fontes:** ANTT, ARTESP, agências reguladoras, relatórios setoriais.

| Possibilidade | Valor |
|---------------|--------|
| Tráfego / demanda / tarifa | Explicar a receita dos cenários |
| Reajuste tarifário vs IPCA | Premissas de receita |
| Comparar outorga e obrigações com benchmarks regulatórios | Compliance / planejamento |

### 7.5 Dados operacionais internos (se a CTI liberar depois)

Clientes, contratos, unidades, produtos, descontos, funil comercial:

- Ticket médio, churn, CAC/LTV (aí o template “fecha” 100%)  
- Segmentação e clustering  
- Otimização de mix / desconto (extensão do template)  

### 7.6 Séries temporais e extensões do template (§9)

Com histórico mais fino (mensal) ou macro:

- Projeção ARIMA/Prophet de receita/caixa  
- Detecção de anomalias e alertas  
- Cenários otimista / realista / pessimista nomeados  
- Pipeline agendado (API BCB + reprocessamento)  

### 7.7 Mapa rápido: “tenho X → posso fazer Y”

| Se conseguirmos… | Então podemos… |
|------------------|-----------------|
| Só o Demonstrativo atual | Descritiva, KPIs, risco por cenários, regressão entre contas, dashboard de planejamento |
| + Selic/IPCA | Deflação, VPL, stress de juros |
| + Ibovespa / ação peer | Benchmark de mercado e correlação |
| + Demonstrativos de 2–3 peers | Ranking competitivo de margens e alavancagem |
| + Demanda/tráfego/tarifa | Explicar receita e melhorar regressão |
| + Dados comerciais (cliente/produto) | CAC/LTV, ticket, cupom, segmentação |
| + Premissas dos 1.200 cenários | Atribuir causa às caudas (o que gera P10) |

---

## 8. Roteiro sugerido (Estudo do caso → PI4)

### Agora (nesta pasta)

1. Validar com CTI/professores o significado dos cenários e da linha-parâmetro.  
2. Fechar o **recorte do MVP** (quais 5–7 KPIs entram no pitch).  
3. Escrever dicionário preliminar das 69 contas.  
4. Definir perguntas analíticas priorizadas (seção 5).  

### Em seguida (em `PI4`)

1. Pipeline raw → processed (Parquet).  
2. Notebook de descritiva (Entrega UC).  
3. Dicionário de KPIs + validação em planilha.  
4. Regressão documentada.  
5. Dashboard Streamlit/Dash + publicação.  
6. Docs ES (ágil, requisitos, UML).  
7. Fontes externas **só se** sobrar tempo e houver justificativa clara (começar por **BCB: Selic/IPCA** — alto valor, baixo atrito).

---

## 9. Decisão de foco recomendada (para o grupo)

**Foco do MVP:** *“Painel de planejamento financeiro sob incerteza”* — mostrar como receita, EBITDA, caixa e endividamento se comportam no horizonte de 12 anos **através de 1.200 cenários**, com KPIs, percentis e uma regressão que ligue drivers (receita/custos/investimentos/financeiro) ao resultado.

**Extensão “nota cheia” se der tempo:** integrar **IPCA + Selic** (deflação + VPL) e, se possível, **1 peer de B3** para benchmark de margem.

---

## 10. Próximo passo imediato

Reunião rápida do grupo para:

1. Confirmar o foco do MVP acima.  
2. Listar dúvidas para a CTI (cenários + parâmetro da coluna D sem conta).  
3. Começar o dicionário de dados e a conversão XLSX → Parquet em `PI4`.

Quando quiser, o próximo artefato nesta pasta pode ser: **dicionário de dados v1** ou **backlog do MVP (issues)**.
