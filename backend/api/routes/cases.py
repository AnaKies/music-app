from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.api.schemas.cases import (
    CaseCreateRequest,
    CaseCreateResponse,
    CaseSummary,
    CaseDetail,
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
    if payload.existing_case_action is not None and payload.existing_case_id is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="existing_case_id is required when existing_case_action is provided.",
        )

    return create_case(db=db, payload=payload)


@router.get(
    "/cases/{case_id}",
    response_model=CaseDetail,
    status_code=status.HTTP_200_OK,
)
def get_case(
    case_id: str,
    db: Session = Depends(get_db),
) -> CaseDetail:
    """
    Get detailed information about a transposition case.
    """
    case = CaseService.get_case_by_id(db, case_id)
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Case with id {case_id} not found.",
        )

    return CaseService.build_case_detail(case)


@router.get(
    "/cases",
    response_model=list[CaseSummary],
)
def list_cases(db: Session = Depends(get_db)) -> list[CaseSummary]:
    """
    List all transposition cases.
    """
    cases = CaseService.get_all_cases(db)
    return [CaseService.build_case_summary(case) for case in cases]


@router.delete(
    "/cases/{case_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_case(
    case_id: str,
    db: Session = Depends(get_db),
) -> None:
    """
    Provisional MVP cleanup route for removing a case.
    """
    deleted = CaseService.delete_case(db, case_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Case with id {case_id} not found.",
        )
