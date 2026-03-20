import uuid
from typing import List, Optional

from sqlalchemy.orm import Session

from backend.api.schemas.recommendations import (
    RecommendationConfidence,
    RecommendationFailure,
    RecommendationItem,
    RecommendationResponse,
    RecommendationStatus,
    RecommendationTargetRange,
    RecommendationWarning,
    RecommendationWarningSeverity,
)
from backend.domain.recommendations.models import RangeRecommendation
from backend.services.recommendations.context import build_recommendation_context
from backend.services.shared.note_ranges import normalize_note_bounds


def generate_recommendations(
    db: Session,
    transposition_case_id: str,
    score_document_id: str,
) -> RecommendationResponse:
    context = build_recommendation_context(
        db=db,
        transposition_case_id=transposition_case_id,
        score_document_id=score_document_id,
    )

    if (
        not context.confirmedConstraints.comfortRangeMin
        or not context.confirmedConstraints.comfortRangeMax
        or context.scoreSummary.noteCount <= 0
    ):
        return RecommendationResponse(
            status=RecommendationStatus.BLOCKED,
            transpositionCaseId=transposition_case_id,
            scoreDocumentId=score_document_id,
            recommendations=[],
            failure=RecommendationFailure(
                confidence=RecommendationConfidence.BLOCKED,
                code="insufficient_context",
                safeSummary="The recommendation path is blocked because the case or score context is incomplete.",
            ),
        )

    primary_confidence = _confidence_for_context(context)
    primary_warnings = _warnings_for_context(context, primary_confidence)

    primary_item = RecommendationItem(
        recommendationId=str(uuid.uuid4()),
        label="Primary recommendation",
        targetRange=RecommendationTargetRange(
            min=_normalized_target_range(
                context.confirmedConstraints.comfortRangeMin,
                context.confirmedConstraints.comfortRangeMax,
            )[0],
            max=_normalized_target_range(
                context.confirmedConstraints.comfortRangeMin,
                context.confirmedConstraints.comfortRangeMax,
            )[1],
        ),
        recommendedKey=_recommended_key(context),
        confidence=primary_confidence,
        summaryReason="Matches the confirmed player comfort range while respecting the current case constraints.",
        warnings=primary_warnings,
        isPrimary=True,
    )

    secondary_item = RecommendationItem(
        recommendationId=str(uuid.uuid4()),
        label="Instrument baseline alternative",
        targetRange=RecommendationTargetRange(
            min=context.instrumentKnowledge.writtenRangeMin,
            max=context.instrumentKnowledge.writtenRangeMax,
        ),
        recommendedKey=None,
        confidence=RecommendationConfidence.MEDIUM
        if primary_confidence != RecommendationConfidence.LOW
        else RecommendationConfidence.LOW,
        summaryReason="Offers the generic instrument baseline as a fallback comparison against the player-specific range.",
        warnings=[
            RecommendationWarning(
                code="generic_baseline",
                severity=RecommendationWarningSeverity.INFO,
                message="This option leans on generic instrument knowledge rather than only the confirmed player comfort range.",
            )
        ],
        isPrimary=False,
    )

    recommendations = [primary_item, secondary_item]
    _persist_recommendations(db, transposition_case_id, score_document_id, recommendations)

    return RecommendationResponse(
        status=RecommendationStatus.READY,
        transpositionCaseId=transposition_case_id,
        scoreDocumentId=score_document_id,
        recommendations=recommendations,
        failure=None,
    )


def _confidence_for_context(context) -> RecommendationConfidence:
    if context.inferredConstraints is not None:
        return RecommendationConfidence.LOW

    if context.confirmedConstraints.restrictedRegisters or context.confirmedConstraints.difficultKeys:
        return RecommendationConfidence.MEDIUM

    return RecommendationConfidence.HIGH


def _warnings_for_context(context, confidence: RecommendationConfidence) -> List[RecommendationWarning]:
    warnings: List[RecommendationWarning] = []
    if context.inferredConstraints is not None:
        warnings.append(
            RecommendationWarning(
                code="advisory_inference_present",
                severity=RecommendationWarningSeverity.WARNING,
                message="Some interview input remains advisory and should be reviewed before trusting the recommendation fully.",
            )
        )
    if context.confirmedConstraints.restrictedRegisters:
        warnings.append(
            RecommendationWarning(
                code="register_risk",
                severity=RecommendationWarningSeverity.WARNING,
                message="The confirmed case includes register-risk flags that may limit aggressive range choices.",
            )
        )
    if confidence == RecommendationConfidence.HIGH:
        warnings.append(
            RecommendationWarning(
                code="grounded_context",
                severity=RecommendationWarningSeverity.INFO,
                message="The recommendation is grounded in confirmed constraints and parsed score structure.",
            )
        )
    return warnings


def _recommended_key(context) -> Optional[str]:
    if context.confirmedConstraints.difficultKeys:
        return None
    return "concert_c"


def _persist_recommendations(
    db: Session,
    transposition_case_id: str,
    score_document_id: str,
    recommendations: List[RecommendationItem],
) -> None:
    db.query(RangeRecommendation).filter(
        RangeRecommendation.transposition_case_id == transposition_case_id,
        RangeRecommendation.score_document_id == score_document_id,
    ).delete()

    for item in recommendations:
        db.add(
            RangeRecommendation(
                id=item.recommendationId,
                transposition_case_id=transposition_case_id,
                score_document_id=score_document_id,
                label=item.label,
                target_range_min=item.targetRange.min,
                target_range_max=item.targetRange.max,
                recommended_key=item.recommendedKey,
                confidence=item.confidence,
                summary_reason=item.summaryReason,
                warnings=[warning.model_dump() for warning in item.warnings],
                is_primary=item.isPrimary,
            )
        )

    db.commit()


def _normalized_target_range(range_min: str, range_max: str) -> tuple[str, str]:
    try:
        return normalize_note_bounds(range_min, range_max)
    except ValueError:
        return range_min, range_max
