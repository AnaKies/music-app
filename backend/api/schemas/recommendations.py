from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class ConfirmedCaseConstraints(BaseModel):
    instrumentIdentity: str
    highestPlayableTone: Optional[str] = None
    lowestPlayableTone: Optional[str] = None
    restrictedTones: List[str] = Field(default_factory=list)
    restrictedRegisters: List[str] = Field(default_factory=list)
    difficultKeys: List[str] = Field(default_factory=list)
    preferredKeys: List[str] = Field(default_factory=list)
    comfortRangeMin: Optional[str] = None
    comfortRangeMax: Optional[str] = None


class InferredConstraintAdvisory(BaseModel):
    source: str
    confidence: str
    advisoryNotes: List[str] = Field(default_factory=list)


class InstrumentKnowledge(BaseModel):
    instrumentIdentity: str
    displayName: str
    transposition: str
    writtenRangeMin: str
    writtenRangeMax: str
    preferredClefs: List[str] = Field(default_factory=list)
    keySuitabilityNotes: List[str] = Field(default_factory=list)


class RecommendationScoreSummary(BaseModel):
    schemaVersion: str
    title: Optional[str] = None
    partCount: int
    measureCount: int
    noteCount: int
    restCount: int
    partNames: List[str] = Field(default_factory=list)


class RecommendationContext(BaseModel):
    contextVersion: str
    transpositionCaseId: str
    scoreDocumentId: str
    confirmedConstraints: ConfirmedCaseConstraints
    inferredConstraints: Optional[InferredConstraintAdvisory] = None
    instrumentKnowledge: InstrumentKnowledge
    scoreSummary: RecommendationScoreSummary


class RecommendationContextRequest(BaseModel):
    transpositionCaseId: str
    scoreDocumentId: str


class RecommendationConfidence(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    BLOCKED = "blocked"


class RecommendationWarningSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    BLOCKER = "blocker"


class RecommendationStatus(str, Enum):
    READY = "ready"
    BLOCKED = "blocked"


class RecommendationWarning(BaseModel):
    code: str
    severity: RecommendationWarningSeverity
    message: str


class RecommendationTargetRange(BaseModel):
    min: str
    max: str


class RecommendationItem(BaseModel):
    recommendationId: str
    label: str
    targetRange: RecommendationTargetRange
    recommendedKey: Optional[str] = None
    confidence: RecommendationConfidence
    summaryReason: str
    warnings: List[RecommendationWarning] = Field(default_factory=list)
    isPrimary: bool
    isStale: bool = False


class RecommendationFailure(BaseModel):
    confidence: RecommendationConfidence
    code: str
    safeSummary: str


class RecommendationResponse(BaseModel):
    status: RecommendationStatus
    transpositionCaseId: str
    scoreDocumentId: str
    recommendations: List[RecommendationItem] = Field(default_factory=list)
    failure: Optional[RecommendationFailure] = None
