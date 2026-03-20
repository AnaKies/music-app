"""
Contract and flow tests for interview endpoints.

These tests cover the F2 MVP path for starting, continuing, and resuming a
structured interview session.
"""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.database import Base, engine, get_db
from backend.domain.cases.models import TranspositionCase
from backend.domain.interviews.models import InterviewSession  # noqa: F401
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
        assert payload["collectedAnswers"] == []
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
            assert instrument.json()["collectedAnswers"][0]["value"]["selectedOption"] == "trumpet-bb"

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


def test_interview_answers_update_the_case_identity_for_later_case_lists():
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
                    "answer": {"selectedOption": "alto-sax-eb"},
                },
            )

        assert instrument.status_code == 200
        persisted_case = session.query(TranspositionCase).filter(TranspositionCase.id == "case-f2-1").first()
        assert persisted_case is not None
        assert persisted_case.instrument_identity == "alto-sax-eb"
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
        assert len(resumed.json()["collectedAnswers"]) == 4
    finally:
        app.dependency_overrides.clear()
        transaction.rollback()
        session.close()
        connection.close()


def test_completed_interview_marks_case_ready_for_upload():
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
            case_detail = client.get("/cases/case-f2-1")

        assert final_step.status_code == 200
        assert final_step.json()["status"] == "completed"
        assert final_step.json()["derivedCaseSummary"]["caseStatus"] == "ready_for_upload"
        assert case_detail.status_code == 200
        assert case_detail.json()["status"] == "ready_for_upload"
        assert case_detail.json()["constraints"]["comfort_range_min"] == "G3"
        assert case_detail.json()["constraints"]["comfort_range_max"] == "D5"
    finally:
        app.dependency_overrides.clear()
        transaction.rollback()
        session.close()
        connection.close()


def test_placeholder_range_values_do_not_trigger_ready_for_upload():
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
                    "answer": {"selectedOptions": []},
                },
            )
            client.post(
                "/interviews",
                json={
                    "caseId": "case-f2-1",
                    "interviewId": interview_id,
                    "questionId": "comfort_range",
                    "answer": {"noteRange": {"min": "no data", "max": "no data"}},
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
            case_detail = client.get("/cases/case-f2-1")

        assert final_step.status_code == 200
        assert final_step.json()["status"] == "completed"
        assert final_step.json()["derivedCaseSummary"]["caseStatus"] == "interview_in_progress"
        assert case_detail.status_code == 200
        assert case_detail.json()["status"] == "interview_in_progress"
        assert case_detail.json()["constraints"]["comfort_range_min"] == "no data"
        assert case_detail.json()["constraints"]["comfort_range_max"] == "no data"
    finally:
        app.dependency_overrides.clear()
        transaction.rollback()
        session.close()
        connection.close()


def test_short_negation_range_values_do_not_trigger_ready_for_upload():
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
                    "answer": {"selectedOption": "flute"},
                },
            )
            client.post(
                "/interviews",
                json={
                    "caseId": "case-f2-1",
                    "interviewId": interview_id,
                    "questionId": "challenge_areas",
                    "answer": {"selectedOptions": []},
                },
            )
            client.post(
                "/interviews",
                json={
                    "caseId": "case-f2-1",
                    "interviewId": interview_id,
                    "questionId": "comfort_range",
                    "answer": {"noteRange": {"min": "no", "max": "no"}},
                },
            )
            final_step = client.post(
                "/interviews",
                json={
                    "caseId": "case-f2-1",
                    "interviewId": interview_id,
                    "questionId": "additional_context",
                    "answer": {"text": "no"},
                },
            )
            case_detail = client.get("/cases/case-f2-1")

        assert final_step.status_code == 200
        assert final_step.json()["status"] == "completed"
        assert final_step.json()["derivedCaseSummary"]["caseStatus"] == "interview_in_progress"
        assert case_detail.status_code == 200
        assert case_detail.json()["status"] == "interview_in_progress"
    finally:
        app.dependency_overrides.clear()
        transaction.rollback()
        session.close()
        connection.close()


def test_note_range_answers_are_normalized_to_low_then_high_for_later_features():
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
                    "answer": {"selectedOption": "flute"},
                },
            )
            client.post(
                "/interviews",
                json={
                    "caseId": "case-f2-1",
                    "interviewId": interview_id,
                    "questionId": "challenge_areas",
                    "answer": {"selectedOptions": []},
                },
            )
            comfort = client.post(
                "/interviews",
                json={
                    "caseId": "case-f2-1",
                    "interviewId": interview_id,
                    "questionId": "comfort_range",
                    "answer": {"noteRange": {"min": "G2", "max": "D2"}},
                },
            )

        assert comfort.status_code == 200
        assert comfort.json()["derivedCaseSummary"]["comfortRangeMin"] == "D2"
        assert comfort.json()["derivedCaseSummary"]["comfortRangeMax"] == "G2"
        persisted_case = session.query(TranspositionCase).filter(TranspositionCase.id == "case-f2-1").first()
        assert persisted_case is not None
        assert persisted_case.comfort_range_min == "D2"
        assert persisted_case.comfort_range_max == "G2"
    finally:
        app.dependency_overrides.clear()
        transaction.rollback()
        session.close()
        connection.close()


def test_note_range_rejects_free_form_values_that_cannot_drive_transformation():
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
                    "answer": {"selectedOption": "flute"},
                },
            )
            client.post(
                "/interviews",
                json={
                    "caseId": "case-f2-1",
                    "interviewId": interview_id,
                    "questionId": "challenge_areas",
                    "answer": {"selectedOptions": []},
                },
            )
            comfort = client.post(
                "/interviews",
                json={
                    "caseId": "case-f2-1",
                    "interviewId": interview_id,
                    "questionId": "comfort_range",
                    "answer": {"noteRange": {"min": "middle c", "max": "D5"}},
                },
            )

        assert comfort.status_code == 422
        assert comfort.json() == {
            "detail": "noteRange must use supported note names like G3 to D5.",
        }
    finally:
        app.dependency_overrides.clear()
        transaction.rollback()
        session.close()
        connection.close()


def test_low_confidence_follow_up_does_not_finalize_case_until_clarification_is_complete():
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
                    "answer": {"selectedOptions": ["high_register", "difficult_keys"]},
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
            awaiting_follow_up = client.post(
                "/interviews",
                json={
                    "caseId": "case-f2-1",
                    "interviewId": interview_id,
                    "questionId": "additional_context",
                    "answer": {"text": "not sure about the upper register"},
                },
            )
            case_during_follow_up = client.get("/cases/case-f2-1")
            clarified = client.post(
                "/interviews",
                json={
                    "caseId": "case-f2-1",
                    "interviewId": interview_id,
                    "questionId": "additional_context_follow_up",
                    "answer": {"text": "avoid assuming anything above written D5"},
                },
            )
            case_after_clarification = client.get("/cases/case-f2-1")

        assert awaiting_follow_up.status_code == 200
        assert awaiting_follow_up.json()["status"] == "awaiting_follow_up"
        assert awaiting_follow_up.json()["derivedCaseSummary"]["caseStatus"] == "interview_in_progress"
        assert case_during_follow_up.status_code == 200
        assert case_during_follow_up.json()["status"] == "interview_in_progress"
        assert case_during_follow_up.json()["constraints"]["comfort_range_min"] == "G3"
        assert case_during_follow_up.json()["constraints"]["comfort_range_max"] == "D5"

        assert clarified.status_code == 200
        assert clarified.json()["status"] == "completed"
        assert clarified.json()["derivedCaseSummary"]["caseStatus"] == "ready_for_upload"
        assert case_after_clarification.status_code == 200
        assert case_after_clarification.json()["status"] == "ready_for_upload"
        assert case_after_clarification.json()["constraints"]["difficult_keys"] == ["needs_clarification"]
        assert case_after_clarification.json()["constraints"]["restricted_registers"] == ["high_register"]
    finally:
        app.dependency_overrides.clear()
        transaction.rollback()
        session.close()
        connection.close()


def test_resuming_an_unfinished_follow_up_session_resets_case_back_to_interview_in_progress():
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
            client.post(
                "/interviews",
                json={
                    "caseId": "case-f2-1",
                    "interviewId": interview_id,
                    "questionId": "additional_context",
                    "answer": {"text": "not sure about the upper register"},
                },
            )

            persisted_case = session.query(TranspositionCase).filter(TranspositionCase.id == "case-f2-1").first()
            assert persisted_case is not None
            persisted_case.status = "ready_for_upload"
            session.add(persisted_case)
            session.commit()

            resumed = client.post("/interviews", json={"caseId": "case-f2-1"})
            case_detail = client.get("/cases/case-f2-1")

        assert resumed.status_code == 200
        assert resumed.json()["status"] == "awaiting_follow_up"
        assert resumed.json()["derivedCaseSummary"]["caseStatus"] == "interview_in_progress"
        assert case_detail.status_code == 200
        assert case_detail.json()["status"] == "interview_in_progress"
    finally:
        app.dependency_overrides.clear()
        transaction.rollback()
        session.close()
        connection.close()


def test_interview_updates_only_the_target_case_when_multiple_cases_exist():
    _reset_tables()

    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)
    _seed_case(session, case_id="case-f3-1")
    _seed_case(session, case_id="case-f3-2")
    app.dependency_overrides[get_db] = _override_get_db(session)

    try:
        with TestClient(app) as client:
            start = client.post("/interviews", json={"caseId": "case-f3-1"})
            interview_id = start.json()["interviewId"]

            client.post(
                "/interviews",
                json={
                    "caseId": "case-f3-1",
                    "interviewId": interview_id,
                    "questionId": "instrument_identity",
                    "answer": {"selectedOption": "alto-sax-eb"},
                },
            )
            client.post(
                "/interviews",
                json={
                    "caseId": "case-f3-1",
                    "interviewId": interview_id,
                    "questionId": "challenge_areas",
                    "answer": {"selectedOptions": ["low_register"]},
                },
            )
            client.post(
                "/interviews",
                json={
                    "caseId": "case-f3-1",
                    "interviewId": interview_id,
                    "questionId": "comfort_range",
                    "answer": {"noteRange": {"min": "C3", "max": "A5"}},
                },
            )
            client.post(
                "/interviews",
                json={
                    "caseId": "case-f3-1",
                    "interviewId": interview_id,
                    "questionId": "additional_context",
                    "answer": {"text": "clear and playable"},
                },
            )

            updated_case = client.get("/cases/case-f3-1")
            untouched_case = client.get("/cases/case-f3-2")

        assert updated_case.status_code == 200
        assert updated_case.json()["instrumentIdentity"] == "alto-sax-eb"
        assert updated_case.json()["status"] == "ready_for_upload"
        assert updated_case.json()["constraints"]["restricted_registers"] == ["low_register"]
        assert updated_case.json()["constraints"]["comfort_range_min"] == "C3"
        assert updated_case.json()["constraints"]["comfort_range_max"] == "A5"

        assert untouched_case.status_code == 200
        assert untouched_case.json()["instrumentIdentity"] == "placeholder"
        assert untouched_case.json()["status"] == "new"
        assert untouched_case.json()["constraints"]["restricted_registers"] == []
        assert untouched_case.json()["constraints"]["comfort_range_min"] is None
        assert untouched_case.json()["constraints"]["comfort_range_max"] is None
    finally:
        app.dependency_overrides.clear()
        transaction.rollback()
        session.close()
        connection.close()
