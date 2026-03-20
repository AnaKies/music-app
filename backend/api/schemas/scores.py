from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class ScoreFormat(str, Enum):
    MUSICXML = "musicxml"


class ScoreProcessingStatus(str, Enum):
    UPLOADED = "uploaded"


class ScoreProcessingSnapshot(BaseModel):
    scoreDocumentId: str
    transpositionCaseId: str
    processingStatus: ScoreProcessingStatus
    acceptedAt: datetime


class ScoreUploadResponse(BaseModel):
    scoreDocumentId: str
    format: ScoreFormat
    acceptedStatus: ScoreProcessingStatus
    initialProcessingSnapshot: ScoreProcessingSnapshot
    originalFilename: str = Field(description="Original uploaded filename.")
