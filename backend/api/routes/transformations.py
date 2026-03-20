from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from backend.api.schemas.transformations import TransformationRequest, TransformationResponse
from backend.database import get_db
from backend.services.transformations.service import create_transformation

router = APIRouter(tags=["transformations"])


@router.post("/transformations", response_model=TransformationResponse, status_code=status.HTTP_202_ACCEPTED)
def post_transformation(
    payload: TransformationRequest,
    db: Session = Depends(get_db),
) -> TransformationResponse:
    return create_transformation(
        db=db,
        transposition_case_id=payload.transpositionCaseId,
        score_document_id=payload.scoreDocumentId,
        recommendation_id=payload.recommendationId,
    )
