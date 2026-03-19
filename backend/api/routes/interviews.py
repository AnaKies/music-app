from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from backend.api.schemas.interviews import (
    InterviewAdvanceRequest,
    InterviewAdvanceResponse,
    InterviewDetailResponse,
)
from backend.database import get_db
from backend.services.interviews.service import InterviewService

router = APIRouter(tags=["interviews"])


@router.post(
    "/interviews",
    response_model=InterviewAdvanceResponse,
    status_code=status.HTTP_200_OK,
)
def post_interview(
    payload: InterviewAdvanceRequest,
    db: Session = Depends(get_db),
) -> InterviewAdvanceResponse:
    return InterviewService.start_or_continue(db=db, payload=payload)


@router.get(
    "/interviews/{interview_id}",
    response_model=InterviewDetailResponse,
    status_code=status.HTTP_200_OK,
)
def get_interview(
    interview_id: str,
    db: Session = Depends(get_db),
) -> InterviewDetailResponse:
    return InterviewService.get_detail(db=db, interview_id=interview_id)
