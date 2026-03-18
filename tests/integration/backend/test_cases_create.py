"""
Contract tests for POST /cases.

Test-1 protects the approved case-creation contract before more frontend and
backend tasks build on top of it.
"""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.main import app
from backend.database import Base, engine, get_db
from backend.domain.cases.models import TranspositionCase


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


def test_post_cases_creates_case_and_returns_documented_contract():
    _reset_tables()

    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)

    app.dependency_overrides[get_db] = _override_get_db(session)

    try:
        with TestClient(app) as client:
            response = client.post(
                "/cases",
                json={"instrument_identity": "trumpet-bb"},
            )

        assert response.status_code == 201

        payload = response.json()
        assert "transpositionCaseId" in payload
        assert payload["status"] == "new"
        assert "caseSummary" in payload

        summary = payload["caseSummary"]
        assert summary["id"] == payload["transpositionCaseId"]
        assert summary["status"] == "new"
        assert summary["instrumentIdentity"] == "trumpet-bb"
        assert summary["scoreCount"] == 0
        assert "createdAt" in summary
        assert "updatedAt" in summary
        assert "userId" not in summary

        persisted_case = (
            session.query(TranspositionCase)
            .filter(TranspositionCase.id == payload["transpositionCaseId"])
            .first()
        )
        assert persisted_case is not None
        assert persisted_case.status.value == "new"
        assert persisted_case.instrument_identity == "trumpet-bb"
    finally:
        app.dependency_overrides.clear()
        transaction.rollback()
        session.close()
        connection.close()


def test_post_cases_rejects_invalid_payloads():
    _reset_tables()

    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)

    app.dependency_overrides[get_db] = _override_get_db(session)

    try:
        with TestClient(app) as client:
            missing_instrument = client.post("/cases", json={})
            empty_instrument = client.post("/cases", json={"instrument_identity": ""})
            reset_without_id = client.post(
                "/cases",
                json={
                    "instrument_identity": "clarinet-bb",
                    "existing_case_action": "reset",
                },
            )

        assert missing_instrument.status_code == 422
        assert empty_instrument.status_code == 422
        assert reset_without_id.status_code == 409
        assert "detail" in reset_without_id.json()
    finally:
        app.dependency_overrides.clear()
        transaction.rollback()
        session.close()
        connection.close()
