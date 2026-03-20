from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path
from typing import Optional
from urllib.parse import quote
from zipfile import BadZipFile, ZipFile

from fastapi import HTTPException, Response, UploadFile, status
from sqlalchemy.orm import Session

from backend.api.schemas.cases import CaseStatus
from backend.api.schemas.scores import (
    CanonicalScorePartSummary,
    CanonicalScoreSummary,
    ScoreArtifactRole,
    ScoreFormat,
    ScorePreviewAvailability,
    ScorePreviewResponse,
    ScoreReadResponse,
    ScoreProcessingSnapshot,
    ScoreProcessingStatus,
    ScoreUploadResponse,
)
from backend.domain.cases.models import TranspositionCase
from backend.domain.recommendations.models import RangeRecommendation
from backend.domain.scores.models import CanonicalScore, ScoreDocument
from backend.domain.transformations.models import TransformationJob
from backend.services.shared.musicxml import ensure_xml_declaration
from backend.services.scores.parser import parse_musicxml

MAX_UPLOAD_SIZE_BYTES = 5 * 1024 * 1024
ALLOWED_SUFFIXES = {".musicxml", ".xml", ".mxl"}
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
            detail="Only MusicXML-family uploads (.musicxml, .xml, .mxl) are supported.",
        )

    content = upload.file.read()
    content_size = len(content)
    if content_size > MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail="The uploaded file exceeds the maximum allowed size.",
        )

    xml_payload = _extract_musicxml_payload(content=content, suffix=suffix)

    score_document = ScoreDocument(
        transposition_case_id=transposition_case_id,
        original_filename=filename,
        format=ScoreFormat.MUSICXML,
        processing_status=ScoreProcessingStatus.UPLOADED,
        storage_uri=f"local://scores/{transposition_case_id}/{filename}",
        source_musicxml=xml_payload.decode("utf-8", errors="ignore"),
        content_size=content_size,
    )
    db.add(score_document)
    db.commit()
    db.refresh(score_document)

    parse_result = parse_musicxml(xml_payload)
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


def get_source_score_preview(
    db: Session,
    score_document_id: str,
) -> ScorePreviewResponse:
    score_document = db.query(ScoreDocument).filter(ScoreDocument.id == score_document_id).first()
    if score_document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Score with id {score_document_id} not found.",
        )

    return _build_source_score_preview(score_document)


def get_score_read(
    db: Session,
    score_document_id: str,
) -> ScoreReadResponse:
    score_document = db.query(ScoreDocument).filter(ScoreDocument.id == score_document_id).first()
    if score_document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Score with id {score_document_id} not found.",
        )

    source_preview = _build_source_score_preview(score_document)
    recommendations_exist = (
        db.query(RangeRecommendation.id)
        .filter(RangeRecommendation.score_document_id == score_document.id)
        .first()
        is not None
    )
    processing_status = _derive_read_processing_status(score_document, recommendations_exist)

    return ScoreReadResponse(
        scoreDocumentId=score_document.id,
        transpositionCaseId=score_document.transposition_case_id,
        processingStatus=processing_status,
        originalFilename=score_document.original_filename,
        safeSummary=_build_score_safe_summary(processing_status),
        sourcePreview=source_preview,
        resultPreview=_build_result_score_preview(db, score_document),
    )


def _build_source_score_preview(score_document: ScoreDocument) -> ScorePreviewResponse:
    canonical_summary = _build_canonical_summary(score_document)
    revision_token = _build_revision_token(score_document)

    if (
        score_document.processing_status == ScoreProcessingStatus.PARSED
        and canonical_summary is not None
        and score_document.source_musicxml
    ):
        return ScorePreviewResponse(
            scoreDocumentId=score_document.id,
            artifactRole=ScoreArtifactRole.SOURCE,
            availability=ScorePreviewAvailability.READY,
            rendererFormat="musicxml_preview",
            pageCount=max(canonical_summary.partCount, 1),
            revisionToken=revision_token,
            safeSummary="The uploaded score is ready for read-only preview.",
            previewAccess=f"/scores/{score_document.id}/preview/content?revision={quote(revision_token, safe='')}",
            originalFilename=score_document.original_filename,
            canonicalScoreSummary=canonical_summary,
        )

    if score_document.processing_status == ScoreProcessingStatus.PARSED and canonical_summary is not None:
        return ScorePreviewResponse(
            scoreDocumentId=score_document.id,
            artifactRole=ScoreArtifactRole.SOURCE,
            availability=ScorePreviewAvailability.UNAVAILABLE,
            rendererFormat="musicxml_preview",
            pageCount=max(canonical_summary.partCount, 1),
            revisionToken=revision_token,
            safeSummary="This older uploaded score does not have preview content stored yet. Upload it again to render the notation preview.",
            originalFilename=score_document.original_filename,
            canonicalScoreSummary=canonical_summary,
        )

    if score_document.processing_status == ScoreProcessingStatus.PARSE_FAILED:
        failure_code = score_document.parse_failure_type.value if score_document.parse_failure_type is not None else "parse_failed"
        return ScorePreviewResponse(
            scoreDocumentId=score_document.id,
            artifactRole=ScoreArtifactRole.SOURCE,
            availability=ScorePreviewAvailability.FAILED,
            revisionToken=revision_token,
            safeSummary="The uploaded score could not be prepared for preview.",
            failureCode=failure_code,
            failureSeverity="warning",
            originalFilename=score_document.original_filename,
        )

    return ScorePreviewResponse(
        scoreDocumentId=score_document.id,
        artifactRole=ScoreArtifactRole.SOURCE,
        availability=ScorePreviewAvailability.NOT_READY,
        revisionToken=revision_token,
        safeSummary="The uploaded score is not ready for preview yet.",
        originalFilename=score_document.original_filename,
    )


def _build_result_score_preview(db: Session, score_document: ScoreDocument) -> ScorePreviewResponse:
    transformation_job = (
        db.query(TransformationJob)
        .filter(
            TransformationJob.score_document_id == score_document.id,
            TransformationJob.result_storage_uri.isnot(None),
            TransformationJob.result_revision_token.isnot(None),
        )
        .order_by(TransformationJob.created_at.desc())
        .first()
    )
    if transformation_job is not None and transformation_job.transformed_musicxml and transformation_job.result_revision_token:
        canonical_summary = _build_transformed_summary(transformation_job.transformed_musicxml)
        return ScorePreviewResponse(
            scoreDocumentId=score_document.id,
            artifactRole=ScoreArtifactRole.RESULT,
            availability=ScorePreviewAvailability.READY,
            rendererFormat="musicxml_preview",
            pageCount=max(canonical_summary.partCount, 1) if canonical_summary is not None else 1,
            revisionToken=transformation_job.result_revision_token,
            safeSummary="A transformed result artifact is ready for read-only preview.",
            previewAccess=(
                f"/transformations/{transformation_job.id}/preview/content"
                f"?revision={quote(transformation_job.result_revision_token, safe='')}"
            ),
            originalFilename=transformation_job.result_filename or score_document.original_filename,
            canonicalScoreSummary=canonical_summary,
        )

    return ScorePreviewResponse(
        scoreDocumentId=score_document.id,
        artifactRole=ScoreArtifactRole.RESULT,
        availability=ScorePreviewAvailability.UNAVAILABLE,
        revisionToken=_build_revision_token(score_document),
        safeSummary="A result preview is not available yet because no transformed result artifact exists.",
        originalFilename=score_document.original_filename,
    )


def _build_canonical_summary(score_document: ScoreDocument) -> Optional[CanonicalScoreSummary]:
    if score_document.canonical_score is None:
        return None

    return CanonicalScoreSummary(
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


def _build_transformed_summary(transformed_musicxml: str) -> Optional[CanonicalScoreSummary]:
    parse_result = parse_musicxml(transformed_musicxml.encode("utf-8"))
    if parse_result.failure is not None or parse_result.canonical_score is None:
        return None

    canonical_score = parse_result.canonical_score
    return CanonicalScoreSummary(
        schemaVersion=canonical_score.schema_version,
        title=canonical_score.title,
        partCount=len(canonical_score.parts or []),
        measureCount=canonical_score.measure_count,
        noteCount=canonical_score.note_count,
        restCount=canonical_score.rest_count,
        parts=[
            CanonicalScorePartSummary(
                partId=part.get("id", ""),
                name=part.get("name", ""),
            )
            for part in (canonical_score.parts or [])
        ],
    )


def _build_revision_token(score_document: ScoreDocument) -> str:
    created_at = score_document.created_at or datetime.now(timezone.utc)
    return created_at.isoformat()


def get_source_score_preview_content(
    db: Session,
    score_document_id: str,
    revision: str,
) -> Response:
    score_document = db.query(ScoreDocument).filter(ScoreDocument.id == score_document_id).first()
    if score_document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Score with id {score_document_id} not found.",
        )

    expected_revision = _build_revision_token(score_document)
    if revision != expected_revision:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="The requested score preview revision is stale.",
        )

    if score_document.processing_status != ScoreProcessingStatus.PARSED or not score_document.source_musicxml:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="The requested score preview content is not ready.",
        )

    return Response(
        content=ensure_xml_declaration(score_document.source_musicxml),
        media_type="application/vnd.recordare.musicxml+xml",
    )


def _extract_musicxml_payload(content: bytes, suffix: str) -> bytes:
    if suffix in {".musicxml", ".xml"}:
        decoded = content.decode("utf-8", errors="ignore")
        if not any(marker in decoded for marker in MUSICXML_MARKERS):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="The uploaded file is not valid MusicXML.",
            )
        return content

    if suffix == ".mxl":
        return _extract_mxl_rootfile(content)

    raise HTTPException(
        status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
        detail="Only MusicXML-family uploads (.musicxml, .xml, .mxl) are supported.",
    )


def _extract_mxl_rootfile(content: bytes) -> bytes:
    try:
        with ZipFile(BytesIO(content)) as archive:
            candidate_names = [
                name for name in archive.namelist()
                if not name.endswith("/") and not name.startswith("META-INF/")
            ]
            preferred_name = next(
                (name for name in candidate_names if Path(name).suffix.lower() in {".musicxml", ".xml"}),
                None,
            )
            selected_name = preferred_name or (candidate_names[0] if candidate_names else None)
            if selected_name is None:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="The uploaded file is not valid MusicXML.",
                )

            selected_info = archive.getinfo(selected_name)
            if selected_info.file_size > MAX_UPLOAD_SIZE_BYTES:
                raise HTTPException(
                    status_code=status.HTTP_413_CONTENT_TOO_LARGE,
                    detail="The uploaded file exceeds the maximum allowed size after extraction.",
                )

            xml_payload = archive.read(selected_name)
    except BadZipFile:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="The uploaded file is not valid MusicXML.",
        ) from None

    decoded = xml_payload.decode("utf-8", errors="ignore")
    if not any(marker in decoded for marker in MUSICXML_MARKERS):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="The uploaded file is not valid MusicXML.",
        )

    return xml_payload


def _derive_read_processing_status(
    score_document: ScoreDocument,
    recommendations_exist: bool,
) -> ScoreProcessingStatus:
    if score_document.processing_status == ScoreProcessingStatus.PARSE_FAILED:
        return ScoreProcessingStatus.FAILED

    if score_document.processing_status == ScoreProcessingStatus.PARSED:
        if recommendations_exist:
            return ScoreProcessingStatus.RECOMMENDATION_READY
        return ScoreProcessingStatus.RECOMMENDATION_PENDING

    if score_document.processing_status == ScoreProcessingStatus.UPLOADED:
        return ScoreProcessingStatus.UPLOADED

    return score_document.processing_status


def _build_score_safe_summary(processing_status: ScoreProcessingStatus) -> str:
    if processing_status == ScoreProcessingStatus.RECOMMENDATION_READY:
        return "The score is parsed and recommendations are ready for review."

    if processing_status == ScoreProcessingStatus.RECOMMENDATION_PENDING:
        return "The score is parsed and ready for recommendation generation."

    if processing_status == ScoreProcessingStatus.FAILED:
        return "The score flow failed before a recommendation-ready state was reached."

    if processing_status == ScoreProcessingStatus.UPLOADED:
        return "The uploaded score has been accepted and is waiting for further processing."

    return "The current score status is available."
