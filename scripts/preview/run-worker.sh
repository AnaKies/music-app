#!/bin/sh

set -eu

HEARTBEAT_DIR="${WORKER_HEARTBEAT_DIR:-/tmp/musicapp-worker}"
HEARTBEAT_FILE="${WORKER_HEARTBEAT_FILE:-$HEARTBEAT_DIR/heartbeat}"
HEARTBEAT_INTERVAL_SECONDS="${WORKER_HEARTBEAT_INTERVAL_SECONDS:-5}"

mkdir -p "$HEARTBEAT_DIR"

echo "MusicApp preview worker heartbeat started"
echo "Heartbeat file: $HEARTBEAT_FILE"

while true; do
  date -u +"%Y-%m-%dT%H:%M:%SZ" > "$HEARTBEAT_FILE"
  sleep "$HEARTBEAT_INTERVAL_SECONDS"
done
