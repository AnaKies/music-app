from datetime import datetime, timezone
from enum import Enum
from typing import Optional, List

from pydantic import BaseModel, Field


class CaseStatus(str, Enum):
    NEW = "new"
    INTERVIEW_IN_PROGRESS = "interview_in_progress"
    READY_FOR_UPLOAD = "ready_for_upload"
    RECOMMENDATION_READY = "recommendation_ready"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class ExistingCaseAction(str, Enum):
    RESET = "reset"


class CaseCreateRequest(BaseModel):
    instrumentIdentity: str = Field(
        min_length=1,
        description="Stable frontend or product identity for the target instrument context.",
    )
    userId: Optional[str] = Field(
        default=None,
        description="Unique user identifier.",
    )
    existingCaseAction: Optional[ExistingCaseAction] = Field(
        default=None,
        description="Optional explicit action on an existing case.",
    )
    existingCaseId: Optional[str] = Field(
        default=None,
        description="Existing case identifier required when a case action is requested.",
    )


class CaseConstraints(BaseModel):
    """
    Active constraints for a transposition case in camelCase.
    """
    highestPlayableTone: Optional[str] = Field(default=None)
    lowestPlayableTone: Optional[str] = Field(default=None)
    restrictedTones: List[str] = Field(default_factory=list)
    restrictedRegisters: List[str] = Field(default_factory=list)
    difficultKeys: List[str] = Field(default_factory=list)
    preferredKeys: List[str] = Field(default_factory=list)
    comfortRangeMin: Optional[str] = Field(default=None)
    comfortRangeMax: Optional[str] = Field(default=None)


class CaseSummary(BaseModel):
    id: str = Field(description="Unique case identifier.")
    userId: Optional[str] = Field(default=None)
    status: CaseStatus = Field(description="Current case lifecycle state.")
    instrumentIdentity: str = Field(description="Stable frontend identity.")
    scoreCount: int = Field(default=0)
    createdAt: datetime = Field(description="Creation timestamp.")
    updatedAt: datetime = Field(description="Last update timestamp.")


class CaseCreateResponse(BaseModel):
    transpositionCaseId: str
    status: CaseStatus
    caseSummary: CaseSummary


class CaseDetail(BaseModel):
    id: str
    userId: Optional[str] = None
    status: CaseStatus
    instrumentIdentity: str
    scoreCount: int = 0
    createdAt: datetime
    updatedAt: datetime
    constraints: CaseConstraints = Field(default_factory=CaseConstraints)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)
