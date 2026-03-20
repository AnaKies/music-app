from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from backend.api.schemas.transformations import TransformationRequest, TransformationResponse
from backend.database import get_db
from backend.services.transformations.service import (
    create_transformation,
    get_transformation_preview_content,
)

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


@router.get(
    "/transformations/{transformation_id}/preview/content",
    status_code=status.HTTP_200_OK,
)
def get_transformation_result_preview_content(
    transformation_id: str,
    revision: str = Query(...),
    db: Session = Depends(get_db),
) -> Response:
    return get_transformation_preview_content(
        db=db,
        transformation_job_id=transformation_id,
        revision=revision,
    )
