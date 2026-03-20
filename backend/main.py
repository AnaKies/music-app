import os
import time

from fastapi import FastAPI, Response, status
from fastapi.middleware.cors import CORSMiddleware
from backend.database import engine, Base, run_startup_migrations
from backend.api.routes import cases, interviews, recommendations, scores, transformations
from backend.domain.interviews.models import InterviewSession  # noqa: F401
from backend.domain.recommendations.models import RangeRecommendation  # noqa: F401
from backend.domain.scores.models import ScoreDocument  # noqa: F401
from backend.domain.transformations.models import TransformationJob  # noqa: F401

# Tabellen erstellen (im MVP bei jedem Start zur Sicherheit, sqlite)
Base.metadata.create_all(bind=engine)
run_startup_migrations()

app = FastAPI(title="MusicApp API")


def _load_allowed_origins() -> list[str]:
    configured_origins = os.getenv("CORS_ALLOW_ORIGINS", "").strip()
    if configured_origins:
        return [origin.strip() for origin in configured_origins.split(",") if origin.strip()]

    return [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_load_allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routen einbinden
app.include_router(cases.router)
app.include_router(interviews.router)
app.include_router(recommendations.router)
app.include_router(scores.router)
app.include_router(transformations.router)

@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/health/worker")
def worker_health_check(response: Response):
    worker_runtime = os.getenv("WORKER_RUNTIME_MODE", "inline_mvp")
    worker_liveness = os.getenv("WORKER_LIVENESS_STATUS", "").strip()
    worker_heartbeat_file = os.getenv("WORKER_HEARTBEAT_FILE", "").strip()
    worker_heartbeat_ttl_seconds = int(os.getenv("WORKER_HEARTBEAT_TTL_SECONDS", "15"))

    if worker_runtime == "inline_mvp":
        return {
            "status": "ok",
            "runtime": "inline_mvp",
            "workerMode": "api-process-inline",
            "safeSummary": "The MVP worker path is available through the API process.",
        }

    if worker_liveness == "healthy":
        return {
            "status": "ok",
            "runtime": worker_runtime,
            "workerMode": "separate-worker-runtime",
            "safeSummary": "The worker runtime responded to the current liveness check.",
        }

    if worker_heartbeat_file:
        try:
            heartbeat_age_seconds = time.time() - os.path.getmtime(worker_heartbeat_file)
        except OSError:
            heartbeat_age_seconds = None

        if heartbeat_age_seconds is not None and heartbeat_age_seconds <= worker_heartbeat_ttl_seconds:
            return {
                "status": "ok",
                "runtime": worker_runtime,
                "workerMode": "separate-worker-runtime",
                "safeSummary": "The worker runtime responded to the current liveness check.",
            }

    response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return {
        "status": "failed",
        "runtime": worker_runtime,
        "workerMode": "separate-worker-runtime",
        "safeSummary": "The expected worker runtime did not respond to the liveness check.",
    }
