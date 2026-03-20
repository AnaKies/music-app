# MusicApp Development Scripts

Quick start scripts for running the MusicApp development environment.

## Quick Start

### Start Both Servers

```bash
./scripts/start.sh
```

This will:
- Start the Backend (FastAPI) on http://localhost:8000
- Start the Frontend (Next.js) on http://localhost:3000
- Show API documentation at http://localhost:8000/docs

### Stop Both Servers

```bash
./scripts/stop.sh
```

Or press `Ctrl+C` in the terminal where `start.sh` is running.

### Start Preview Infrastructure

```bash
./scripts/preview/start-preview.sh
```

This starts the shareable preview topology with separate:
- Frontend runtime on http://localhost:3000
- API runtime on http://localhost:8000
- Worker heartbeat runtime for deploy verification

### Stop Preview Infrastructure

```bash
./scripts/preview/stop-preview.sh
```

## Manual Start (Alternative)

If you prefer to start servers separately:

### Backend Only

```bash
cd backend
python3 -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Only

```bash
cd frontend
export NEXT_PUBLIC_API_URL="http://localhost:8000"
npm run dev
```

## Access Points

| Service | URL | Description |
|---------|-----|-------------|
| Frontend | http://localhost:3000 | Main application |
| Backend API | http://localhost:8000 | REST API |
| API Docs | http://localhost:8000/docs | Swagger/OpenAPI documentation |
| Health Check | http://localhost:8000/health | Backend health status |
| Worker Health | http://localhost:8000/health/worker | Worker liveness signal with explicit runtime semantics |

## Requirements

- **Python 3.9+** with pip
- **Node.js 18+** with npm
- **curl** (for health checks in start script)

## Troubleshooting

### Port Already in Use

If port 8000 or 3000 is already in use:

```bash
# Stop all servers
./scripts/stop.sh

# Or manually kill processes
kill -9 $(lsof -ti:8000)
kill -9 $(lsof -ti:3000)
```

### Dependencies Missing

```bash
# Install Python dependencies
cd backend
python3 -m pip install fastapi uvicorn sqlalchemy pydantic python-multipart

# Install Node.js dependencies
cd frontend
npm install
```

### Backend Not Starting

Check Python version:
```bash
python3 --version  # Should be 3.9+
```

### Frontend Not Starting

Check Node.js version:
```bash
node --version  # Should be 18+
npm --version
```

## Environment Variables

### Frontend (.env.local)

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Preview Environment

Preview configuration is isolated in:

[`infra/environments/preview/preview.env`](/Users/anastasiakiessig/Library/Mobile%20Documents/com~apple~CloudDocs/AI_project/MusicApp/infra/environments/preview/preview.env)

Template:

[`infra/environments/preview/preview.env.example`](/Users/anastasiakiessig/Library/Mobile%20Documents/com~apple~CloudDocs/AI_project/MusicApp/infra/environments/preview/preview.env.example)

## Testing

### Run Backend Tests

```bash
cd backend
python3 -m pytest tests/
```

### Run Frontend Tests

```bash
cd frontend
npm test -- --run
```

### Run Preview Smoke Verification

```bash
API_BASE_URL=http://localhost:8000 \
FRONTEND_BASE_URL=http://localhost:3000 \
SCORE_ID=<existing-score-id> \
./scripts/verification/preview-smoke.sh
```

If you intentionally want to skip the score-status gate:

```bash
API_BASE_URL=http://localhost:8000 \
FRONTEND_BASE_URL=http://localhost:3000 \
ALLOW_SKIP_SCORE_STATUS=true \
./scripts/verification/preview-smoke.sh
```

### Run Post-Deploy Checklist

```bash
API_BASE_URL=http://localhost:8000 \
FRONTEND_BASE_URL=http://localhost:3000 \
SCORE_ID=<existing-score-id> \
./scripts/verification/post-deploy-checklist.sh
```

Optional environment-state drift verification:

```bash
PREVIEW_API_BASE_URL=http://preview-api.example \
PRODUCTION_API_BASE_URL=http://prod-api.example \
SCORE_ID=<shared-score-id> \
TRANSFORMATION_ID=<optional-shared-transformation-id> \
python3 ./scripts/verification/contract-drift-check.py
```

Notes:
- `preview-smoke.sh` now treats score-status verification as required by default.
- The frontend-to-backend check uses `GET /api/health/backend` on the frontend, so a broken frontend API configuration becomes visible.
- `GET /health/worker` reports inline-MVP health by default, but in preview it uses the worker heartbeat file from `preview.env` to distinguish a healthy worker from an absent one.
- The preview topology is defined in [`infra/deployment/docker-compose.preview.yml`](/Users/anastasiakiessig/Library/Mobile%20Documents/com~apple~CloudDocs/AI_project/MusicApp/infra/deployment/docker-compose.preview.yml).
- Preview uses `NEXT_PUBLIC_API_URL=http://localhost:8000` for browser requests and `INTERNAL_API_BASE_URL=http://api:8000` for server-side frontend probes inside Compose.

## Logs

Both servers output logs to the terminal. When running `start.sh`, you'll see interleaved logs from both backend and frontend.

To see only backend logs:
```bash
cd backend
python3 -m uvicorn main:app --reload
```

To see only frontend logs:
```bash
cd frontend
npm run dev
```
