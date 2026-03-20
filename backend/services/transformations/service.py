from fastapi import HTTPException, Response, status
from sqlalchemy.orm import Session

from backend.api.schemas.scores import ScoreProcessingStatus
from backend.api.schemas.transformations import (
    TransformationResponse,
    TransformationStatus,
    TransformationWarning,
)
from backend.domain.recommendations.models import RangeRecommendation
from backend.domain.scores.models import ScoreDocument
from backend.domain.transformations.models import TransformationJob
from backend.services.exports.service import export_transformation_result
from backend.services.shared.musicxml import ensure_xml_declaration
from backend.services.transformations.engine import transform_musicxml_to_target_range


def create_transformation(
    db: Session,
    transposition_case_id: str,
    score_document_id: str,
    recommendation_id: str,
) -> TransformationResponse:
    score_document = db.query(ScoreDocument).filter(ScoreDocument.id == score_document_id).first()
    if score_document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Score with id {score_document_id} not found.",
        )

    if score_document.transposition_case_id != transposition_case_id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="The selected score does not belong to the selected case.",
        )

    if score_document.processing_status != ScoreProcessingStatus.PARSED or not score_document.source_musicxml:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="The selected score is not ready for deterministic transformation.",
        )

    recommendation = (
        db.query(RangeRecommendation)
        .filter(
            RangeRecommendation.id == recommendation_id,
            RangeRecommendation.transposition_case_id == transposition_case_id,
            RangeRecommendation.score_document_id == score_document_id,
        )
        .first()
    )
    if recommendation is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="The selected recommendation is unknown.",
        )

    if recommendation.is_stale:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="The selected recommendation is stale. Regenerate recommendations before transforming.",
        )

    try:
        engine_result = transform_musicxml_to_target_range(
            musicxml=score_document.source_musicxml,
            target_range_min=recommendation.target_range_min,
            target_range_max=recommendation.target_range_max,
        )
    except ValueError as error:
        error_code = str(error)
        if error_code == "invalid_target_range":
            detail = "The selected recommendation range is not in a supported note format."
        elif error_code == "incomplete_source_score":
            detail = "The selected score does not contain enough pitched note data for deterministic transformation."
        else:
            detail = "The transformation request could not be executed from the validated deterministic inputs."
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=detail,
        ) from error

    safe_summary = (
        "The deterministic transformation completed successfully."
        if not engine_result.warnings
        else "The deterministic transformation completed with warnings."
    )
    transformation_job = TransformationJob(
        transposition_case_id=transposition_case_id,
        score_document_id=score_document_id,
        recommendation_id=recommendation_id,
        status=TransformationStatus.COMPLETED,
        selected_range_min=recommendation.target_range_min,
        selected_range_max=recommendation.target_range_max,
        semitone_shift=engine_result.semitone_shift,
        safe_summary=safe_summary,
        warnings=[warning.model_dump() for warning in engine_result.warnings],
        transformed_musicxml=engine_result.transformed_musicxml,
    )
    db.add(transformation_job)
    db.flush()

    try:
        exported_artifact = export_transformation_result(
            transformation_job_id=transformation_job.id,
            transformed_musicxml=engine_result.transformed_musicxml,
            original_filename=score_document.original_filename,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="The transformed score could not be exported as a valid MusicXML result.",
        ) from error

    transformation_job.result_storage_uri = exported_artifact.storage_uri
    transformation_job.result_filename = exported_artifact.filename
    transformation_job.result_revision_token = exported_artifact.revision_token
    transformation_job.exported_at = exported_artifact.exported_at

    db.commit()
    db.refresh(transformation_job)

    return TransformationResponse(
        **_build_transformation_payload(transformation_job),
    )


def get_transformation_preview_content(
    db: Session,
    transformation_job_id: str,
    revision: str,
) -> Response:
    transformation_job = db.query(TransformationJob).filter(TransformationJob.id == transformation_job_id).first()
    if transformation_job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transformation with id {transformation_job_id} not found.",
        )

    if not transformation_job.result_revision_token or revision != transformation_job.result_revision_token:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="The requested result preview revision is stale.",
        )

    if not transformation_job.transformed_musicxml or not transformation_job.result_storage_uri:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="The requested result preview content is not ready.",
        )

    return Response(
        content=ensure_xml_declaration(transformation_job.transformed_musicxml),
        media_type="application/vnd.recordare.musicxml+xml",
    )


def get_transformation_read(
    db: Session,
    transformation_job_id: str,
) -> TransformationResponse:
    transformation_job = db.query(TransformationJob).filter(TransformationJob.id == transformation_job_id).first()
    if transformation_job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transformation with id {transformation_job_id} not found.",
        )

    return TransformationResponse(**_build_transformation_payload(transformation_job))


def _build_transformation_payload(transformation_job: TransformationJob) -> dict:
    return {
        "transformationJobId": transformation_job.id,
        "status": transformation_job.status,
        "transpositionCaseId": transformation_job.transposition_case_id,
        "scoreDocumentId": transformation_job.score_document_id,
        "recommendationId": transformation_job.recommendation_id,
        "selectedRangeMin": transformation_job.selected_range_min,
        "selectedRangeMax": transformation_job.selected_range_max,
        "semitoneShift": transformation_job.semitone_shift,
        "safeSummary": transformation_job.safe_summary,
        "resultFilename": transformation_job.result_filename,
        "resultPreviewRevisionToken": transformation_job.result_revision_token,
        "isRetryable": False,
        "failureCode": None,
        "failureSeverity": None,
        "warnings": [TransformationWarning(**warning) for warning in (transformation_job.warnings or [])],
        "createdAt": transformation_job.created_at,
    }
