"""
Contract and flow tests for interview endpoints.

These tests cover the F2 MVP path for starting, continuing, and resuming a
structured interview session.
"""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.database import Base, engine, get_db
from backend.domain.cases.models import TranspositionCase
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


def _seed_case(session: Session, case_id: str = "case-f2-1") -> None:
    session.add(
        TranspositionCase(
            id=case_id,
            status="new",
            instrument_identity="placeholder",
        )
    )
    session.commit()


def test_post_interviews_starts_session_and_returns_first_question():
    _reset_tables()

    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)
    _seed_case(session)
    app.dependency_overrides[get_db] = _override_get_db(session)

    try:
        with TestClient(app) as client:
            response = client.post("/interviews", json={"caseId": "case-f2-1"})

        assert response.status_code == 200
        payload = response.json()
        assert payload["caseId"] == "case-f2-1"
        assert payload["status"] == "in_progress"
        assert payload["nextQuestion"]["id"] == "instrument_identity"
        assert payload["nextQuestion"]["type"] == "single_select"
        assert payload["progress"] == {
            "currentStep": 1,
            "totalSteps": 4,
            "percentComplete": 0,
        }
    finally:
        app.dependency_overrides.clear()
        transaction.rollback()
        session.close()
        connection.close()


def test_post_interviews_continues_session_and_can_trigger_low_confidence_follow_up():
    _reset_tables()

    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)
    _seed_case(session)
    app.dependency_overrides[get_db] = _override_get_db(session)

    try:
        with TestClient(app) as client:
            start = client.post("/interviews", json={"caseId": "case-f2-1"})
            interview_id = start.json()["interviewId"]

            instrument = client.post(
                "/interviews",
                json={
                    "caseId": "case-f2-1",
                    "interviewId": interview_id,
                    "questionId": "instrument_identity",
                    "answer": {"selectedOption": "trumpet-bb"},
                },
            )

            assert instrument.status_code == 200
            assert instrument.json()["nextQuestion"]["id"] == "challenge_areas"

            challenge = client.post(
                "/interviews",
                json={
                    "caseId": "case-f2-1",
                    "interviewId": interview_id,
                    "questionId": "challenge_areas",
                    "answer": {"selectedOptions": ["high_register", "difficult_keys"]},
                },
            )

            assert challenge.status_code == 200
            assert challenge.json()["nextQuestion"]["id"] == "comfort_range"

            comfort = client.post(
                "/interviews",
                json={
                    "caseId": "case-f2-1",
                    "interviewId": interview_id,
                    "questionId": "comfort_range",
                    "answer": {"noteRange": {"min": "G3", "max": "D5"}},
                },
            )

            assert comfort.status_code == 200
            assert comfort.json()["nextQuestion"]["id"] == "additional_context"

            follow_up = client.post(
                "/interviews",
                json={
                    "caseId": "case-f2-1",
                    "interviewId": interview_id,
                    "questionId": "additional_context",
                    "answer": {"text": "not sure about the upper register"},
                },
            )

        assert follow_up.status_code == 200
        payload = follow_up.json()
        assert payload["status"] == "awaiting_follow_up"
        assert payload["lowConfidence"] is True
        assert payload["nextQuestion"]["id"] == "additional_context_follow_up"
    finally:
        app.dependency_overrides.clear()
        transaction.rollback()
        session.close()
        connection.close()


def test_get_interviews_reads_structured_session_detail_and_not_found():
    _reset_tables()

    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)
    _seed_case(session)
    app.dependency_overrides[get_db] = _override_get_db(session)

    try:
        with TestClient(app) as client:
            start = client.post("/interviews", json={"caseId": "case-f2-1"})
            interview_id = start.json()["interviewId"]
            client.post(
                "/interviews",
                json={
                    "caseId": "case-f2-1",
                    "interviewId": interview_id,
                    "questionId": "instrument_identity",
                    "answer": {"selectedOption": "trumpet-bb"},
                },
            )

            existing = client.get(f"/interviews/{interview_id}")
            missing = client.get("/interviews/missing-session")

        assert existing.status_code == 200
        payload = existing.json()
        assert payload["interviewId"] == interview_id
        assert payload["caseId"] == "case-f2-1"
        assert payload["currentQuestion"]["id"] == "challenge_areas"
        assert len(payload["collectedAnswers"]) == 1
        assert payload["derivedCaseSummary"]["instrumentIdentity"] == "trumpet-bb"

        assert missing.status_code == 404
        assert missing.json() == {
            "detail": "Interview with id missing-session not found.",
        }
    finally:
        app.dependency_overrides.clear()
        transaction.rollback()
        session.close()
        connection.close()


def test_post_interviews_reuses_completed_session_instead_of_silently_starting_a_new_one():
    _reset_tables()

    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)
    _seed_case(session)
    app.dependency_overrides[get_db] = _override_get_db(session)

    try:
        with TestClient(app) as client:
            start = client.post("/interviews", json={"caseId": "case-f2-1"})
            interview_id = start.json()["interviewId"]

            client.post(
                "/interviews",
                json={
                    "caseId": "case-f2-1",
                    "interviewId": interview_id,
                    "questionId": "instrument_identity",
                    "answer": {"selectedOption": "trumpet-bb"},
                },
            )
            client.post(
                "/interviews",
                json={
                    "caseId": "case-f2-1",
                    "interviewId": interview_id,
                    "questionId": "challenge_areas",
                    "answer": {"selectedOptions": ["high_register"]},
                },
            )
            client.post(
                "/interviews",
                json={
                    "caseId": "case-f2-1",
                    "interviewId": interview_id,
                    "questionId": "comfort_range",
                    "answer": {"noteRange": {"min": "G3", "max": "D5"}},
                },
            )
            final_step = client.post(
                "/interviews",
                json={
                    "caseId": "case-f2-1",
                    "interviewId": interview_id,
                    "questionId": "additional_context",
                    "answer": {"text": "clear and playable"},
                },
            )

            resumed = client.post("/interviews", json={"caseId": "case-f2-1"})

        assert final_step.status_code == 200
        assert final_step.json()["status"] == "completed"
        assert resumed.status_code == 200
        assert resumed.json()["status"] == "completed"
        assert resumed.json()["interviewId"] == interview_id
        assert resumed.json()["nextQuestion"] is None
    finally:
        app.dependency_overrides.clear()
        transaction.rollback()
        session.close()
        connection.close()
