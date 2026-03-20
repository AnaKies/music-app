from typing import List, Optional

from sqlalchemy.orm import Session

from backend.api.schemas.cases import CaseConstraints, CaseDetail, CaseSummary
from backend.domain.cases.models import TranspositionCase


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
