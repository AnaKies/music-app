from typing import List, Optional

from sqlalchemy.orm import Session

from backend.api.schemas.cases import CaseConstraints, CaseDetail, CaseStatus, CaseSummary, CaseUpdateRequest
from backend.domain.cases.models import TranspositionCase
from backend.domain.interviews.models import InterviewSession
from backend.domain.recommendations.models import RangeRecommendation
from backend.domain.scores.models import ScoreDocument
from backend.domain.transformations.models import TransformationJob
from backend.services.interviews.service import _has_confirmed_constraints_for_upload


class CaseService:
    @staticmethod
    def get_case_by_id(db: Session, case_id: str) -> Optional[TranspositionCase]:
        return db.query(TranspositionCase).filter(TranspositionCase.id == case_id).first()

    @staticmethod
    def get_all_cases(db: Session) -> List[TranspositionCase]:
        return db.query(TranspositionCase).all()

    @staticmethod
    def delete_case(db: Session, case_id: str) -> bool:
        case = CaseService.get_case_by_id(db, case_id)
        if case is None:
            return False

        db.delete(case)
        db.commit()
        return True

    @staticmethod
    def update_case(db: Session, case_id: str, payload: CaseUpdateRequest) -> Optional[TranspositionCase]:
        case = CaseService.get_case_by_id(db, case_id)
        if case is None:
            return None

        has_relevant_changes = _has_relevant_case_changes(case, payload)

        case.instrument_identity = payload.instrumentIdentity
        case.highest_playable_tone = payload.constraints.highest_playable_tone
        case.lowest_playable_tone = payload.constraints.lowest_playable_tone
        case.restricted_tones = payload.constraints.restricted_tones
        case.restricted_registers = payload.constraints.restricted_registers
        case.difficult_keys = payload.constraints.difficult_keys
        case.preferred_keys = payload.constraints.preferred_keys
        case.comfort_range_min = payload.constraints.comfort_range_min
        case.comfort_range_max = payload.constraints.comfort_range_max
        case.status = (
            CaseStatus.READY_FOR_UPLOAD
            if _has_confirmed_constraints_for_upload(case)
            else CaseStatus.INTERVIEW_IN_PROGRESS
        )

        if has_relevant_changes:
            _clear_downstream_runtime_state(db, case.id, mark_recommendations_stale=True)

        db.add(case)
        db.commit()
        db.refresh(case)
        return case

    @staticmethod
    def reset_case(db: Session, case_id: str) -> Optional[TranspositionCase]:
        case = CaseService.get_case_by_id(db, case_id)
        if case is None:
            return None

        _clear_downstream_runtime_state(db, case.id, remove_scores=True, remove_interviews=True)

        case.status = CaseStatus.NEW
        case.highest_playable_tone = None
        case.lowest_playable_tone = None
        case.restricted_tones = []
        case.restricted_registers = []
        case.difficult_keys = []
        case.preferred_keys = []
        case.comfort_range_min = None
        case.comfort_range_max = None

        db.add(case)
        db.commit()
        db.refresh(case)
        return case

    @staticmethod
    def build_case_summary(case: TranspositionCase) -> CaseSummary:
        return CaseSummary(
            id=case.id,
            status=case.status,
            instrumentIdentity=case.instrument_identity,
            scoreCount=case.score_count,
            createdAt=case.created_at,
            updatedAt=case.updated_at,
        )

    @staticmethod
    def build_case_detail(case: TranspositionCase) -> CaseDetail:
        latest_score = None
        if case.scores:
            latest_score = max(case.scores, key=lambda score: score.created_at)

        return CaseDetail(
            id=case.id,
            status=case.status,
            instrumentIdentity=case.instrument_identity,
            scoreCount=case.score_count,
            latestScoreDocumentId=latest_score.id if latest_score is not None else None,
            createdAt=case.created_at,
            updatedAt=case.updated_at,
            constraints=CaseConstraints(
                highest_playable_tone=case.highest_playable_tone,
                lowest_playable_tone=case.lowest_playable_tone,
                restricted_tones=case.restricted_tones or [],
                restricted_registers=case.restricted_registers or [],
                difficult_keys=case.difficult_keys or [],
                preferred_keys=case.preferred_keys or [],
                comfort_range_min=case.comfort_range_min,
                comfort_range_max=case.comfort_range_max,
            ),
        )


def _has_relevant_case_changes(case: TranspositionCase, payload: CaseUpdateRequest) -> bool:
    return any(
        [
            case.instrument_identity != payload.instrumentIdentity,
            case.highest_playable_tone != payload.constraints.highest_playable_tone,
            case.lowest_playable_tone != payload.constraints.lowest_playable_tone,
            (case.restricted_tones or []) != payload.constraints.restricted_tones,
            (case.restricted_registers or []) != payload.constraints.restricted_registers,
            (case.difficult_keys or []) != payload.constraints.difficult_keys,
            (case.preferred_keys or []) != payload.constraints.preferred_keys,
            case.comfort_range_min != payload.constraints.comfort_range_min,
            case.comfort_range_max != payload.constraints.comfort_range_max,
        ]
    )


def _clear_downstream_runtime_state(
    db: Session,
    case_id: str,
    *,
    remove_scores: bool = False,
    remove_interviews: bool = False,
    mark_recommendations_stale: bool = False,
) -> None:
    db.query(TransformationJob).filter(TransformationJob.transposition_case_id == case_id).delete(
        synchronize_session=False
    )
    if mark_recommendations_stale:
        db.query(RangeRecommendation).filter(RangeRecommendation.transposition_case_id == case_id).update(
            {RangeRecommendation.is_stale: True},
            synchronize_session=False,
        )
    else:
        db.query(RangeRecommendation).filter(RangeRecommendation.transposition_case_id == case_id).delete(
            synchronize_session=False
        )
    if remove_scores:
        score_documents = db.query(ScoreDocument).filter(ScoreDocument.transposition_case_id == case_id).all()
        for score_document in score_documents:
            db.delete(score_document)
    if remove_interviews:
        db.query(InterviewSession).filter(InterviewSession.case_id == case_id).delete(synchronize_session=False)
