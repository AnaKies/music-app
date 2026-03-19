from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class ScoreFormat(str, Enum):
    MUSICXML = "musicxml"


class ScoreProcessingStatus(str, Enum):
    UPLOADED = "uploaded"
    PARSED = "parsed"
    PARSE_FAILED = "parse_failed"


class ParseFailureType(str, Enum):
    INVALID_XML = "invalid_xml"
    UNSUPPORTED_STRUCTURE = "unsupported_structure"
    EMPTY_SCORE = "empty_score"


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
