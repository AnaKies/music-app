from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from typing import Optional

from backend.database import Base, engine, get_db
from backend.domain.cases.models import TranspositionCase
from backend.domain.recommendations.models import RangeRecommendation
from backend.domain.scores.models import CanonicalScore, ScoreDocument
from backend.main import app


def _reset_tables() -> None:
    engine.dispose()
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def _override_get_db(session: Session):
    def _dependency():
        try:
            yield session
        finally:
            pass

    return _dependency


def _seed_case_score(session: Session, *, comfort_min: Optional[str] = "G3", comfort_max: Optional[str] = "D5") -> None:
    session.add(
        TranspositionCase(
            id="case-1",
            status="ready_for_upload",
            instrument_identity="flute",
            restricted_registers=["high_register"],
            comfort_range_min=comfort_min,
            comfort_range_max=comfort_max,
        )
    )
    session.add(
        ScoreDocument(
            id="score-1",
            transposition_case_id="case-1",
            original_filename="example.musicxml",
            format="musicxml",
            processing_status="parsed",
            storage_uri="local://scores/case-1/example.musicxml",
            content_size=256,
        )
    )
    session.add(
        CanonicalScore(
            score_document_id="score-1",
            schema_version="v1",
            title="Study",
            parts=[{"id": "P1", "name": "Flute"}],
            measure_count=8,
            note_count=32,
            rest_count=4,
        )
    )
    session.commit()


def test_post_recommendations_returns_primary_and_secondary_items():
    _reset_tables()
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)
    _seed_case_score(session)
    app.dependency_overrides[get_db] = _override_get_db(session)

    try:
        with TestClient(app) as client:
            response = client.post(
                "/recommendations",
                json={"transpositionCaseId": "case-1", "scoreDocumentId": "score-1"},
            )

        assert response.status_code == 200
        payload = response.json()
        assert payload["status"] == "ready"
        assert len(payload["recommendations"]) == 2
        assert payload["recommendations"][0]["isPrimary"] is True
        assert payload["recommendations"][0]["confidence"] == "medium"
        assert payload["recommendations"][1]["isPrimary"] is False

        persisted = session.query(RangeRecommendation).filter(RangeRecommendation.score_document_id == "score-1").all()
        assert len(persisted) == 2
    finally:
        app.dependency_overrides.clear()
        transaction.rollback()
        session.close()
        connection.close()


def test_post_recommendations_returns_blocked_failure_for_incomplete_context():
    _reset_tables()
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)
    _seed_case_score(session, comfort_min=None, comfort_max=None)
    app.dependency_overrides[get_db] = _override_get_db(session)

    try:
        with TestClient(app) as client:
            response = client.post(
                "/recommendations",
                json={"transpositionCaseId": "case-1", "scoreDocumentId": "score-1"},
            )

        assert response.status_code == 200
        payload = response.json()
        assert payload["status"] == "blocked"
        assert payload["recommendations"] == []
        assert payload["failure"] == {
            "confidence": "blocked",
            "code": "insufficient_context",
            "safeSummary": "The recommendation path is blocked because the case or score context is incomplete.",
        }
    finally:
        app.dependency_overrides.clear()
        transaction.rollback()
        session.close()
        connection.close()
