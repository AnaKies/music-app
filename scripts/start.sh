#!/bin/bash

################################################################################
# MusicApp Development Server Starter
# 
# This script starts both the backend (FastAPI) and frontend (Next.js) servers
# for local development.
#
# Usage: ./scripts/start.sh
#
# Requirements:
#   - Python 3.9+
#   - Node.js 18+
#   - npm
#
# Stops with Ctrl+C
################################################################################

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo -e "${BLUE}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   MusicApp Development Server Starter                 ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check if we're in the right directory
if [ ! -f "$PROJECT_ROOT/backend/main.py" ]; then
    echo -e "${RED}Error: backend/main.py not found${NC}"
    echo "Please run this script from the project root directory."
    exit 1
fi

if [ ! -f "$PROJECT_ROOT/frontend/package.json" ]; then
    echo -e "${RED}Error: frontend/package.json not found${NC}"
    echo "Please run this script from the project root directory."
    exit 1
fi

# Stop any existing servers first
echo -e "${YELLOW}Checking for existing servers...${NC}"
EXISTING_BACKEND=$(lsof -ti:8000 2>/dev/null || true)
EXISTING_FRONTEND=$(lsof -ti:3000 2>/dev/null || true)

if [ ! -z "$EXISTING_BACKEND" ] || [ ! -z "$EXISTING_FRONTEND" ]; then
    echo -e "${YELLOW}Found existing servers, stopping them...${NC}"
    pkill -f "uvicorn backend.main:app" 2>/dev/null || true
    if [ ! -z "$EXISTING_BACKEND" ]; then
        kill $EXISTING_BACKEND 2>/dev/null || true
    fi
    pkill -f "next dev" 2>/dev/null || true
    if [ ! -z "$EXISTING_FRONTEND" ]; then
        kill $EXISTING_FRONTEND 2>/dev/null || true
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

    echo -e "${GREEN}✓ Existing servers stopped${NC}"
    echo ""
fi

# Function to cleanup on exit
cleanup() {
    echo ""
    echo -e "${YELLOW}Shutting down servers...${NC}"
    
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null || true
        echo -e "${GREEN}✓ Backend stopped${NC}"
    fi
    
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null || true
        echo -e "${GREEN}✓ Frontend stopped${NC}"
    fi
    
    exit 0
}

# Trap Ctrl+C and call cleanup
trap cleanup SIGINT SIGTERM

# Start Backend
echo -e "${GREEN}Starting Backend Server...${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
cd "$PROJECT_ROOT/backend"

# Check if dependencies are installed
if ! python3 -c "import fastapi" 2>/dev/null; then
    echo -e "${YELLOW}Installing Python dependencies...${NC}"
    python3 -m pip install fastapi uvicorn sqlalchemy pydantic python-multipart 2>/dev/null || \
    python3 -m pip install fastapi uvicorn sqlalchemy pydantic python-multipart --user
fi

# Start backend in background
export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"
python3 -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# Wait for backend to be ready
echo -e "${YELLOW}Waiting for backend to be ready...${NC}"
for i in {1..30}; do
    if curl -s http://localhost:8000/health >/dev/null 2>&1; then
        echo -e "${GREEN}✓ Backend is ready on http://localhost:8000${NC}"
        echo -e "${GREEN}  API Docs: http://localhost:8000/docs${NC}"
        break
    fi
    if [ $i -eq 30 ]; then
        echo -e "${RED}✗ Backend failed to start${NC}"
        exit 1
    fi
    sleep 1
done

echo ""

# Start Frontend
echo -e "${GREEN}Starting Frontend Server...${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
cd "$PROJECT_ROOT/frontend"

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}Installing npm dependencies...${NC}"
    npm install --silent
fi

# Set API URL environment variable
export NEXT_PUBLIC_API_URL="http://localhost:8000"

# Start frontend in background
npm run dev &
FRONTEND_PID=$!

# Wait for frontend to be ready
echo -e "${YELLOW}Waiting for frontend to be ready...${NC}"
for i in {1..30}; do
    if curl -s http://localhost:3000 >/dev/null 2>&1; then
        echo -e "${GREEN}✓ Frontend is ready on http://localhost:3000${NC}"
        break
    fi
    if [ $i -eq 30 ]; then
        echo -e "${RED}✗ Frontend failed to start${NC}"
        exit 1
    fi
    sleep 1
done

echo ""
echo -e "${BLUE}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   Servers Running                                     ║${NC}"
echo -e "${BLUE}╠════════════════════════════════════════════════════════╣${NC}"
echo -e "${BLUE}║${NC}                                                      ${BLUE}║${NC}"
echo -e "${BLUE}║${NC}  ${GREEN}✓ Backend:${NC}  http://localhost:8000                    ${BLUE}║${NC}"
echo -e "${BLUE}║${NC}  ${GREEN}✓ API Docs:${NC} http://localhost:8000/docs               ${BLUE}║${NC}"
echo -e "${BLUE}║${NC}  ${GREEN}✓ Frontend:${NC} http://localhost:3000                    ${BLUE}║${NC}"
echo -e "${BLUE}║${NC}                                                      ${BLUE}║${NC}"
echo -e "${BLUE}╠════════════════════════════════════════════════════════╣${NC}"
echo -e "${BLUE}║${NC}  Press ${YELLOW}Ctrl+C${NC} to stop all servers                   ${BLUE}║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════╝${NC}"
echo ""

# Wait for both processes
wait
