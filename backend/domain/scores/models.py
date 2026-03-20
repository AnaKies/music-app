import uuid
from datetime import datetime, timezone

from sqlalchemy import JSON, Column, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from backend.api.schemas.scores import ParseFailureType, ScoreFormat, ScoreProcessingStatus
from backend.database import Base


class ScoreDocument(Base):
    __tablename__ = "score_documents"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    transposition_case_id = Column(String, ForeignKey("transposition_cases.id"), nullable=False, index=True)
    original_filename = Column(String, nullable=False)
    format = Column(Enum(ScoreFormat), nullable=False, default=ScoreFormat.MUSICXML)
    processing_status = Column(
        Enum(ScoreProcessingStatus),
        nullable=False,
        default=ScoreProcessingStatus.UPLOADED,
    )
    parse_failure_type = Column(Enum(ParseFailureType), nullable=True)
    storage_uri = Column(String, nullable=False)
    source_musicxml = Column(Text, nullable=True)
    content_size = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    case = relationship("TranspositionCase", back_populates="scores")
    canonical_score = relationship(
        "CanonicalScore",
        back_populates="score_document",
        uselist=False,
        cascade="all, delete-orphan",
    )


class CanonicalScore(Base):
    __tablename__ = "canonical_scores"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    score_document_id = Column(String, ForeignKey("score_documents.id"), nullable=False, unique=True, index=True)
    schema_version = Column(String, nullable=False)
    title = Column(String, nullable=True)
    parts = Column(JSON, nullable=False, default=list)
    measure_count = Column(Integer, nullable=False, default=0)
    note_count = Column(Integer, nullable=False, default=0)
    rest_count = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    score_document = relationship("ScoreDocument", back_populates="canonical_score")
