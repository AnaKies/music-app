#!/bin/bash

set -euo pipefail

API_BASE_URL="${API_BASE_URL:-http://localhost:8000}"
FRONTEND_BASE_URL="${FRONTEND_BASE_URL:-http://localhost:3000}"
SCORE_ID="${SCORE_ID:-}"
ALLOW_SKIP_SCORE_STATUS="${ALLOW_SKIP_SCORE_STATUS:-false}"

parse_json_field() {
  local payload="$1"
  local field_name="$2"

  python3 - "$payload" "$field_name" <<'PY'
import json
import sys

payload = json.loads(sys.argv[1])
field_name = sys.argv[2]
value = payload.get(field_name)
if isinstance(value, bool):
    print("true" if value else "false")
elif value is None:
    print("")
else:
    print(value)
PY
}

echo "========================================="
echo "MusicApp Preview Smoke Check"
echo "========================================="
echo "Frontend: $FRONTEND_BASE_URL"
echo "API:      $API_BASE_URL"
echo ""

echo "[1/4] Checking API health..."
api_health_payload="$(curl -fsS "$API_BASE_URL/health")"
api_status="$(parse_json_field "$api_health_payload" "status")"
if [ "$api_status" != "ok" ]; then
  echo "✗ API health check failed: unexpected status '$api_status'"
  exit 1
fi
echo "✓ API health check passed"

echo "[2/4] Checking worker liveness..."
worker_payload="$(curl -fsS "$API_BASE_URL/health/worker")"
worker_status="$(parse_json_field "$worker_payload" "status")"
worker_runtime="$(parse_json_field "$worker_payload" "runtime")"
if [ "$worker_status" != "ok" ]; then
  echo "✗ Worker liveness check failed: runtime '$worker_runtime' is not healthy"
  exit 1
fi
echo "✓ Worker liveness check passed"

echo "[3/4] Checking frontend-to-backend reachability..."
curl -fsS "$FRONTEND_BASE_URL" >/dev/null
frontend_backend_payload="$(curl -fsS "$FRONTEND_BASE_URL/api/health/backend")"
frontend_backend_status="$(parse_json_field "$frontend_backend_payload" "status")"
if [ "$frontend_backend_status" != "ok" ]; then
  echo "✗ Frontend-to-backend reachability failed"
  exit 1
fi
echo "✓ Frontend-to-backend reachability is healthy"

echo "[4/4] Checking durable score-status read path..."
if [ -z "$SCORE_ID" ]; then
  if [ "$ALLOW_SKIP_SCORE_STATUS" = "true" ]; then
    echo "⚠ SCORE_ID is not set; skipping /scores/{id} smoke check because ALLOW_SKIP_SCORE_STATUS=true"
  else
    echo "✗ SCORE_ID is required for F16 score-status verification"
    exit 1
  fi
else
  score_payload="$(curl -fsS "$API_BASE_URL/scores/$SCORE_ID")"
  score_processing_status="$(parse_json_field "$score_payload" "processingStatus")"
  if [ -z "$score_processing_status" ]; then
    echo "✗ Score status read check failed: processingStatus is missing"
    exit 1
  fi
  echo "✓ Score status read check passed for score $SCORE_ID with status '$score_processing_status'"
fi

echo ""
echo "Smoke verification passed."
