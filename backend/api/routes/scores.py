from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from sqlalchemy.orm import Session

from backend.api.schemas.scores import ScoreUploadResponse
from backend.database import get_db
from backend.services.scores.service import accept_score_upload

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
