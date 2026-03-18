from typing import List, Optional

from sqlalchemy.orm import Session

from backend.api.schemas.cases import CaseConstraints, CaseDetail, CaseSummary
from backend.domain.cases.models import TranspositionCase


class CaseService:
    """
    Service layer for transposition case operations.
    
    Provides database queries and schema transformation methods
    for case-related business logic.
    """
    
    @staticmethod
    def get_case_by_id(db: Session, case_id: str) -> Optional[TranspositionCase]:
        """Retrieve a single case by its unique identifier."""
        return db.query(TranspositionCase).filter(TranspositionCase.id == case_id).first()

    @staticmethod
    def get_all_cases(db: Session) -> List[TranspositionCase]:
        """Retrieve all cases from the database."""
        return db.query(TranspositionCase).all()

    @staticmethod
    def build_case_summary(case: TranspositionCase) -> CaseSummary:
        """
        Build a CaseSummary schema from a domain model.
        
        Used for list endpoints where full constraint details are not needed.
        """
        return CaseSummary(
            id=case.id,
            status=case.status,
            instrumentIdentity=case.instrument_identity,
            userId=case.user_id,
            scoreCount=case.score_count,
            createdAt=case.created_at,
            updatedAt=case.updated_at,
        )

    @staticmethod
    def build_case_detail(case: TranspositionCase) -> CaseDetail:
        """
        Build a CaseDetail schema from a domain model.
        
        Used for detail endpoints where constraint information is required.
        Includes all confirmed user-specific playable constraints.
        """
        return CaseDetail(
            id=case.id,
            status=case.status,
            instrumentIdentity=case.instrument_identity,
            userId=case.user_id,
            scoreCount=case.score_count,
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
