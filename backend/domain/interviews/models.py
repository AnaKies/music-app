import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Enum, JSON, String

from backend.api.schemas.interviews import InterviewSessionStatus
from backend.database import Base


class InterviewSession(Base):
    __tablename__ = "interview_sessions"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    case_id = Column(String, nullable=False, index=True)
    status = Column(Enum(InterviewSessionStatus), nullable=False, default=InterviewSessionStatus.IN_PROGRESS)
    current_question_id = Column(String, nullable=True)
    answers = Column(JSON, nullable=False, default=list)
    low_confidence = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
