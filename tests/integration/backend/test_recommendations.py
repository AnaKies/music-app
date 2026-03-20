from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from typing import Optional

from backend.database import Base, engine, get_db
from backend.domain.cases.models import TranspositionCase
from backend.domain.interviews.models import InterviewSession
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
        assert payload["recommendations"][0]["isStale"] is False
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
            "isRetryable": False,
            "failureSeverity": "warning",
        }
    finally:
        app.dependency_overrides.clear()
        transaction.rollback()
        session.close()
        connection.close()


def test_post_recommendations_marks_low_confidence_when_advisory_inference_exists():
    _reset_tables()
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)
    _seed_case_score(session)
    session.add(
        InterviewSession(
            case_id="case-1",
            status="completed",
            current_question_id=None,
            answers=[
                {
                    "questionId": "additional_context",
                    "questionType": "note_text",
                    "value": {"text": "not sure about endurance in the upper register"},
                    "lowConfidenceFlag": True,
                    "answeredAt": "2026-03-19T10:00:00Z",
                }
            ],
            low_confidence={"reason": "User uncertainty triggered follow-up handling."},
        )
    )
    session.commit()
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
        assert payload["recommendations"][0]["confidence"] == "low"
        assert payload["recommendations"][0]["warnings"][0]["code"] == "advisory_inference_present"
    finally:
        app.dependency_overrides.clear()
        transaction.rollback()
        session.close()
        connection.close()


def test_post_recommendations_keeps_payload_presentation_safe():
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
        serialized = str(payload).lower()
        assert "provider" not in serialized
        assert "llm" not in serialized
        assert "model said" not in serialized
    finally:
        app.dependency_overrides.clear()
        transaction.rollback()
        session.close()
        connection.close()


def test_get_recommendations_returns_persisted_stale_state():
    _reset_tables()
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)
    _seed_case_score(session)
    session.add(
        RangeRecommendation(
            id="rec-stale-1",
            transposition_case_id="case-1",
            score_document_id="score-1",
            label="Primary recommendation",
            target_range_min="G3",
            target_range_max="D5",
            recommended_key="concert_c",
            confidence="medium",
            summary_reason="Matches the confirmed player comfort range.",
            warnings=[],
            is_primary=True,
            is_stale=True,
        )
    )
    session.commit()
    app.dependency_overrides[get_db] = _override_get_db(session)

    try:
        with TestClient(app) as client:
            response = client.get("/recommendations", params={"transpositionCaseId": "case-1", "scoreDocumentId": "score-1"})

        assert response.status_code == 200
        payload = response.json()
        assert payload["status"] == "ready"
        assert payload["recommendations"] == [
            {
                "recommendationId": "rec-stale-1",
                "label": "Primary recommendation",
                "targetRange": {"min": "G3", "max": "D5"},
                "recommendedKey": "concert_c",
                "confidence": "medium",
                "summaryReason": "Matches the confirmed player comfort range.",
                "warnings": [],
                "isPrimary": True,
                "isStale": True,
            }
        ]
    finally:
        app.dependency_overrides.clear()
        transaction.rollback()
        session.close()
        connection.close()
