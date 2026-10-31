# Backend CTI

`main.py` cria a aplicacao FastAPI e regista os routers e a configuracao de runtime.
Os comandos de arranque e os endpoints existentes foram preservados.

| Modulo | Responsabilidade |
| --- | --- |
| `routers/auth_router.py` | Login, logout e logs em `/api/v1/auth/*` |
| `routers/chat_router.py` | Contrato HTTP de `/api/chat` |
| `routers/health_router.py` | `/`, `/api/health`, `/api/v1/health` e `/json/version` |
| `routers/users.py` | Gestao de usuarios em `/api/v1/users/*` |
| `routers/email.py` | SMTP e risco em `/api/v1/email/*` |
| `services/dashboard_pipeline.py` | Orquestracao e API publica dos dados do dashboard |
| `services/dashboard_cache.py` | Parquets e fallback CSV |
| `services/metrics_calculator.py` | Metricas de contexto e reconstrucao de contas |
| `services/scenario_filter.py` | Filtros de cenario/ano e consolidacao anual |
| `services/chat_service.py` | Inicializacao lazy do RAG e historico por sessao |
| `runtime.py` | Lifespan, logs de pedidos e CORS |
| `services/`, `data_loader/`, `metrics/`, `db/` | Servicos, leitura de dados, calculos e persistencia |

## Arranque local

Com as dependencias de `requirements.txt` instaladas, a partir desta pasta:

```sh
python -m uvicorn main:app --host 127.0.0.1 --port 8000
```

O comando `uvicorn Backend.main:app` continua disponivel a partir de `PI4/`.
Na Render, use `uvicorn main:app --host 0.0.0.0 --port $PORT` nesta pasta.
O blueprint da raiz publica dois servicos; consulte `../README.md`.

## Verificacao de contratos

A partir da raiz do repositorio (inclui `httpx`, dependencia do TestClient):

```sh
python -m unittest discover -s PI4/Backend/tests -v
```

Os testes executam o lifespan real com SQLite temporario e verificam paths,
metodos, saude, autenticacao, CORS, sessoes de chat e o pipeline do dashboard.
O pipeline e verificado com filtros, KPIs e leitura/escrita de parquets temporarios. O motor de resposta e os
alertas por e-mail sao substituidos nos testes para evitar chamadas externas.
