#!/usr/bin/env bash
# Servico unificado: FastAPI interno + Streamlit na $PORT da Render.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
APP_DIR="${ROOT}/PI4"
cd "${APP_DIR}"
export PYTHONPATH="${APP_DIR}${PYTHONPATH:+:${PYTHONPATH}}"
export RENDER="${RENDER:-true}"
export PYTHONUNBUFFERED=1

PORT="${PORT:-10000}"
API_BIND="${API_BIND:-0.0.0.0}"
API_HOST="${API_HOST:-127.0.0.1}"
API_PORT="${API_PORT:-8081}"
export API_HOST API_PORT
# Cliente no mesmo container: loopback, nunca a URL publica da Render.
export BACKEND_URL="http://127.0.0.1:${API_PORT}"
export CTI_API_URL="${BACKEND_URL}"

echo "[start] =========================================="
echo "[start] cwd=$(pwd) ROOT=${ROOT} APP_DIR=${APP_DIR}"
echo "[start] RENDER=${RENDER} PYTHONPATH=${PYTHONPATH}"
echo "[start] PORT publica Streamlit=${PORT}"
echo "[start] API_HOST=${API_HOST} API_PORT=${API_PORT}"
echo "[start] BACKEND_URL=${BACKEND_URL}"
echo "[start] CTI_API_URL=${CTI_API_URL}"
if [ "${PORT}" = "${API_PORT}" ]; then
  echo "[start] CONFLITO: PORT publica e API_PORT sao iguais (${PORT})"
fi
echo "[start] a iniciar uvicorn Backend.main:app --host ${API_BIND} --port ${API_PORT}"
echo "[start] cliente Streamlit usa ${BACKEND_URL}"
echo "[start] =========================================="

uvicorn Backend.main:app --host "${API_BIND}" --port "${API_PORT}" --log-level info &
API_PID=$!
echo "[start] uvicorn PID=${API_PID}"

HEALTH_URL="${BACKEND_URL}/api/v1/health"
ready=0
for tentativa in 1 2 3; do
  echo "[start] health tentativa ${tentativa}/3 GET ${HEALTH_URL}"
  if python - <<PY
import urllib.error
import urllib.request
url = "${HEALTH_URL}"
print(f"[start-py] GET {url}", flush=True)
try:
    req = urllib.request.Request(url, method="GET", headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=4) as resp:
        body = resp.read()[:240]
        print(f"[start-py] status={resp.status} body={body!r}", flush=True)
        if int(resp.status) != 200:
            raise SystemExit(1)
except urllib.error.HTTPError as exc:
    print(f"[start-py] HTTPError status={exc.code} reason={exc.reason}", flush=True)
    raise SystemExit(1)
except Exception as exc:
    print(f"[start-py] ERRO {type(exc).__name__}: {exc}", flush=True)
    raise SystemExit(1)
PY
  then
    ready=1
    echo "[start] FastAPI pronta em ${BACKEND_URL}"
    break
  fi
  echo "[start] health ainda falhou; a esperar 2s"
  sleep 2
done

if [ "${ready}" -ne 1 ]; then
  echo "[start] uvicorn ainda no ar? pid=${API_PID}"
  ps -p "${API_PID}" -o pid,cmd || echo "[start] processo uvicorn nao encontrado"
  echo "[start] erro: FastAPI nao respondeu em ${HEALTH_URL}"
  kill "${API_PID}" 2>/dev/null || true
  exit 1
fi

echo "[start] URL base que o Streamlit vai usar: ${BACKEND_URL}"
echo "[start] a subir streamlit run Frontend/app.py --server.port=${PORT}"

streamlit run Frontend/app.py \
  --server.port="${PORT}" \
  --server.address=0.0.0.0 \
  --server.headless=true \
  --logger.level=info

echo "[start] Streamlit saiu; a terminar uvicorn pid=${API_PID}"
kill "${API_PID}" 2>/dev/null || true
