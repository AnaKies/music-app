#!/bin/bash

################################################################################
# MusicApp Development Server Stopper
# 
# This script stops all running MusicApp development servers (backend and frontend).
#
# Usage: ./scripts/stop.sh
#
################################################################################

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

wait_for_port_release() {
    local port="$1"
    local retries="${2:-20}"

    for _ in $(seq 1 "$retries"); do
        if ! lsof -ti:"$port" >/dev/null 2>&1; then
            return 0
        fi
        sleep 1
    done

    return 1
}

force_release_port() {
    local port="$1"
    local pids

    pids=$(lsof -ti:"$port" 2>/dev/null || true)
    if [ -n "$pids" ]; then
        kill -9 $pids 2>/dev/null || true
    fi
}

echo -e "${YELLOW}Stopping MusicApp development servers...${NC}"
echo ""

# Kill backend processes (uvicorn on port 8000)
echo -e "${YELLOW}Stopping Backend...${NC}"
BACKEND_PIDS=$(lsof -ti:8000 2>/dev/null || true)
if [ ! -z "$BACKEND_PIDS" ]; then
    kill $BACKEND_PIDS 2>/dev/null || true
    echo -e "${GREEN}✓ Backend stopped (PID: $BACKEND_PIDS)${NC}"
else
    echo -e "${GREEN}✓ No backend process found${NC}"
fi

# Kill frontend processes (next.js on port 3000)
echo -e "${YELLOW}Stopping Frontend...${NC}"
FRONTEND_PIDS=$(lsof -ti:3000 2>/dev/null || true)
if [ ! -z "$FRONTEND_PIDS" ]; then
    kill $FRONTEND_PIDS 2>/dev/null || true
    echo -e "${GREEN}✓ Frontend stopped (PID: $FRONTEND_PIDS)${NC}"
else
    echo -e "${GREEN}✓ No frontend process found${NC}"
fi

# Also kill any node processes related to next.js
NODE_PIDS=$(pgrep -f "next dev" 2>/dev/null || true)
if [ ! -z "$NODE_PIDS" ]; then
    kill $NODE_PIDS 2>/dev/null || true
    echo -e "${GREEN}✓ Next.js dev server stopped${NC}"
fi

# Also kill any python processes related to uvicorn
UVICORN_PIDS=$(pgrep -f "uvicorn backend.main:app" 2>/dev/null || true)
if [ ! -z "$UVICORN_PIDS" ]; then
    kill $UVICORN_PIDS 2>/dev/null || true
    echo -e "${GREEN}✓ Uvicorn server stopped${NC}"
fi

if ! wait_for_port_release 8000 10; then
    echo -e "${YELLOW}Backend port 8000 is still busy, forcing shutdown...${NC}"
    force_release_port 8000
    if ! wait_for_port_release 8000 5; then
        echo -e "${RED}✗ Backend port 8000 is still busy after forced stop${NC}"
        exit 1
    fi
fi

if ! wait_for_port_release 3000 10; then
    echo -e "${YELLOW}Frontend port 3000 is still busy, forcing shutdown...${NC}"
    force_release_port 3000
    if ! wait_for_port_release 3000 5; then
        echo -e "${RED}✗ Frontend port 3000 is still busy after forced stop${NC}"
        exit 1
    fi
fi

echo ""
echo -e "${GREEN}╔════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║   All servers stopped successfully    ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════╝${NC}"
