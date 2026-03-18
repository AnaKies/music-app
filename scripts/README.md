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
