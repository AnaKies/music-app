from datetime import datetime, timezone
from enum import Enum
from typing import Optional

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
    instrument_identity: str = Field(
        min_length=1,
        description="Stable frontend or product identity for the target instrument context.",
    )
    existing_case_action: Optional[ExistingCaseAction] = Field(
        default=None,
        description="Optional explicit action on an existing case.",
    )
    existing_case_id: Optional[str] = Field(
        default=None,
        description="Existing case identifier required when a case action is requested.",
    )


class CaseConstraints(BaseModel):
    highest_playable_tone: Optional[str] = Field(default=None)
    lowest_playable_tone: Optional[str] = Field(default=None)
    restricted_tones: list[str] = Field(default_factory=list)
    restricted_registers: list[str] = Field(default_factory=list)
    difficult_keys: list[str] = Field(default_factory=list)
    preferred_keys: list[str] = Field(default_factory=list)
    comfort_range_min: Optional[str] = Field(default=None)
    comfort_range_max: Optional[str] = Field(default=None)


class CaseSummary(BaseModel):
    id: str = Field(description="Unique case identifier.")
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
    status: CaseStatus
    instrumentIdentity: str
    scoreCount: int = 0
    latestScoreDocumentId: Optional[str] = None
    createdAt: datetime
    updatedAt: datetime
    constraints: CaseConstraints = Field(default_factory=CaseConstraints)


class CaseUpdateRequest(BaseModel):
    instrumentIdentity: str = Field(min_length=1)
    constraints: CaseConstraints = Field(default_factory=CaseConstraints)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)
