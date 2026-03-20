from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.api.schemas.recommendations import (
    RecommendationContext,
    RecommendationContextRequest,
    RecommendationResponse,
)
from backend.database import get_db
from backend.services.recommendations.context import build_recommendation_context
from backend.services.recommendations.generation import generate_recommendations, get_recommendations_read

router = APIRouter(tags=["recommendations"])


@router.post("/recommendations/context", response_model=RecommendationContext)
def post_recommendation_context(
    payload: RecommendationContextRequest,
    db: Session = Depends(get_db),
) -> RecommendationContext:
    return build_recommendation_context(
        db=db,
        transposition_case_id=payload.transpositionCaseId,
        score_document_id=payload.scoreDocumentId,
    )


@router.post("/recommendations", response_model=RecommendationResponse)
def post_recommendations(
    payload: RecommendationContextRequest,
    db: Session = Depends(get_db),
) -> RecommendationResponse:
    return generate_recommendations(
        db=db,
        transposition_case_id=payload.transpositionCaseId,
        score_document_id=payload.scoreDocumentId,
    )


@router.get("/recommendations", response_model=RecommendationResponse)
def get_recommendations(
    transpositionCaseId: str,
    scoreDocumentId: str,
    db: Session = Depends(get_db),
) -> RecommendationResponse:
    return get_recommendations_read(
        db=db,
        transposition_case_id=transpositionCaseId,
        score_document_id=scoreDocumentId,
    )
