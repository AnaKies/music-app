from fastapi import FastAPI
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

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
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
