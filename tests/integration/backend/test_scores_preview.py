from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.api.schemas.cases import CaseStatus
from backend.api.schemas.recommendations import RecommendationConfidence
from backend.api.schemas.scores import ParseFailureType, ScoreFormat, ScoreProcessingStatus
from backend.api.schemas.transformations import TransformationStatus
from backend.database import Base, engine, get_db
from backend.domain.cases.models import TranspositionCase
from backend.domain.recommendations.models import RangeRecommendation
from backend.domain.scores.models import CanonicalScore, ScoreDocument
from backend.domain.transformations.models import TransformationJob
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
            response = client.get(
                "/scores/score-preview-content/preview/content?revision=2026-03-20T10:00:00+00:00"
            )

        assert response.status_code == 409
        assert response.json() == {
            "detail": "The requested score preview revision is stale.",
        }
    finally:
        app.dependency_overrides.clear()
        transaction.rollback()
        session.close()
        connection.close()


def test_get_scores_preview_content_returns_musicxml_document_for_matching_revision():
    _reset_tables()
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)
    _seed_case(session, "case-preview-content")
    score_document = ScoreDocument(
        id="score-preview-content",
        transposition_case_id="case-preview-content",
        original_filename="example.musicxml",
        format=ScoreFormat.MUSICXML,
        processing_status=ScoreProcessingStatus.PARSED,
        storage_uri="local://scores/case-preview-content/example.musicxml",
        source_musicxml="<score-partwise version='4.0'></score-partwise>",
        content_size=64,
    )
    session.add(score_document)
    session.commit()
    app.dependency_overrides[get_db] = _override_get_db(session)

    try:
        revision = score_document.created_at.isoformat()
        with TestClient(app) as client:
            response = client.get(f"/scores/score-preview-content/preview/content?revision={revision}")

        assert response.status_code == 200
        assert response.headers["content-type"].startswith("application/vnd.recordare.musicxml+xml")
        assert response.text.startswith("<?xml")
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


def test_get_scores_download_returns_transformed_musicxml_artifact():
    _reset_tables()
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)
    _seed_case(session, "case-result-download")
    score_document = ScoreDocument(
        id="score-download-ready",
        transposition_case_id="case-result-download",
        original_filename="example.musicxml",
        format=ScoreFormat.MUSICXML,
        processing_status=ScoreProcessingStatus.COMPLETED,
        storage_uri="local://scores/case-result-download/example.musicxml",
        source_musicxml="<score-partwise version='4.0'></score-partwise>",
        content_size=256,
    )
    session.add(score_document)
    session.flush()
    session.add(
        TransformationJob(
            id="job-download-ready",
            transposition_case_id="case-result-download",
            score_document_id=score_document.id,
            recommendation_id="rec-1",
            status=TransformationStatus.COMPLETED,
            selected_range_min="G3",
            selected_range_max="D5",
            semitone_shift=-2,
            safe_summary="The deterministic transformation completed successfully.",
            warnings=[],
            transformed_musicxml="<score-partwise version='4.0'></score-partwise>",
            result_storage_uri="local://transformations/job-download-ready/example-transformed.musicxml",
            result_filename="example-transformed.musicxml",
            result_revision_token="2026-03-20T11:00:00+00:00",
        )
    )
    session.commit()
    app.dependency_overrides[get_db] = _override_get_db(session)

    try:
        with TestClient(app) as client:
            response = client.get("/scores/score-download-ready/download?artifact=result")

        assert response.status_code == 200
        assert response.headers["content-type"].startswith("application/vnd.recordare.musicxml+xml")
        assert response.headers["content-disposition"] == 'attachment; filename="example-transformed.musicxml"'
        assert response.text.startswith("<?xml")
        assert "<score-partwise" in response.text
    finally:
        app.dependency_overrides.clear()
        transaction.rollback()
        session.close()
        connection.close()


def test_get_scores_download_rejects_unsupported_artifact_selector():
    _reset_tables()
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)
    _seed_case(session, "case-result-download")
    session.add(
        ScoreDocument(
            id="score-download-ready",
            transposition_case_id="case-result-download",
            original_filename="example.musicxml",
            format=ScoreFormat.MUSICXML,
            processing_status=ScoreProcessingStatus.PARSED,
            storage_uri="local://scores/case-result-download/example.musicxml",
            source_musicxml="<score-partwise version='4.0'></score-partwise>",
            content_size=64,
        )
    )
    session.commit()
    app.dependency_overrides[get_db] = _override_get_db(session)

    try:
        with TestClient(app) as client:
            response = client.get("/scores/score-download-ready/download?artifact=source")

        assert response.status_code == 422
        assert response.json() == {"detail": "Only result artifact downloads are supported."}
    finally:
        app.dependency_overrides.clear()
        transaction.rollback()
        session.close()
        connection.close()


def test_get_scores_read_returns_ready_result_preview_after_exported_transformation():
    _reset_tables()
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)
    _seed_case(session, "case-preview-result")
    score_document = ScoreDocument(
        id="score-preview-result",
        transposition_case_id="case-preview-result",
        original_filename="example.musicxml",
        format=ScoreFormat.MUSICXML,
        processing_status=ScoreProcessingStatus.PARSED,
        storage_uri="local://scores/case-preview-result/example.musicxml",
        source_musicxml="<score-partwise version='4.0'><part-list><score-part id='P1'><part-name>Flute</part-name></score-part></part-list><part id='P1'><measure number='1'><note><pitch><step>C</step><octave>4</octave></pitch><duration>4</duration></note></measure></part></score-partwise>",
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
            measure_count=1,
            note_count=1,
            rest_count=0,
        )
    )
    session.add(
        TransformationJob(
            id="job-result-preview",
            transposition_case_id="case-preview-result",
            score_document_id=score_document.id,
            recommendation_id="rec-1",
            status="completed",
            selected_range_min="G3",
            selected_range_max="D5",
            semitone_shift=0,
            safe_summary="The deterministic transformation completed successfully.",
            warnings=[],
            transformed_musicxml="<score-partwise version='4.0'><part-list><score-part id='P1'><part-name>Flute</part-name></score-part></part-list><part id='P1'><measure number='1'><note><pitch><step>D</step><octave>4</octave></pitch><duration>4</duration></note></measure></part></score-partwise>",
            result_storage_uri="local://transformations/job-result-preview/example-transformed.musicxml",
            result_filename="example-transformed.musicxml",
            result_revision_token="2026-03-20T18:00:00+00:00",
        )
    )
    session.commit()
    app.dependency_overrides[get_db] = _override_get_db(session)

    try:
        with TestClient(app) as client:
            response = client.get("/scores/score-preview-result")

        assert response.status_code == 200
        payload = response.json()
        assert payload["latestTransformationJobId"] == "job-result-preview"
        assert payload["resultPreview"]["availability"] == "ready"
        assert payload["resultPreview"]["previewAccess"] == (
            "/transformations/job-result-preview/preview/content?revision=2026-03-20T18%3A00%3A00%2B00%3A00"
        )
        assert payload["resultPreview"]["originalFilename"] == "example-transformed.musicxml"
    finally:
        app.dependency_overrides.clear()
        transaction.rollback()
        session.close()
        connection.close()


def test_get_transformation_preview_content_returns_exported_musicxml_for_matching_revision():
    _reset_tables()
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)
    _seed_case(session, "case-preview-result")
    session.add(
        TransformationJob(
            id="job-result-content",
            transposition_case_id="case-preview-result",
            score_document_id="score-preview-result",
            recommendation_id="rec-1",
            status="completed",
            selected_range_min="G3",
            selected_range_max="D5",
            semitone_shift=0,
            safe_summary="The deterministic transformation completed successfully.",
            warnings=[],
            transformed_musicxml="<score-partwise version='4.0'></score-partwise>",
            result_storage_uri="local://transformations/job-result-content/example-transformed.musicxml",
            result_filename="example-transformed.musicxml",
            result_revision_token="2026-03-20T18:00:00+00:00",
        )
    )
    session.commit()
    app.dependency_overrides[get_db] = _override_get_db(session)

    try:
        with TestClient(app) as client:
            response = client.get(
                "/transformations/job-result-content/preview/content?revision=2026-03-20T18%3A00%3A00%2B00%3A00"
            )

        assert response.status_code == 200
        assert response.headers["content-type"].startswith("application/vnd.recordare.musicxml+xml")
        assert "<score-partwise" in response.text
    finally:
        app.dependency_overrides.clear()
        transaction.rollback()
        session.close()
        connection.close()


def test_get_score_read_returns_preview_models_and_recommendation_pending_state():
    _reset_tables()
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)
    _seed_case(session, "case-read")
    score_document = ScoreDocument(
        id="score-read-pending",
        transposition_case_id="case-read",
        original_filename="example.musicxml",
        format=ScoreFormat.MUSICXML,
        processing_status=ScoreProcessingStatus.PARSED,
        storage_uri="local://scores/case-read/example.musicxml",
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
            response = client.get("/scores/score-read-pending")

        assert response.status_code == 200
        payload = response.json()
        assert payload["processingStatus"] == "recommendation_pending"
        assert payload["sourcePreview"]["availability"] == "ready"
        assert payload["resultPreview"]["availability"] == "unavailable"
    finally:
        app.dependency_overrides.clear()
        transaction.rollback()
        session.close()
        connection.close()


def test_get_score_read_returns_recommendation_ready_when_recommendations_exist():
    _reset_tables()
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)
    _seed_case(session, "case-read-ready")
    score_document = ScoreDocument(
        id="score-read-ready",
        transposition_case_id="case-read-ready",
        original_filename="example.musicxml",
        format=ScoreFormat.MUSICXML,
        processing_status=ScoreProcessingStatus.PARSED,
        storage_uri="local://scores/case-read-ready/example.musicxml",
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
    session.add(
        RangeRecommendation(
            id="rec-1",
            transposition_case_id="case-read-ready",
            score_document_id=score_document.id,
            label="Primary recommendation",
            target_range_min="G3",
            target_range_max="D5",
            recommended_key="concert_c",
            confidence=RecommendationConfidence.MEDIUM,
            summary_reason="Matches the confirmed player comfort range.",
            warnings=[],
            is_primary=True,
        )
    )
    session.commit()
    app.dependency_overrides[get_db] = _override_get_db(session)

    try:
        with TestClient(app) as client:
            response = client.get("/scores/score-read-ready")

        assert response.status_code == 200
        payload = response.json()
        assert payload["processingStatus"] == "recommendation_ready"
    finally:
        app.dependency_overrides.clear()
        transaction.rollback()
        session.close()
        connection.close()
