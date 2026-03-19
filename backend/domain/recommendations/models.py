import uuid
from datetime import datetime, timezone

from sqlalchemy import JSON, Boolean, Column, DateTime, Enum, ForeignKey, String

from backend.api.schemas.recommendations import RecommendationConfidence
from backend.database import Base


class RangeRecommendation(Base):
    __tablename__ = "range_recommendations"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    transposition_case_id = Column(String, ForeignKey("transposition_cases.id"), nullable=False, index=True)
    score_document_id = Column(String, ForeignKey("score_documents.id"), nullable=False, index=True)
    label = Column(String, nullable=False)
    target_range_min = Column(String, nullable=False)
    target_range_max = Column(String, nullable=False)
    recommended_key = Column(String, nullable=True)
    confidence = Column(Enum(RecommendationConfidence), nullable=False)
    summary_reason = Column(String, nullable=False)
    warnings = Column(JSON, nullable=False, default=list)
    is_primary = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
