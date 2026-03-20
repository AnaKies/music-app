#!/bin/bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PREVIEW_API_BASE_URL="${PREVIEW_API_BASE_URL:-${API_BASE_URL:-}}"
PRODUCTION_API_BASE_URL="${PRODUCTION_API_BASE_URL:-}"
SCORE_ID="${SCORE_ID:-}"

echo "========================================="
echo "MusicApp Post-Deploy Verification"
echo "========================================="
echo ""

echo "[1/3] Running preview smoke verification..."
"$SCRIPT_DIR/preview-smoke.sh"
echo "✓ Preview smoke verification passed"

echo "[2/3] Confirming checklist gate coverage..."
if [ -z "$SCORE_ID" ]; then
  echo "✗ SCORE_ID is required for the post-deploy checklist"
  exit 1
fi
echo "✓ Required score-status input is present"

echo "[3/3] Checking environment-state drift..."
if [ -n "$PREVIEW_API_BASE_URL" ] && [ -n "$PRODUCTION_API_BASE_URL" ]; then
  python3 "$SCRIPT_DIR/contract-drift-check.py"
  echo "✓ Environment-state drift check passed"
else
  echo "⚠ PREVIEW_API_BASE_URL or PRODUCTION_API_BASE_URL not set; skipping drift check"
fi

echo ""
echo "Verification checklist passed."
echo "- API health responds"
echo "- Worker liveness semantics are healthy"
echo "- Frontend can reach the configured API"
echo "- Score status read path is verified"
echo "- Drift check is enforced when preview and production URLs are provided"
