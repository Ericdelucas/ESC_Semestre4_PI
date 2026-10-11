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
export API_HOST API_PORT

INTERNAL_API="http://${API_HOST}:${API_PORT}"
export BACKEND_URL="${INTERNAL_API}"
export CTI_API_URL="${INTERNAL_API}"

echo "[start] API interna em ${INTERNAL_API}"
echo "[start] Streamlit na porta pública ${PORT}"
echo "[start] BACKEND_URL=${BACKEND_URL}"

uvicorn Backend.main:app --host "${API_HOST}" --port "${API_PORT}" &
API_PID=$!

shutdown() {
  kill "${API_PID}" 2>/dev/null || true
}
# Nao usar trap EXIT: o exec do Streamlit dispararia o trap e matava o uvicorn.
trap shutdown INT TERM

ready=0
for _ in $(seq 1 30); do
  if python -c "import urllib.request; urllib.request.urlopen('${INTERNAL_API}/api/v1/health', timeout=2)" >/dev/null 2>&1; then
    ready=1
    break
  fi
  sleep 1
done

if [ "${ready}" -ne 1 ]; then
  echo "[start] aviso: API ainda sem health em ${INTERNAL_API}; a subir o Streamlit na mesma"
fi

exec streamlit run Frontend/app.py \
  --server.port="${PORT}" \
  --server.address=0.0.0.0 \
  --server.headless=true
