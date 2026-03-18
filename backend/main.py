from fastapi import FastAPI
from backend.database import engine, Base
from backend.api.routes import cases

# Tabellen erstellen (im MVP bei jedem Start zur Sicherheit, sqlite)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="MusicApp API")

# Routen einbinden
app.include_router(cases.router)

@app.get("/health")
def health_check():
    return {"status": "ok"}
