from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.database import Base, engine, get_db
from backend.domain.cases.models import TranspositionCase
from backend.domain.recommendations.models import RangeRecommendation
from backend.domain.scores.models import CanonicalScore, ScoreDocument
from backend.domain.transformations.models import TransformationJob
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


def _seed_case_score_and_recommendation(session: Session, *, wide_score: bool = False) -> None:
    session.add(
        TranspositionCase(
            id="case-1",
            status="ready_for_upload",
            instrument_identity="flute",
            comfort_range_min="G3",
            comfort_range_max="D5",
        )
    )
    source_musicxml = (
        """<?xml version='1.0' encoding='UTF-8'?>
        <score-partwise version='4.0'>
          <part-list>
            <score-part id='P1'><part-name>Flute</part-name></score-part>
          </part-list>
          <part id='P1'>
            <measure number='1'>
              <note><pitch><step>C</step><octave>4</octave></pitch><duration>4</duration></note>
              <note><pitch><step>E</step><octave>4</octave></pitch><duration>4</duration></note>
            </measure>
          </part>
        </score-partwise>"""
        if not wide_score
        else """<?xml version='1.0' encoding='UTF-8'?>
        <score-partwise version='4.0'>
          <part-list>
            <score-part id='P1'><part-name>Flute</part-name></score-part>
          </part-list>
          <part id='P1'>
            <measure number='1'>
              <note><pitch><step>C</step><octave>3</octave></pitch><duration>4</duration></note>
              <note><pitch><step>C</step><octave>6</octave></pitch><duration>4</duration></note>
            </measure>
          </part>
        </score-partwise>"""
    )
    session.add(
        ScoreDocument(
            id="score-1",
            transposition_case_id="case-1",
            original_filename="example.musicxml",
            format="musicxml",
            processing_status="parsed",
            storage_uri="local://scores/case-1/example.musicxml",
            source_musicxml=source_musicxml,
            content_size=512,
        )
    )
    session.add(
        CanonicalScore(
            score_document_id="score-1",
            schema_version="v1",
            title="Study",
            parts=[{"id": "P1", "name": "Flute"}],
            measure_count=1,
            note_count=2,
            rest_count=0,
        )
    )
    session.add(
        RangeRecommendation(
            id="rec-1",
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
        )
    )
    session.commit()


def _update_recommendation_range(session: Session, *, range_min: str, range_max: str) -> None:
    recommendation = session.query(RangeRecommendation).filter(RangeRecommendation.id == "rec-1").first()
    assert recommendation is not None
    recommendation.target_range_min = range_min
    recommendation.target_range_max = range_max
    session.add(recommendation)
    session.commit()


def test_post_transformations_accepts_valid_selected_recommendation():
    _reset_tables()
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)
    _seed_case_score_and_recommendation(session)
    app.dependency_overrides[get_db] = _override_get_db(session)

    try:
        with TestClient(app) as client:
            response = client.post(
                "/transformations",
                json={
                    "transpositionCaseId": "case-1",
                    "scoreDocumentId": "score-1",
                    "recommendationId": "rec-1",
                },
            )

        assert response.status_code == 202
        payload = response.json()
        assert payload["status"] == "completed"
        assert payload["recommendationId"] == "rec-1"
        assert payload["warnings"] == []
        persisted = session.query(TransformationJob).filter(TransformationJob.score_document_id == "score-1").all()
        assert len(persisted) == 1
        assert persisted[0].transformed_musicxml is not None
        assert persisted[0].transformed_musicxml.startswith("<?xml")
        assert persisted[0].result_storage_uri is not None
        assert persisted[0].result_filename == "example-transformed.musicxml"
        assert persisted[0].result_revision_token is not None
        assert persisted[0].exported_at is not None
    finally:
        app.dependency_overrides.clear()
        transaction.rollback()
        session.close()
        connection.close()


def test_post_transformations_rejects_unknown_or_stale_recommendation():
    _reset_tables()
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)
    _seed_case_score_and_recommendation(session)
    app.dependency_overrides[get_db] = _override_get_db(session)

    try:
        with TestClient(app) as client:
            response = client.post(
                "/transformations",
                json={
                    "transpositionCaseId": "case-1",
                    "scoreDocumentId": "score-1",
                    "recommendationId": "rec-missing",
                },
            )

        assert response.status_code == 409
        assert response.json() == {
            "detail": "The selected recommendation is unknown or stale.",
        }
    finally:
        app.dependency_overrides.clear()
        transaction.rollback()
        session.close()
        connection.close()


def test_post_transformations_emits_structured_warning_when_score_cannot_fit_cleanly():
    _reset_tables()
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)
    _seed_case_score_and_recommendation(session, wide_score=True)
    app.dependency_overrides[get_db] = _override_get_db(session)

    try:
        with TestClient(app) as client:
            response = client.post(
                "/transformations",
                json={
                    "transpositionCaseId": "case-1",
                    "scoreDocumentId": "score-1",
                    "recommendationId": "rec-1",
                },
            )

        assert response.status_code == 202
        payload = response.json()
        assert payload["status"] == "completed"
        assert len(payload["warnings"]) >= 1
        assert payload["warnings"][0]["severity"] == "warning"
    finally:
        app.dependency_overrides.clear()
        transaction.rollback()
        session.close()
        connection.close()


def test_post_transformations_rejects_raw_ai_text_boundary_regression():
    _reset_tables()
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)
    _seed_case_score_and_recommendation(session)
    app.dependency_overrides[get_db] = _override_get_db(session)

    try:
        with TestClient(app) as client:
            response = client.post(
                "/transformations",
                json={
                    "transpositionCaseId": "case-1",
                    "scoreDocumentId": "score-1",
                    "recommendationId": "rec-1",
                    "rawAiText": "transpose it however the model prefers",
                },
            )

        assert response.status_code == 422
    finally:
        app.dependency_overrides.clear()
        transaction.rollback()
        session.close()
        connection.close()


def test_post_transformations_accepts_flat_range_notation_from_selected_recommendation():
    _reset_tables()
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)
    _seed_case_score_and_recommendation(session)
    _update_recommendation_range(session, range_min="Bb3", range_max="F5")
    app.dependency_overrides[get_db] = _override_get_db(session)

    try:
        with TestClient(app) as client:
            response = client.post(
                "/transformations",
                json={
                    "transpositionCaseId": "case-1",
                    "scoreDocumentId": "score-1",
                    "recommendationId": "rec-1",
                },
            )

        assert response.status_code == 202
        assert response.json()["status"] == "completed"
    finally:
        app.dependency_overrides.clear()
        transaction.rollback()
        session.close()
        connection.close()


def test_post_transformations_returns_precise_error_for_invalid_target_range_format():
    _reset_tables()
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)
    _seed_case_score_and_recommendation(session)
    _update_recommendation_range(session, range_min="middle c", range_max="D5")
    app.dependency_overrides[get_db] = _override_get_db(session)

    try:
        with TestClient(app) as client:
            response = client.post(
                "/transformations",
                json={
                    "transpositionCaseId": "case-1",
                    "scoreDocumentId": "score-1",
                    "recommendationId": "rec-1",
                },
            )

        assert response.status_code == 422
        assert response.json() == {
            "detail": "The selected recommendation range is not in a supported note format.",
        }
    finally:
        app.dependency_overrides.clear()
        transaction.rollback()
        session.close()
        connection.close()


def test_post_transformations_accepts_reversed_range_order_from_existing_recommendation_data():
    _reset_tables()
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)
    _seed_case_score_and_recommendation(session)
    _update_recommendation_range(session, range_min="G2", range_max="D2")
    app.dependency_overrides[get_db] = _override_get_db(session)

    try:
        with TestClient(app) as client:
            response = client.post(
                "/transformations",
                json={
                    "transpositionCaseId": "case-1",
                    "scoreDocumentId": "score-1",
                    "recommendationId": "rec-1",
                },
            )

        assert response.status_code == 202
        assert response.json()["status"] == "completed"
    finally:
        app.dependency_overrides.clear()
        transaction.rollback()
        session.close()
        connection.close()
