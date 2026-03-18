from fastapi import FastAPI

from backend.api.routes import api_router


def create_app() -> FastAPI:
    app = FastAPI(
        title="MusicApp Backend API",
        version="0.1.0",
        description="Minimal backend scaffold for transposition case creation.",
    )
    app.include_router(api_router)
    return app


app = create_app()
