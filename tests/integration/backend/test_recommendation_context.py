from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.database import Base, engine, get_db
from backend.domain.cases.models import TranspositionCase
from backend.domain.interviews.models import InterviewSession
from backend.domain.scores.models import CanonicalScore, ScoreDocument
from backend.main import app


def _reset_tables() -> None:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def _override_get_db(session: Session):
    def _dependency():
        try:
            yield session
        finally:
            pass

    return _dependency


def _seed_case_with_score(session: Session) -> None:
    session.add(
        TranspositionCase(
            id="case-1",
            status="ready_for_upload",
            instrument_identity="flute",
            restricted_registers=["high_register"],
            difficult_keys=["needs_clarification"],
            comfort_range_min="G3",
            comfort_range_max="D5",
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
            content_size=128,
        )
    )
    session.add(
        CanonicalScore(
            score_document_id="score-1",
            schema_version="v1",
            title="Study",
            parts=[{"id": "P1", "name": "Flute"}],
            measure_count=12,
            note_count=48,
            rest_count=6,
        )
    )
    session.commit()


def test_post_recommendation_context_builds_full_context():
    _reset_tables()
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)
    _seed_case_with_score(session)
    session.add(
        InterviewSession(
            case_id="case-1",
            status="completed",
            current_question_id=None,
            answers=[
                {
                    "questionId": "additional_context",
                    "questionType": "note_text",
                    "value": {"text": "not sure about sustained high phrases"},
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
                "/recommendations/context",
                json={"transpositionCaseId": "case-1", "scoreDocumentId": "score-1"},
            )

        assert response.status_code == 200
        payload = response.json()
        assert payload["contextVersion"] == "v1"
        assert payload["confirmedConstraints"]["instrumentIdentity"] == "flute"
        assert payload["confirmedConstraints"]["comfortRangeMin"] == "G3"
        assert payload["instrumentKnowledge"]["displayName"] == "Flute"
        assert payload["scoreSummary"] == {
            "schemaVersion": "v1",
            "title": "Study",
            "partCount": 1,
            "measureCount": 12,
            "noteCount": 48,
            "restCount": 6,
            "partNames": ["Flute"],
        }
        assert payload["inferredConstraints"] == {
            "source": "interview_low_confidence",
            "confidence": "low",
            "advisoryNotes": [
                "not sure about sustained high phrases",
                "User uncertainty triggered follow-up handling.",
            ],
        }
    finally:
        app.dependency_overrides.clear()
        transaction.rollback()
        session.close()
        connection.close()


def test_post_recommendation_context_handles_missing_inferred_constraints():
    _reset_tables()
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)
    _seed_case_with_score(session)
    app.dependency_overrides[get_db] = _override_get_db(session)

    try:
        with TestClient(app) as client:
            response = client.post(
                "/recommendations/context",
                json={"transpositionCaseId": "case-1", "scoreDocumentId": "score-1"},
            )

        assert response.status_code == 200
        payload = response.json()
        assert payload["inferredConstraints"] is None
    finally:
        app.dependency_overrides.clear()
        transaction.rollback()
        session.close()
        connection.close()
