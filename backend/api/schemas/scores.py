from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class ScoreFormat(str, Enum):
    MUSICXML = "musicxml"


class ScoreProcessingStatus(str, Enum):
    UPLOADED = "uploaded"
    QUEUED = "queued"
    PARSING = "parsing"
    PARSED = "parsed"
    RECOMMENDATION_PENDING = "recommendation_pending"
    RECOMMENDATION_READY = "recommendation_ready"
    TRANSFORMING = "transforming"
    COMPLETED = "completed"
    FAILED = "failed"
    PARSE_FAILED = "parse_failed"


class ParseFailureType(str, Enum):
    INVALID_XML = "invalid_xml"
    UNSUPPORTED_STRUCTURE = "unsupported_structure"
    EMPTY_SCORE = "empty_score"


class ScorePreviewAvailability(str, Enum):
    READY = "ready"
    NOT_READY = "not_ready"
    UNAVAILABLE = "unavailable"
    FAILED = "failed"


class ScoreArtifactRole(str, Enum):
    SOURCE = "source"
    RESULT = "result"


class CanonicalScorePartSummary(BaseModel):
    partId: str
    name: str


class CanonicalScoreSummary(BaseModel):
    schemaVersion: str
    title: Optional[str] = None
    partCount: int
    measureCount: int
    noteCount: int
    restCount: int
    parts: List[CanonicalScorePartSummary]


class ScoreProcessingSnapshot(BaseModel):
    scoreDocumentId: str
    transpositionCaseId: str
    processingStatus: ScoreProcessingStatus
    acceptedAt: datetime
    parseFailureType: Optional[ParseFailureType] = None
    canonicalScoreSummary: Optional[CanonicalScoreSummary] = None


class ScoreUploadResponse(BaseModel):
    scoreDocumentId: str
    format: ScoreFormat
    acceptedStatus: ScoreProcessingStatus
    initialProcessingSnapshot: ScoreProcessingSnapshot
    originalFilename: str = Field(description="Original uploaded filename.")


class ScorePreviewResponse(BaseModel):
    scoreDocumentId: str
    artifactRole: ScoreArtifactRole
    availability: ScorePreviewAvailability
    rendererFormat: Optional[str] = None
    pageCount: Optional[int] = None
    revisionToken: Optional[str] = None
    safeSummary: str
    failureCode: Optional[str] = None
    failureSeverity: Optional[str] = None
    isRetryable: bool = False
    previewAccess: Optional[str] = None
    originalFilename: Optional[str] = None
    canonicalScoreSummary: Optional[CanonicalScoreSummary] = None


class ScoreReadResponse(BaseModel):
    scoreDocumentId: str
    transpositionCaseId: str
    processingStatus: ScoreProcessingStatus
    originalFilename: str
    safeSummary: str
    latestTransformationJobId: Optional[str] = None
    sourcePreview: Optional[ScorePreviewResponse] = None
    resultPreview: Optional[ScorePreviewResponse] = None
