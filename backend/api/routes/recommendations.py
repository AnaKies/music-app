from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.api.schemas.recommendations import RecommendationContext, RecommendationContextRequest
from backend.database import get_db
from backend.services.recommendations.context import build_recommendation_context

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
