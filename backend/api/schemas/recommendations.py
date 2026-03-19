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
