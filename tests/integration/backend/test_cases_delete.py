"""
Contract tests for DELETE /cases/{id}.

This provisional MVP cleanup route exists so end-to-end and manual testing do
not get blocked by an ever-growing list of stale cases.
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


def test_delete_case_removes_existing_case():
    _reset_tables()

    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)
    session.add(
        TranspositionCase(
            id="case-to-delete",
            status="new",
            instrument_identity="placeholder",
        )
    )
    session.commit()
    app.dependency_overrides[get_db] = _override_get_db(session)

    try:
        with TestClient(app) as client:
            response = client.delete("/cases/case-to-delete")
            missing = client.get("/cases/case-to-delete")

        assert response.status_code == 204
        assert response.content == b""
        assert missing.status_code == 404
        assert session.query(TranspositionCase).filter(TranspositionCase.id == "case-to-delete").first() is None
    finally:
        app.dependency_overrides.clear()
        transaction.rollback()
        session.close()
        connection.close()


def test_delete_case_returns_structured_404_for_unknown_case():
    _reset_tables()

    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)
    app.dependency_overrides[get_db] = _override_get_db(session)

    try:
        with TestClient(app) as client:
            response = client.delete("/cases/missing-case")

        assert response.status_code == 404
        assert response.json() == {
            "detail": "Case with id missing-case not found.",
        }
    finally:
        app.dependency_overrides.clear()
        transaction.rollback()
        session.close()
        connection.close()
