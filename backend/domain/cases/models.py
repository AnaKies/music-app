import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Enum, JSON
from backend.database import Base
from backend.api.schemas.cases import CaseStatus


class TranspositionCase(Base):
    """
    SQLAlchemy model for transposition cases.

    Represents a persistent user and instrument context that can be reused
    across multiple score uploads as defined in the architecture data model.
    """
    __tablename__ = "transposition_cases"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=True, index=True)
    status = Column(Enum(CaseStatus), default=CaseStatus.NEW, nullable=False)
    instrument_identity = Column(String, nullable=False)

    # Constraints as JSON fields for MVP simplicity
    highest_playable_tone = Column(String, nullable=True)
    lowest_playable_tone = Column(String, nullable=True)
    restricted_tones = Column(JSON, default=list)
    restricted_registers = Column(JSON, default=list)
    difficult_keys = Column(JSON, default=list)
    preferred_keys = Column(JSON, default=list)
    comfort_range_min = Column(String, nullable=True)
    comfort_range_max = Column(String, nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    @property
    def score_count(self) -> int:
        # Placeholder for the number of linked scores
        return 0
