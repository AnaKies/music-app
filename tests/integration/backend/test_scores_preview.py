from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.api.schemas.cases import CaseStatus
from backend.api.schemas.scores import ParseFailureType, ScoreFormat, ScoreProcessingStatus
from backend.database import Base, engine, get_db
from backend.domain.cases.models import TranspositionCase
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


def _seed_case(session: Session, case_id: str) -> None:
    session.add(
        TranspositionCase(
            id=case_id,
            status=CaseStatus.READY_FOR_UPLOAD,
            instrument_identity="flute",
            comfort_range_min="G3",
            comfort_range_max="D5",
        )
    )
    session.commit()


def test_get_scores_preview_returns_ready_source_preview_contract():
    _reset_tables()
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)
    _seed_case(session, "case-preview")
    score_document = ScoreDocument(
        id="score-preview-ready",
        transposition_case_id="case-preview",
        original_filename="example.musicxml",
        format=ScoreFormat.MUSICXML,
        processing_status=ScoreProcessingStatus.PARSED,
        storage_uri="local://scores/case-preview/example.musicxml",
        source_musicxml="<score-partwise version='4.0'></score-partwise>",
        content_size=512,
    )
    session.add(score_document)
    session.flush()
    session.add(
        CanonicalScore(
            score_document_id=score_document.id,
            schema_version="v1",
            title="Etude in C",
            parts=[{"id": "P1", "name": "Flute"}],
            measure_count=12,
            note_count=48,
            rest_count=4,
        )
    )
    session.commit()
    app.dependency_overrides[get_db] = _override_get_db(session)

    try:
        with TestClient(app) as client:
            response = client.get("/scores/score-preview-ready/preview")

        assert response.status_code == 200
        payload = response.json()
        assert payload["scoreDocumentId"] == "score-preview-ready"
        assert payload["artifactRole"] == "source"
        assert payload["availability"] == "ready"
        assert payload["rendererFormat"] == "musicxml_preview"
        assert payload["safeSummary"] == "The uploaded score is ready for read-only preview."
        assert payload["previewAccess"].startswith("/scores/score-preview-ready/preview/content?revision=")
        assert payload["canonicalScoreSummary"] == {
            "schemaVersion": "v1",
            "title": "Etude in C",
            "partCount": 1,
            "measureCount": 12,
            "noteCount": 48,
            "restCount": 4,
            "parts": [{"partId": "P1", "name": "Flute"}],
        }
        assert "storage_uri" not in payload
        assert "local://" not in str(payload)
    finally:
        app.dependency_overrides.clear()
        transaction.rollback()
        session.close()
        connection.close()


def test_get_scores_preview_content_returns_musicxml_document():
    _reset_tables()
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)
    _seed_case(session, "case-preview-content")
    session.add(
        ScoreDocument(
            id="score-preview-content",
            transposition_case_id="case-preview-content",
            original_filename="example.musicxml",
            format=ScoreFormat.MUSICXML,
            processing_status=ScoreProcessingStatus.PARSED,
            storage_uri="local://scores/case-preview-content/example.musicxml",
            source_musicxml="<score-partwise version='4.0'></score-partwise>",
            content_size=64,
        )
    )
    session.commit()
    app.dependency_overrides[get_db] = _override_get_db(session)

    try:
        with TestClient(app) as client:
            response = client.get("/scores/score-preview-content/preview/content")

        assert response.status_code == 200
        assert response.headers["content-type"].startswith("application/vnd.recordare.musicxml+xml")
        assert "<score-partwise" in response.text
    finally:
        app.dependency_overrides.clear()
        transaction.rollback()
        session.close()
        connection.close()


def test_get_scores_preview_returns_unavailable_for_legacy_score_without_stored_musicxml():
    _reset_tables()
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)
    _seed_case(session, "case-preview-legacy")
    score_document = ScoreDocument(
        id="score-preview-legacy",
        transposition_case_id="case-preview-legacy",
        original_filename="legacy.musicxml",
        format=ScoreFormat.MUSICXML,
        processing_status=ScoreProcessingStatus.PARSED,
        storage_uri="local://scores/case-preview-legacy/legacy.musicxml",
        content_size=128,
    )
    session.add(score_document)
    session.flush()
    session.add(
        CanonicalScore(
            score_document_id=score_document.id,
            schema_version="v1",
            title="Legacy Score",
            parts=[{"id": "P1", "name": "Flute"}],
            measure_count=8,
            note_count=20,
            rest_count=2,
        )
    )
    session.commit()
    app.dependency_overrides[get_db] = _override_get_db(session)

    try:
        with TestClient(app) as client:
            response = client.get("/scores/score-preview-legacy/preview")

        assert response.status_code == 200
        payload = response.json()
        assert payload["availability"] == "unavailable"
        assert payload["previewAccess"] is None
        assert "Upload it again" in payload["safeSummary"]
    finally:
        app.dependency_overrides.clear()
        transaction.rollback()
        session.close()
        connection.close()


def test_get_scores_preview_returns_failed_state_for_parse_failure():
    _reset_tables()
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)
    _seed_case(session, "case-preview-failed")
    session.add(
        ScoreDocument(
            id="score-preview-failed",
            transposition_case_id="case-preview-failed",
            original_filename="broken.musicxml",
            format=ScoreFormat.MUSICXML,
            processing_status=ScoreProcessingStatus.PARSE_FAILED,
            parse_failure_type=ParseFailureType.INVALID_XML,
            storage_uri="local://scores/case-preview-failed/broken.musicxml",
            content_size=256,
        )
    )
    session.commit()
    app.dependency_overrides[get_db] = _override_get_db(session)

    try:
        with TestClient(app) as client:
            response = client.get("/scores/score-preview-failed/preview")

        assert response.status_code == 200
        payload = response.json()
        assert payload["artifactRole"] == "source"
        assert payload["availability"] == "failed"
        assert payload["safeSummary"] == "The uploaded score could not be prepared for preview."
        assert payload["failureCode"] == "invalid_xml"
        assert payload["failureSeverity"] == "warning"
        assert payload["previewAccess"] is None
        assert "local://" not in str(payload)
    finally:
        app.dependency_overrides.clear()
        transaction.rollback()
        session.close()
        connection.close()
