from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.api.schemas.cases import (
    CaseCreateRequest, 
    CaseCreateResponse, 
    CaseSummary, 
    CaseDetail
)
from backend.database import get_db
from backend.services.cases.create_case import create_case
from backend.services.cases.service import CaseService

router = APIRouter(tags=["cases"])


@router.post(
    "/cases",
    response_model=CaseCreateResponse,
    status_code=status.HTTP_201_CREATED,
)
def post_case(
    payload: CaseCreateRequest,
    db: Session = Depends(get_db),
) -> CaseCreateResponse:
    """
    Create a new transposition case or perform an action on an existing one.
    """
    # Validate action/ID combination
    if payload.existingCaseAction is not None and payload.existingCaseId is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="existingCaseId is required when existingCaseAction is provided.",
        )

    return create_case(db=db, payload=payload)


@router.get(
    "/cases/{case_id}", 
    response_model=CaseDetail
)
def get_case(
    case_id: str, 
    db: Session = Depends(get_db)
) -> CaseDetail:
    """
    Get detailed information about a transposition case.
    """
    case = CaseService.get_case_by_id(db, case_id)
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Case with id {case_id} not found"
        )
    
    return {
        "id": case.id,
        "userId": case.user_id,
        "status": case.status,
        "instrumentIdentity": case.instrument_identity,
        "scoreCount": case.score_count,
        "createdAt": case.created_at,
        "updatedAt": case.updated_at,
        "constraints": {
            "highestPlayableTone": case.highest_playable_tone,
            "lowestPlayableTone": case.lowest_playable_tone,
            "restrictedTones": case.restricted_tones,
            "restrictedRegisters": case.restricted_registers,
            "difficultKeys": case.difficult_keys,
            "preferredKeys": case.preferred_keys,
            "comfortRangeMin": case.comfort_range_min,
            "comfortRangeMax": case.comfort_range_max
        }
    }


@router.get(
    "/cases", 
    response_model=List[CaseSummary]
)
def list_cases(
    db: Session = Depends(get_db)
) -> List[CaseSummary]:
    """
    List all transposition cases.
    """
    cases = CaseService.get_all_cases(db)
    return [
        {
            "id": c.id,
            "userId": c.user_id,
            "status": c.status,
            "instrumentIdentity": c.instrument_identity,
            "scoreCount": c.score_count,
            "createdAt": c.created_at,
            "updatedAt": c.updated_at
        } for c in cases
    ]
