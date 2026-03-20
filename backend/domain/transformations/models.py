import uuid
from datetime import datetime, timezone

from sqlalchemy import JSON, Column, DateTime, Enum, ForeignKey, Integer, String, Text

from backend.api.schemas.transformations import TransformationStatus
from backend.database import Base


class TransformationJob(Base):
    __tablename__ = "transformation_jobs"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    transposition_case_id = Column(String, ForeignKey("transposition_cases.id"), nullable=False, index=True)
    score_document_id = Column(String, ForeignKey("score_documents.id"), nullable=False, index=True)
    recommendation_id = Column(String, ForeignKey("range_recommendations.id"), nullable=False, index=True)
    status = Column(Enum(TransformationStatus), nullable=False, default=TransformationStatus.COMPLETED)
    selected_range_min = Column(String, nullable=False)
    selected_range_max = Column(String, nullable=False)
    semitone_shift = Column(Integer, nullable=True)
    safe_summary = Column(String, nullable=False)
    warnings = Column(JSON, nullable=False, default=list)
    transformed_musicxml = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
