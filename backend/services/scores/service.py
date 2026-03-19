from datetime import datetime, timezone
from pathlib import Path

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from backend.api.schemas.cases import CaseStatus
from backend.api.schemas.scores import (
    ScoreFormat,
    ScoreProcessingSnapshot,
    ScoreProcessingStatus,
    ScoreUploadResponse,
)
from backend.domain.cases.models import TranspositionCase
from backend.domain.scores.models import ScoreDocument

MAX_UPLOAD_SIZE_BYTES = 5 * 1024 * 1024
ALLOWED_SUFFIXES = {".musicxml", ".xml"}
MUSICXML_MARKERS = ("<score-partwise", "<score-timewise")


def accept_score_upload(
    db: Session,
    transposition_case_id: str,
    upload: UploadFile,
) -> ScoreUploadResponse:
    case = db.query(TranspositionCase).filter(TranspositionCase.id == transposition_case_id).first()
    if case is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Case with id {transposition_case_id} not found.",
        )

    if case.status != CaseStatus.READY_FOR_UPLOAD:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="The selected case is not ready for score upload.",
        )

    filename = upload.filename or ""
    suffix = Path(filename).suffix.lower()
    if suffix not in ALLOWED_SUFFIXES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Only MusicXML uploads are supported.",
        )

    content = upload.file.read()
    content_size = len(content)
    if content_size > MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="The uploaded file exceeds the maximum allowed size.",
        )

    decoded = content.decode("utf-8", errors="ignore")
    if not any(marker in decoded for marker in MUSICXML_MARKERS):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="The uploaded file is not valid MusicXML.",
        )

    score_document = ScoreDocument(
        transposition_case_id=transposition_case_id,
        original_filename=filename,
        format=ScoreFormat.MUSICXML,
        processing_status=ScoreProcessingStatus.UPLOADED,
        storage_uri=f"local://scores/{transposition_case_id}/{filename}",
        content_size=content_size,
    )
    db.add(score_document)
    db.commit()
    db.refresh(score_document)
    db.refresh(case)

    accepted_at = score_document.created_at or datetime.now(timezone.utc)
    return ScoreUploadResponse(
        scoreDocumentId=score_document.id,
        format=score_document.format,
        acceptedStatus=score_document.processing_status,
        originalFilename=score_document.original_filename,
        initialProcessingSnapshot=ScoreProcessingSnapshot(
            scoreDocumentId=score_document.id,
            transpositionCaseId=transposition_case_id,
            processingStatus=score_document.processing_status,
            acceptedAt=accepted_at,
        ),
    )
