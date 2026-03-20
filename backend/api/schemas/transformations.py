from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class TransformationStatus(str, Enum):
    COMPLETED = "completed"
    FAILED = "failed"


class TransformationWarningSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    BLOCKER = "blocker"


class TransformationWarning(BaseModel):
    code: str
    severity: TransformationWarningSeverity
    message: str


class TransformationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    transpositionCaseId: str
    scoreDocumentId: str
    recommendationId: str


class TransformationResponse(BaseModel):
    transformationJobId: str
    status: TransformationStatus
    transpositionCaseId: str
    scoreDocumentId: str
    recommendationId: str
    selectedRangeMin: str
    selectedRangeMax: str
    semitoneShift: Optional[int] = None
    safeSummary: str
    resultFilename: Optional[str] = None
    resultPreviewRevisionToken: Optional[str] = None
    isRetryable: bool = False
    failureCode: Optional[str] = None
    failureSeverity: Optional[str] = None
    warnings: List[TransformationWarning]
    createdAt: datetime
