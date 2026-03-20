#!/bin/bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
COMPOSE_FILE="$PROJECT_ROOT/infra/deployment/docker-compose.preview.yml"
ENV_FILE="$PROJECT_ROOT/infra/environments/preview/preview.env"

docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" down

echo "Preview environment stopped."
