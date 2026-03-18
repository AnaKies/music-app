from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.database import engine, Base
from backend.api.routes import cases

# Tabellen erstellen (im MVP bei jedem Start zur Sicherheit, sqlite)
Base.metadata.create_all(bind=engine)

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

@app.get("/health")
def health_check():
    return {"status": "ok"}
