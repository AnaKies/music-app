"""
Contract tests for GET /cases/{id} endpoint (F1 Case Entry feature).

These tests verify that case retrieval works correctly at the API level,
including response contract compliance, not-found handling, and constraint population.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.database import Base, get_db
from backend.domain.cases.models import TranspositionCase
from backend.api.schemas.cases import CaseStatus
from backend.main import app


# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_cases_read.db"
test_engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="function", autouse=True)
def setup_db():
    """Create fresh database for each test."""
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


def override_get_db():
    """Override database dependency for testing."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="function")
def client():
    """Create test client with overridden database dependency."""
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


class TestGetCaseContract:
    """Contract tests for GET /cases/{id} endpoint."""

    def test_get_case_success(self, client):
        """Verify successful case retrieval with all required fields."""
        # Arrange: Create test case in database
        db = TestingSessionLocal()
        test_case = TranspositionCase(
            id="test-case-123",
            status=CaseStatus.READY_FOR_UPLOAD,
            instrument_identity="trumpet-bb",
            user_id=None,
            highest_playable_tone="C6",
            lowest_playable_tone="F#3",
            restricted_tones=["C#7"],
            difficult_keys=["F# major"],
        )
        db.add(test_case)
        db.commit()
        db.close()
        
        # Act: Call the endpoint
        response = client.get("/cases/test-case-123")
        
        # Assert: Response structure and content
        assert response.status_code == 200
        data = response.json()
        
        # Verify core fields
        assert data["id"] == "test-case-123"
        assert data["status"] == "ready_for_upload"
        assert data["instrumentIdentity"] == "trumpet-bb"
        assert data["userId"] is None
        assert data["scoreCount"] == 0
        assert "createdAt" in data
        assert "updatedAt" in data
        
        # Verify constraints
        assert "constraints" in data
        constraints = data["constraints"]
        assert constraints["highest_playable_tone"] == "C6"
        assert constraints["lowest_playable_tone"] == "F#3"
        assert constraints["restricted_tones"] == ["C#7"]
        assert constraints["difficult_keys"] == ["F# major"]

    def test_get_case_not_found(self, client):
        """Verify 404 response for non-existent case ID."""
        response = client.get("/cases/non-existent-id")
        
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "non-existent-id" in data["detail"]

    def test_get_case_with_all_constraints(self, client):
        """Verify case retrieval with all constraint fields populated."""
        # Arrange
        db = TestingSessionLocal()
        test_case = TranspositionCase(
            id="test-case-full",
            status=CaseStatus.INTERVIEW_IN_PROGRESS,
            instrument_identity="alto-sax-eb",
            user_id="user-456",
            highest_playable_tone="C7",
            lowest_playable_tone="D3",
            restricted_tones=["C#7", "D7"],
            restricted_registers=["altissimo"],
            difficult_keys=["C# minor", "F# major"],
            preferred_keys=["Eb major", "Bb major"],
            comfort_range_min="G3",
            comfort_range_max="G6",
        )
        db.add(test_case)
        db.commit()
        db.close()
        
        # Act
        response = client.get("/cases/test-case-full")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        
        assert data["userId"] == "user-456"
        constraints = data["constraints"]
        assert constraints["highest_playable_tone"] == "C7"
        assert constraints["lowest_playable_tone"] == "D3"
        assert len(constraints["restricted_tones"]) == 2
        assert len(constraints["restricted_registers"]) == 1
        assert len(constraints["difficult_keys"]) == 2
        assert len(constraints["preferred_keys"]) == 2
        assert constraints["comfort_range_min"] == "G3"
        assert constraints["comfort_range_max"] == "G6"

    def test_get_case_with_empty_constraints(self, client):
        """Verify case retrieval returns empty lists for null constraint arrays."""
        # Arrange: Case with no constraints
        db = TestingSessionLocal()
        test_case = TranspositionCase(
            id="test-case-empty",
            status=CaseStatus.NEW,
            instrument_identity="flute",
        )
        db.add(test_case)
        db.commit()
        db.close()
        
        # Act
        response = client.get("/cases/test-case-empty")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        
        constraints = data["constraints"]
        assert constraints["restricted_tones"] == []
        assert constraints["restricted_registers"] == []
        assert constraints["difficult_keys"] == []
        assert constraints["preferred_keys"] == []
        assert constraints["highest_playable_tone"] is None
        assert constraints["lowest_playable_tone"] is None

    def test_get_case_timestamps_are_iso8601(self, client):
        """Verify timestamps are in ISO 8601 format."""
        # Arrange
        db = TestingSessionLocal()
        test_case = TranspositionCase(
            id="test-case-time",
            status=CaseStatus.COMPLETED,
            instrument_identity="clarinet-bb",
        )
        db.add(test_case)
        db.commit()
        db.close()
        
        # Act
        response = client.get("/cases/test-case-time")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        
        created_at = data["createdAt"]
        updated_at = data["updatedAt"]
        
        # ISO 8601 format check
        assert "T" in created_at
        assert "T" in updated_at

    def test_get_case_status_enum_values(self, client):
        """Verify all status enum values are correctly serialized."""
        test_statuses = [
            CaseStatus.NEW,
            CaseStatus.INTERVIEW_IN_PROGRESS,
            CaseStatus.READY_FOR_UPLOAD,
            CaseStatus.RECOMMENDATION_READY,
            CaseStatus.COMPLETED,
            CaseStatus.ARCHIVED,
        ]
        
        for i, test_status in enumerate(test_statuses):
            # Arrange
            db = TestingSessionLocal()
            test_case = TranspositionCase(
                id=f"test-case-status-{i}",
                status=test_status,
                instrument_identity="violin",
            )
            db.add(test_case)
            db.commit()
            db.close()
            
            # Act
            response = client.get(f"/cases/test-case-status-{i}")
            
            # Assert
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == test_status.value


class TestGetCaseEdgeCases:
    """Edge case tests for GET /cases/{id}."""

    def test_get_case_with_special_characters_in_id(self, client):
        """Verify case retrieval works with special characters in ID."""
        # Arrange
        db = TestingSessionLocal()
        test_case = TranspositionCase(
            id="case-with-dashes-and-123",
            status=CaseStatus.NEW,
            instrument_identity="cello",
        )
        db.add(test_case)
        db.commit()
        db.close()
        
        # Act
        response = client.get("/cases/case-with-dashes-and-123")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "case-with-dashes-and-123"

    def test_get_case_response_is_json(self, client):
        """Verify response content-type is JSON."""
        # Arrange
        db = TestingSessionLocal()
        test_case = TranspositionCase(
            id="test-case-json",
            status=CaseStatus.NEW,
            instrument_identity="horn-f",
        )
        db.add(test_case)
        db.commit()
        db.close()
        
        # Act
        response = client.get("/cases/test-case-json")
        
        # Assert
        assert response.status_code == 200
        assert "application/json" in response.headers["content-type"]

    def test_get_case_multiple_sequential_requests(self, client):
        """Verify multiple sequential GET requests return consistent data."""
        # Arrange
        db = TestingSessionLocal()
        test_case = TranspositionCase(
            id="test-case-multi",
            status=CaseStatus.READY_FOR_UPLOAD,
            instrument_identity="euphonium",
            highest_playable_tone="Bb5",
        )
        db.add(test_case)
        db.commit()
        db.close()
        
        # Act: Multiple requests
        responses = []
        for _ in range(3):
            response = client.get("/cases/test-case-multi")
            responses.append(response.json())
        
        # Assert: All responses are identical
        assert all(r == responses[0] for r in responses)
        assert responses[0]["status"] == "ready_for_upload"
        assert responses[0]["constraints"]["highest_playable_tone"] == "Bb5"
