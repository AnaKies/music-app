from fastapi import APIRouter

from .cases import router as cases_router
from .interviews import router as interviews_router
from .scores import router as scores_router

api_router = APIRouter()
api_router.include_router(cases_router)
api_router.include_router(interviews_router)
api_router.include_router(scores_router)
