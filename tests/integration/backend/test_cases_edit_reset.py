from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.api.schemas.cases import CaseStatus
from backend.api.schemas.interviews import InterviewSessionStatus
from backend.api.schemas.recommendations import RecommendationConfidence
from backend.api.schemas.scores import ScoreFormat, ScoreProcessingStatus
from backend.api.schemas.transformations import TransformationStatus
from backend.database import Base, engine, get_db
from backend.domain.cases.models import TranspositionCase
from backend.domain.interviews.models import InterviewSession
from backend.domain.recommendations.models import RangeRecommendation
from backend.domain.scores.models import ScoreDocument
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


def test_patch_case_updates_constraints_and_clears_downstream_runtime_state():
    _reset_tables()

    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)
    case = TranspositionCase(
        id="case-edit-1",
        status=CaseStatus.READY_FOR_UPLOAD,
        instrument_identity="trumpet-bb",
        comfort_range_min="G3",
        comfort_range_max="D5",
    )
    session.add(case)
    session.flush()
    session.add(
        ScoreDocument(
            id="score-edit-1",
            transposition_case_id=case.id,
            original_filename="example.musicxml",
            format=ScoreFormat.MUSICXML,
            processing_status=ScoreProcessingStatus.PARSED,
            storage_uri="local://scores/case-edit-1/example.musicxml",
            source_musicxml="<score-partwise version='4.0'></score-partwise>",
            content_size=64,
        )
    )
    session.add(
        RangeRecommendation(
            id="rec-edit-1",
            transposition_case_id=case.id,
            score_document_id="score-edit-1",
            label="Primary recommendation",
            target_range_min="G3",
            target_range_max="D5",
            confidence=RecommendationConfidence.MEDIUM,
            summary_reason="Matches the current confirmed range.",
            warnings=[],
            is_primary=True,
        )
    )
    session.add(
        TransformationJob(
            id="job-edit-1",
            transposition_case_id=case.id,
            score_document_id="score-edit-1",
            recommendation_id="rec-edit-1",
            status=TransformationStatus.COMPLETED,
            selected_range_min="G3",
            selected_range_max="D5",
            semitone_shift=-2,
            safe_summary="The deterministic transformation completed successfully.",
            warnings=[],
        )
    )
    session.commit()
    app.dependency_overrides[get_db] = _override_get_db(session)

    try:
        with TestClient(app) as client:
            response = client.patch(
                "/cases/case-edit-1",
                json={
                    "instrumentIdentity": "flute",
                    "constraints": {
                        "highest_playable_tone": None,
                        "lowest_playable_tone": None,
                        "restricted_tones": [],
                        "restricted_registers": [],
                        "difficult_keys": [],
                        "preferred_keys": [],
                        "comfort_range_min": "A3",
                        "comfort_range_max": "E5",
                    },
                },
            )

        assert response.status_code == 200
        payload = response.json()
        assert payload["instrumentIdentity"] == "flute"
        assert payload["status"] == "ready_for_upload"
        assert payload["constraints"]["comfort_range_min"] == "A3"
        assert payload["constraints"]["comfort_range_max"] == "E5"
        assert session.query(ScoreDocument).filter(ScoreDocument.id == "score-edit-1").first() is not None
        assert session.query(RangeRecommendation).filter(RangeRecommendation.id == "rec-edit-1").first() is None
        assert session.query(TransformationJob).filter(TransformationJob.id == "job-edit-1").first() is None
    finally:
        app.dependency_overrides.clear()
        transaction.rollback()
        session.close()
        connection.close()


def test_post_case_reset_clears_case_state_and_related_runtime_records():
    _reset_tables()

    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)
    case = TranspositionCase(
        id="case-reset-1",
        status=CaseStatus.READY_FOR_UPLOAD,
        instrument_identity="clarinet-bb",
        comfort_range_min="G3",
        comfort_range_max="D5",
        difficult_keys=["needs_clarification"],
    )
    session.add(case)
    session.flush()
    session.add(
        InterviewSession(
            id="interview-reset-1",
            case_id=case.id,
            status=InterviewSessionStatus.COMPLETED,
            current_question_id=None,
            answers=[],
            low_confidence={"active": False},
        )
    )
    session.add(
        ScoreDocument(
            id="score-reset-1",
            transposition_case_id=case.id,
            original_filename="example.musicxml",
            format=ScoreFormat.MUSICXML,
            processing_status=ScoreProcessingStatus.PARSED,
            storage_uri="local://scores/case-reset-1/example.musicxml",
            source_musicxml="<score-partwise version='4.0'></score-partwise>",
            content_size=64,
        )
    )
    session.add(
        RangeRecommendation(
            id="rec-reset-1",
            transposition_case_id=case.id,
            score_document_id="score-reset-1",
            label="Primary recommendation",
            target_range_min="G3",
            target_range_max="D5",
            confidence=RecommendationConfidence.MEDIUM,
            summary_reason="Matches the current confirmed range.",
            warnings=[],
            is_primary=True,
        )
    )
    session.add(
        TransformationJob(
            id="job-reset-1",
            transposition_case_id=case.id,
            score_document_id="score-reset-1",
            recommendation_id="rec-reset-1",
            status=TransformationStatus.COMPLETED,
            selected_range_min="G3",
            selected_range_max="D5",
            semitone_shift=-2,
            safe_summary="The deterministic transformation completed successfully.",
            warnings=[],
        )
    )
    session.commit()
    app.dependency_overrides[get_db] = _override_get_db(session)

    try:
        with TestClient(app) as client:
            response = client.post("/cases/case-reset-1/reset")

        assert response.status_code == 200
        payload = response.json()
        assert payload["status"] == "new"
        assert payload["scoreCount"] == 0
        assert payload["latestScoreDocumentId"] is None
        assert payload["constraints"] == {
            "highest_playable_tone": None,
            "lowest_playable_tone": None,
            "restricted_tones": [],
            "restricted_registers": [],
            "difficult_keys": [],
            "preferred_keys": [],
            "comfort_range_min": None,
            "comfort_range_max": None,
        }
        assert session.query(InterviewSession).filter(InterviewSession.id == "interview-reset-1").first() is None
        assert session.query(ScoreDocument).filter(ScoreDocument.id == "score-reset-1").first() is None
        assert session.query(RangeRecommendation).filter(RangeRecommendation.id == "rec-reset-1").first() is None
        assert session.query(TransformationJob).filter(TransformationJob.id == "job-reset-1").first() is None
    finally:
        app.dependency_overrides.clear()
        transaction.rollback()
        session.close()
        connection.close()
