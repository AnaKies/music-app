from fastapi import HTTPException, status
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
            detail="The selected recommendation is unknown or stale.",
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
    db.commit()
    db.refresh(transformation_job)

    return TransformationResponse(
        transformationJobId=transformation_job.id,
        status=transformation_job.status,
        transpositionCaseId=transposition_case_id,
        scoreDocumentId=score_document_id,
        recommendationId=recommendation_id,
        selectedRangeMin=transformation_job.selected_range_min,
        selectedRangeMax=transformation_job.selected_range_max,
        semitoneShift=transformation_job.semitone_shift,
        safeSummary=transformation_job.safe_summary,
        warnings=[TransformationWarning(**warning) for warning in (transformation_job.warnings or [])],
        createdAt=transformation_job.created_at,
    )
