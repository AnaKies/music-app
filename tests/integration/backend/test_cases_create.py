"""
Contract tests for POST /cases endpoint (F1 Case Entry feature).

These tests verify that case creation works correctly at the API level,
including validation, persistence, and response contract compliance.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.database import engine, get_db
from backend.domain.cases.models import TranspositionCase, Base


# Create test database tables
@pytest.fixture(scope="module", autouse=True)
def setup_test_db():
    # Drop all tables first to ensure clean state
    Base.metadata.drop_all(bind=engine)
    # Then create fresh tables with current schema
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


# Override database dependency for testing
@pytest.fixture
def db_session():
    """Create a fresh database session for each test."""
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)
    
    # Override get_db dependency
    def override_get_db():
        try:
            yield session
        finally:
            pass
    
    from backend.api.routes import cases
    cases.get_db = override_get_db
    
    yield session
    
    transaction.rollback()
    session.close()
    connection.close()


@pytest.fixture
def client(db_session):
    """Create test client with database override."""
    from fastapi.testclient import TestClient
    from backend.main import app
    
    with TestClient(app) as test_client:
        yield test_client


class TestPostCasesContract:
    """Contract tests for POST /cases endpoint."""

    def test_create_case_success_minimal_request(self, client, db_session):
        """Verify successful case creation with minimal valid request."""
        response = client.post(
            "/cases",
            json={"instrument_identity": "trumpet-bb"},
        )
        
        assert response.status_code == 201
        data = response.json()
        
        # Verify response structure
        assert "transpositionCaseId" in data
        assert data["status"] == "new"
        assert "caseSummary" in data
        
        # Verify case summary structure
        summary = data["caseSummary"]
        assert summary["id"] == data["transpositionCaseId"]
        assert summary["status"] == "new"
        assert summary["instrumentIdentity"] == "trumpet-bb"
        assert summary["userId"] is None
        assert summary["scoreCount"] == 0
        assert "createdAt" in summary
        assert "updatedAt" in summary

    def test_create_case_persists_to_database(self, client, db_session):
        """Verify case is actually persisted to database."""
        response = client.post(
            "/cases",
            json={"instrument_identity": "alto-sax-eb"},
        )
        
        assert response.status_code == 201
        data = response.json()
        case_id = data["transpositionCaseId"]
        
        # Verify persistence
        persisted_case = db_session.query(TranspositionCase).filter(
            TranspositionCase.id == case_id
        ).first()
        
        assert persisted_case is not None
        assert persisted_case.status.value == "new"
        assert persisted_case.user_id is None

    def test_create_case_with_various_instruments(self, client, db_session):
        """Verify case creation works for different instrument identities."""
        instruments = [
            "flute",
            "clarinet-bb",
            "trombone",
            "violin",
            "cello",
            "horn-f",
        ]
        
        for instrument in instruments:
            response = client.post(
                "/cases",
                json={"instrument_identity": instrument},
            )
            assert response.status_code == 201
            data = response.json()
            assert data["caseSummary"]["instrumentIdentity"] == instrument

    def test_create_case_rejects_empty_instrument_identity(self, client):
        """Verify empty instrument identity is rejected with 422."""
        response = client.post(
            "/cases",
            json={"instrument_identity": ""},
        )
        
        assert response.status_code == 422

    def test_create_case_rejects_missing_instrument_identity(self, client):
        """Verify missing instrument identity is rejected with 422."""
        response = client.post(
            "/cases",
            json={},
        )
        
        assert response.status_code == 422

    def test_create_case_rejects_action_without_id(self, client):
        """Verify action without case ID is rejected with 409."""
        response = client.post(
            "/cases",
            json={
                "instrument_identity": "trumpet-bb",
                "existing_case_action": "reset",
            },
        )
        
        assert response.status_code == 409
        data = response.json()
        assert "detail" in data

    def test_create_case_accepts_action_with_id(self, client, db_session):
        """Verify action with case ID is accepted (will be implemented in F13)."""
        # First create a case
        create_response = client.post(
            "/cases",
            json={"instrument_identity": "clarinet-bb"},
        )
        case_id = create_response.json()["transpositionCaseId"]
        
        # Try to reset it (this may fail gracefully in MVP)
        response = client.post(
            "/cases",
            json={
                "instrument_identity": "clarinet-bb",
                "existing_case_action": "reset",
                "existing_case_id": case_id,
            },
        )
        
        # Should not fail validation - actual behavior depends on F13 implementation
        assert response.status_code in [201, 400, 404]

    def test_create_case_response_is_serializable(self, client, db_session):
        """Verify response can be serialized to JSON without errors."""
        response = client.post(
            "/cases",
            json={"instrument_identity": "euphonium"},
        )
        
        assert response.status_code == 201
        # If we got here, JSON serialization worked
        data = response.json()
        assert isinstance(data, dict)

    def test_create_case_timestamps_are_iso8601(self, client, db_session):
        """Verify timestamps are in ISO 8601 format."""
        response = client.post(
            "/cases",
            json={"instrument_identity": "oboe"},
        )
        
        assert response.status_code == 201
        data = response.json()
        
        # ISO 8601 format check (basic)
        created_at = data["caseSummary"]["createdAt"]
        updated_at = data["caseSummary"]["updatedAt"]
        
        assert "T" in created_at  # ISO 8601 date-time separator
        assert "T" in updated_at


class TestPostCasesIdempotency:
    """Tests for case creation behavior under repeated calls."""

    def test_multiple_sequential_creates(self, client, db_session):
        """Verify multiple sequential creates all succeed."""
        case_ids = []
        
        for i in range(5):
            response = client.post(
                "/cases",
                json={"instrument_identity": f"trumpet-{i}"},
            )
            assert response.status_code == 201
            case_id = response.json()["transpositionCaseId"]
            case_ids.append(case_id)
        
        # All IDs should be unique
        assert len(set(case_ids)) == 5
        
        # All should be persisted
        count = db_session.query(TranspositionCase).count()
        assert count >= 5
