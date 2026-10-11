#!/usr/bin/env bash
# Sobe FastAPI (interno) + Streamlit (porta pública da Render).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
APP_DIR="${ROOT}/PI4"
cd "${APP_DIR}"
export PYTHONPATH="${APP_DIR}${PYTHONPATH:+:${PYTHONPATH}}"
export RENDER="${RENDER:-true}"

PORT="${PORT:-10000}"
API_HOST="${API_HOST:-127.0.0.1}"
API_PORT="${API_PORT:-8081}"
export CTI_API_URL="${CTI_API_URL:-http://${API_HOST}:${API_PORT}}"

echo "[start] API em ${API_HOST}:${API_PORT}"
echo "[start] Streamlit na porta pública ${PORT}"
echo "[start] CTI_API_URL=${CTI_API_URL}"

uvicorn Backend.main:app --host "${API_HOST}" --port "${API_PORT}" &
API_PID=$!

shutdown() {
  kill "${API_PID}" 2>/dev/null || true
}
trap shutdown EXIT INT TERM

for _ in 1 2 3 4 5 6 7 8 9 10; do
  if python -c "import urllib.request; urllib.request.urlopen('${CTI_API_URL}/api/v1/health', timeout=2)" >/dev/null 2>&1; then
    break
  fi
  sleep 1
done

exec streamlit run Frontend/app.py \
  --server.port="${PORT}" \
  --server.address=0.0.0.0 \
  --server.headless=true
