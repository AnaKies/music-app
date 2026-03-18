from datetime import datetime, timezone
from sqlalchemy.orm import Session
from backend.api.schemas.cases import (
    CaseCreateRequest,
    CaseCreateResponse,
    CaseStatus,
    CaseSummary,
)
from backend.domain.cases.models import TranspositionCase


def create_case(db: Session, payload: CaseCreateRequest) -> CaseCreateResponse:
    """
    Create a new transposition case and persist it to the database.
    """
    now = datetime.now(timezone.utc)
    
    # Create domain model instance
    new_case = TranspositionCase(
        user_id=payload.userId,
        status=CaseStatus.NEW,
        instrument_identity=payload.instrumentIdentity,
        created_at=now,
        updated_at=now,
    )

    # Persist to database
    db.add(new_case)
    db.commit()
    db.refresh(new_case)

    # Build response using the schema contract (mapping to camelCase)
    return CaseCreateResponse(
        transpositionCaseId=new_case.id,
        status=new_case.status,
        caseSummary=CaseSummary(
            id=new_case.id,
            userId=new_case.user_id,
            status=new_case.status,
            instrumentIdentity=new_case.instrument_identity,
            scoreCount=0,
            createdAt=new_case.created_at,
            updatedAt=new_case.updated_at,
        ),
    )
