import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from backend.api.schemas.scores import ScoreFormat, ScoreProcessingStatus
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
    storage_uri = Column(String, nullable=False)
    content_size = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    case = relationship("TranspositionCase", back_populates="scores")
