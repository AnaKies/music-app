"""
Contract tests for GET /cases/{id}.

Test-2 protects the documented read contract for a single case and its 404
behavior before frontend and follow-up backend work build on top of it.
"""

from datetime import datetime, timezone

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.api.schemas.cases import CaseStatus
from backend.api.schemas.scores import ScoreFormat, ScoreProcessingStatus
from backend.database import Base, engine, get_db
from backend.domain.cases.models import TranspositionCase
from backend.domain.scores.models import ScoreDocument
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


def test_get_case_returns_documented_case_detail_contract():
    _reset_tables()

    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)

    app.dependency_overrides[get_db] = _override_get_db(session)

    test_case = TranspositionCase(
        id="test-case-unique-id",
        status=CaseStatus.READY_FOR_UPLOAD,
        instrument_identity="trumpet-bb",
        highest_playable_tone="G5",
        lowest_playable_tone="E3",
        restricted_tones=["C#5"],
        restricted_registers=["high"],
        difficult_keys=["B"],
        preferred_keys=["F"],
        comfort_range_min="G3",
        comfort_range_max="D5",
    )
    session.add(test_case)
    session.commit()

    try:
        with TestClient(app) as client:
            response = client.get("/cases/test-case-unique-id")

        assert response.status_code == 200

        payload = response.json()
        assert payload["id"] == "test-case-unique-id"
        assert payload["status"] == "ready_for_upload"
        assert payload["instrumentIdentity"] == "trumpet-bb"
        assert payload["scoreCount"] == 0
        assert payload["latestScoreDocumentId"] is None
        assert "createdAt" in payload
        assert "updatedAt" in payload
        assert "userId" not in payload

        assert payload["constraints"] == {
            "highest_playable_tone": "G5",
            "lowest_playable_tone": "E3",
            "restricted_tones": ["C#5"],
            "restricted_registers": ["high"],
            "difficult_keys": ["B"],
            "preferred_keys": ["F"],
            "comfort_range_min": "G3",
            "comfort_range_max": "D5",
        }
    finally:
        app.dependency_overrides.clear()
        transaction.rollback()
        session.close()
        connection.close()


def test_get_case_includes_latest_score_document_id_when_scores_exist():
    _reset_tables()

    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)

    app.dependency_overrides[get_db] = _override_get_db(session)

    test_case = TranspositionCase(
        id="test-case-with-scores",
        status=CaseStatus.READY_FOR_UPLOAD,
        instrument_identity="clarinet-bb",
    )
    session.add(test_case)
    session.flush()
    session.add_all(
        [
            ScoreDocument(
                id="score-older",
                transposition_case_id=test_case.id,
                original_filename="older.musicxml",
                format=ScoreFormat.MUSICXML,
                processing_status=ScoreProcessingStatus.PARSED,
                storage_uri="local://scores/test-case-with-scores/older.musicxml",
                content_size=128,
                created_at=datetime(2026, 3, 20, 10, 0, tzinfo=timezone.utc),
            ),
            ScoreDocument(
                id="score-latest",
                transposition_case_id=test_case.id,
                original_filename="latest.musicxml",
                format=ScoreFormat.MUSICXML,
                processing_status=ScoreProcessingStatus.PARSED,
                storage_uri="local://scores/test-case-with-scores/latest.musicxml",
                content_size=256,
                created_at=datetime(2026, 3, 20, 10, 5, tzinfo=timezone.utc),
            ),
        ]
    )
    session.commit()

    try:
        with TestClient(app) as client:
            response = client.get("/cases/test-case-with-scores")

        assert response.status_code == 200
        payload = response.json()
        assert payload["scoreCount"] == 2
        assert payload["latestScoreDocumentId"] == "score-latest"
    finally:
        app.dependency_overrides.clear()
        transaction.rollback()
        session.close()
        connection.close()


def test_get_case_returns_structured_404_for_unknown_case():
    _reset_tables()

    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)

    app.dependency_overrides[get_db] = _override_get_db(session)

    try:
        with TestClient(app) as client:
            response = client.get("/cases/non-existent-id")

        assert response.status_code == 404
        assert response.json() == {
            "detail": "Case with id non-existent-id not found.",
        }
    finally:
        app.dependency_overrides.clear()
        transaction.rollback()
        session.close()
        connection.close()
