#!/usr/bin/env bash
# Serviço unificado: FastAPI interno + Streamlit na $PORT da Render.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
APP_DIR="${ROOT}/PI4"
cd "${APP_DIR}"
export PYTHONPATH="${APP_DIR}${PYTHONPATH:+:${PYTHONPATH}}"
export RENDER="${RENDER:-true}"

PORT="${PORT:-10000}"
API_HOST="${API_HOST:-127.0.0.1}"
API_PORT="${API_PORT:-8081}"
export API_HOST API_PORT
export BACKEND_URL="http://${API_HOST}:${API_PORT}"
export CTI_API_URL="${BACKEND_URL}"

echo "[start] FastAPI em ${BACKEND_URL}"
echo "[start] Streamlit em 0.0.0.0:${PORT}"

uvicorn Backend.main:app --host "${API_HOST}" --port "${API_PORT}" &
API_PID=$!

sleep 3

if ! python -c "import urllib.request; urllib.request.urlopen('${BACKEND_URL}/api/v1/health', timeout=5)" >/dev/null 2>&1; then
  echo "[start] erro: FastAPI nao respondeu em ${BACKEND_URL}/api/v1/health"
  kill "${API_PID}" 2>/dev/null || true
  exit 1
fi

echo "[start] FastAPI pronta. A subir o Streamlit."

# Sem exec e sem trap EXIT: o shell fica pai do uvicorn e o Streamlit corre em primeiro plano.
streamlit run Frontend/app.py \
  --server.port="${PORT}" \
  --server.address=0.0.0.0 \
  --server.headless=true

kill "${API_PID}" 2>/dev/null || true
