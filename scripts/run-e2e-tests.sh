#!/bin/bash

# E2E Test Runner for MusicApp
# Starts backend and frontend servers, then runs Playwright tests

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
FRONTEND_DIR="$PROJECT_ROOT/frontend"
BACKEND_DIR="$PROJECT_ROOT"

echo "========================================="
echo "MusicApp E2E Test Runner"
echo "========================================="
echo ""

# Cleanup function
cleanup() {
  echo ""
  echo "Cleaning up..."
  
  if [ ! -z "$BACKEND_PID" ]; then
    echo "Stopping backend (PID: $BACKEND_PID)..."
    kill $BACKEND_PID 2>/dev/null || true
  fi
  
  if [ ! -z "$FRONTEND_PID" ]; then
    echo "Stopping frontend (PID: $FRONTEND_PID)..."
    kill $FRONTEND_PID 2>/dev/null || true
  fi
  
  # Wait for processes to stop
  sleep 2
  echo "Cleanup complete."
}

# Trap to ensure cleanup runs on exit
trap cleanup EXIT

# Activate virtual environment for backend if it exists
if [ -f "$PROJECT_ROOT/venv/bin/activate" ]; then
  echo "Activating Python virtual environment..."
  source "$PROJECT_ROOT/venv/bin/activate"
fi

# Start backend server
echo "Starting backend server..."
cd "$BACKEND_DIR"
python3 -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
echo "Backend started (PID: $BACKEND_PID)"

# Wait for backend to be ready
echo "Waiting for backend to be ready..."
for i in {1..30}; do
  if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "Backend is ready!"
    break
  fi
  if [ $i -eq 30 ]; then
    echo "ERROR: Backend failed to start within 30 seconds"
    exit 1
  fi
  sleep 1
done

# Start frontend server
echo "Starting frontend server..."
cd "$FRONTEND_DIR"
npm run dev &
FRONTEND_PID=$!
echo "Frontend started (PID: $FRONTEND_PID)"

# Wait for frontend to be ready
echo "Waiting for frontend to be ready..."
for i in {1..60}; do
  if curl -s http://localhost:3000 > /dev/null 2>&1; then
    echo "Frontend is ready!"
    break
  fi
  if [ $i -eq 60 ]; then
    echo "ERROR: Frontend failed to start within 60 seconds"
    exit 1
  fi
  sleep 1
done

echo ""
echo "========================================="
echo "Running Playwright E2E Tests"
echo "========================================="
echo ""

# Run Playwright tests
cd "$FRONTEND_DIR"
npx playwright test

# Capture test exit code
TEST_EXIT_CODE=$?

echo ""
echo "========================================="
if [ $TEST_EXIT_CODE -eq 0 ]; then
  echo "✅ All E2E tests passed!"
else
  echo "❌ Some E2E tests failed (exit code: $TEST_EXIT_CODE)"
fi
echo "========================================="

# Exit with test exit code
exit $TEST_EXIT_CODE
