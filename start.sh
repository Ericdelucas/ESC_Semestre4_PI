#!/usr/bin/env bash
# FastAPI em background; Streamlit liga ja na $PORT para a Render nao devolver 503.
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
export BACKEND_URL="http://127.0.0.1:${API_PORT}"
export CTI_API_URL="${BACKEND_URL}"

echo "[start] cwd=$(pwd) RENDER=${RENDER:-}"
echo "[start] PORT publica Streamlit=${PORT}"
echo "[start] FastAPI interna ${BACKEND_URL} (bind ${API_BIND}:${API_PORT})"
echo "[start] DATABASE_URL definida=$([ -n "${DATABASE_URL:-}" ] && echo sim || echo nao)"
echo "[start] DATABASE_URL_POOLER definida=$([ -n "${DATABASE_URL_POOLER:-}" ] && echo sim || echo nao)"
echo "[start] SUPABASE_REGION=${SUPABASE_REGION:-<vazia>}"

uvicorn Backend.main:app --host "${API_BIND}" --port "${API_PORT}" --log-level info &
API_PID=$!
echo "[start] uvicorn PID=${API_PID}"

echo "[start] a ligar Streamlit imediatamente em 0.0.0.0:${PORT}"
streamlit run Frontend/app.py \
  --server.port="${PORT}" \
  --server.address=0.0.0.0 \
  --server.headless=true \
  --logger.level=info

echo "[start] Streamlit saiu; a terminar uvicorn pid=${API_PID}"
kill "${API_PID}" 2>/dev/null || true
