from fastapi import APIRouter, Depends, File, Form, Response, UploadFile, status
from sqlalchemy.orm import Session

from backend.api.schemas.scores import ScorePreviewResponse, ScoreUploadResponse
from backend.database import get_db
from backend.services.scores.service import (
    accept_score_upload,
    get_source_score_preview,
    get_source_score_preview_content,
)

router = APIRouter(tags=["scores"])


@router.post(
    "/scores",
    response_model=ScoreUploadResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def post_score(
    transpositionCaseId: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> ScoreUploadResponse:
    return accept_score_upload(
        db=db,
        transposition_case_id=transpositionCaseId,
        upload=file,
    )


@router.get(
    "/scores/{score_id}/preview",
    response_model=ScorePreviewResponse,
    status_code=status.HTTP_200_OK,
)
def get_score_preview(
    score_id: str,
    db: Session = Depends(get_db),
) -> ScorePreviewResponse:
    return get_source_score_preview(
        db=db,
        score_document_id=score_id,
    )


@router.get(
    "/scores/{score_id}/preview/content",
    status_code=status.HTTP_200_OK,
)
def get_score_preview_content(
    score_id: str,
    db: Session = Depends(get_db),
) -> Response:
    return get_source_score_preview_content(
        db=db,
        score_document_id=score_id,
    )
