from datetime import datetime, timezone
from pathlib import Path

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from backend.api.schemas.cases import CaseStatus
from backend.api.schemas.scores import (
    CanonicalScorePartSummary,
    CanonicalScoreSummary,
    ScoreFormat,
    ScoreProcessingSnapshot,
    ScoreProcessingStatus,
    ScoreUploadResponse,
)
from backend.domain.cases.models import TranspositionCase
from backend.domain.scores.models import CanonicalScore, ScoreDocument
from backend.services.scores.parser import parse_musicxml

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

    parse_result = parse_musicxml(content)
    canonical_summary = None
    parse_failure_type = None

    if parse_result.failure is not None:
        score_document.processing_status = ScoreProcessingStatus.PARSE_FAILED
        score_document.parse_failure_type = parse_result.failure.failure_type
        parse_failure_type = parse_result.failure.failure_type
    elif parse_result.canonical_score is not None:
        score_document.processing_status = ScoreProcessingStatus.PARSED
        score_document.parse_failure_type = None
        db.add(
            CanonicalScore(
                score_document_id=score_document.id,
                schema_version=parse_result.canonical_score.schema_version,
                title=parse_result.canonical_score.title,
                parts=parse_result.canonical_score.parts,
                measure_count=parse_result.canonical_score.measure_count,
                note_count=parse_result.canonical_score.note_count,
                rest_count=parse_result.canonical_score.rest_count,
            )
        )

    db.commit()
    db.refresh(score_document)
    db.refresh(case)

    if score_document.canonical_score is not None:
        canonical_summary = CanonicalScoreSummary(
            schemaVersion=score_document.canonical_score.schema_version,
            title=score_document.canonical_score.title,
            partCount=len(score_document.canonical_score.parts or []),
            measureCount=score_document.canonical_score.measure_count,
            noteCount=score_document.canonical_score.note_count,
            restCount=score_document.canonical_score.rest_count,
            parts=[
                CanonicalScorePartSummary(
                    partId=part.get("id", ""),
                    name=part.get("name", ""),
                )
                for part in (score_document.canonical_score.parts or [])
            ],
        )

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
            parseFailureType=parse_failure_type,
            canonicalScoreSummary=canonical_summary,
        ),
    )
