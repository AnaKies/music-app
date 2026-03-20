from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Response, UploadFile, status
from sqlalchemy.orm import Session

from backend.api.schemas.scores import ScorePreviewResponse, ScoreReadResponse, ScoreUploadResponse
from backend.database import get_db
from backend.services.scores.service import (
    accept_score_upload,
    get_result_score_download,
    get_score_read,
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
    "/scores/{score_id}",
    response_model=ScoreReadResponse,
    status_code=status.HTTP_200_OK,
)
def get_score(
    score_id: str,
    db: Session = Depends(get_db),
) -> ScoreReadResponse:
    return get_score_read(
        db=db,
        score_document_id=score_id,
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
    revision: str = Query(...),
    db: Session = Depends(get_db),
) -> Response:
    return get_source_score_preview_content(
        db=db,
        score_document_id=score_id,
        revision=revision,
    )


@router.get(
    "/scores/{score_id}/download",
    status_code=status.HTTP_200_OK,
)
def get_score_download(
    score_id: str,
    artifact: str = Query(...),
    db: Session = Depends(get_db),
) -> Response:
    if artifact != "result":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Only result artifact downloads are supported.",
        )

    return get_result_score_download(
        db=db,
        score_document_id=score_id,
    )
