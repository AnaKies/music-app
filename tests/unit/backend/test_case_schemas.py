"""
Contract tests for case-related API schemas.

These tests protect the case creation and read contracts before multiple
developers build against them. They verify schema structure, serialization,
and validation behavior.
"""
from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from backend.api.schemas.cases import (
    CaseStatus,
    CaseConstraints,
    CaseSummary,
    CaseDetail,
    CaseCreateRequest,
    CaseCreateResponse,
    ExistingCaseAction,
)


class TestCaseStatus:
    """Tests for CaseStatus enum values."""

    def test_all_required_status_values_exist(self):
        """Verify all architecture-required status values are present."""
        assert CaseStatus.NEW.value == "new"
        assert CaseStatus.INTERVIEW_IN_PROGRESS.value == "interview_in_progress"
        assert CaseStatus.READY_FOR_UPLOAD.value == "ready_for_upload"
        assert CaseStatus.RECOMMENDATION_READY.value == "recommendation_ready"
        assert CaseStatus.COMPLETED.value == "completed"
        assert CaseStatus.ARCHIVED.value == "archived"

    def test_case_status_is_string_enum(self):
        """Verify CaseStatus behaves as a string enum for JSON serialization."""
        assert isinstance(CaseStatus.NEW.value, str)
        assert CaseStatus.NEW == "new"
        assert CaseStatus.READY_FOR_UPLOAD == "ready_for_upload"


class TestCaseConstraints:
    """Tests for CaseConstraints schema."""

    def test_empty_constraints_valid(self):
        """Verify empty constraints are valid (all fields optional)."""
        constraints = CaseConstraints()
        assert constraints.highest_playable_tone is None
        assert constraints.lowest_playable_tone is None
        assert constraints.restricted_tones == []
        assert constraints.restricted_registers == []
        assert constraints.difficult_keys == []
        assert constraints.preferred_keys == []
        assert constraints.comfort_range_min is None
        assert constraints.comfort_range_max is None

    def test_constraints_with_all_fields(self):
        """Verify constraints accept all constraint types."""
        constraints = CaseConstraints(
            highest_playable_tone="C6",
            lowest_playable_tone="G3",
            restricted_tones=["C#7", "D7"],
            restricted_registers=["altissimo"],
            difficult_keys=["F# major", "C# minor"],
            preferred_keys=["C major", "G major", "D major"],
            comfort_range_min="A3",
            comfort_range_max="G5",
        )
        assert constraints.highest_playable_tone == "C6"
        assert constraints.lowest_playable_tone == "G3"
        assert len(constraints.restricted_tones) == 2
        assert len(constraints.preferred_keys) == 3

    def test_constraints_serialization(self):
        """Verify constraints can be serialized to dict."""
        constraints = CaseConstraints(
            highest_playable_tone="C6",
            difficult_keys=["F# major"],
        )
        data = constraints.model_dump()
        assert data["highest_playable_tone"] == "C6"
        assert data["difficult_keys"] == ["F# major"]
        assert data["restricted_tones"] == []


class TestCaseSummary:
    """Tests for CaseSummary schema."""

    @pytest.fixture
    def sample_timestamp(self):
        return datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc)

    def test_minimal_case_summary_required_fields_only(self, sample_timestamp):
        """Verify CaseSummary with only required fields."""
        summary = CaseSummary(
            id="case-123",
            status=CaseStatus.NEW,
            instrumentIdentity="trumpet-bb",
            createdAt=sample_timestamp,
            updatedAt=sample_timestamp,
        )
        assert summary.id == "case-123"
        assert summary.status == CaseStatus.NEW
        assert summary.instrumentIdentity == "trumpet-bb"
        assert summary.scoreCount == 0

    def test_case_summary_with_optional_fields(self, sample_timestamp):
        """Verify CaseSummary accepts additive non-user fields."""
        summary = CaseSummary(
            id="case-456",
            status=CaseStatus.READY_FOR_UPLOAD,
            instrumentIdentity="alto-sax-eb",
            scoreCount=5,
            createdAt=sample_timestamp,
            updatedAt=sample_timestamp,
        )
        assert summary.scoreCount == 5

    def test_case_summary_serialization(self, sample_timestamp):
        """Verify CaseSummary serializes to dict correctly."""
        summary = CaseSummary(
            id="case-789",
            status=CaseStatus.RECOMMENDATION_READY,
            instrumentIdentity="trombone",
            createdAt=sample_timestamp,
            updatedAt=sample_timestamp,
        )
        data = summary.model_dump()
        assert data["id"] == "case-789"
        assert data["status"] == "recommendation_ready"
        assert data["instrumentIdentity"] == "trombone"
        assert "scoreCount" in data

    def test_case_summary_from_attributes(self, sample_timestamp):
        """Verify CaseSummary can be constructed from ORM-like attributes."""
        summary = CaseSummary.model_validate(
            {
                "id": "case-orm-1",
                "status": "interview_in_progress",
                "instrumentIdentity": "flute",
                "scoreCount": 0,
                "createdAt": sample_timestamp,
                "updatedAt": sample_timestamp,
            }
        )
        assert summary.id == "case-orm-1"
        assert summary.status == CaseStatus.INTERVIEW_IN_PROGRESS


class TestCaseDetail:
    """Tests for CaseDetail schema."""

    @pytest.fixture
    def sample_timestamp(self):
        return datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc)

    def test_case_detail_includes_constraints(self, sample_timestamp):
        """Verify CaseDetail includes all CaseSummary fields plus constraints."""
        detail = CaseDetail(
            id="case-detail-1",
            status=CaseStatus.READY_FOR_UPLOAD,
            instrumentIdentity="clarinet-bb",
            createdAt=sample_timestamp,
            updatedAt=sample_timestamp,
            constraints=CaseConstraints(
                highest_playable_tone="C7",
                lowest_playable_tone="E3",
            ),
        )
        assert detail.id == "case-detail-1"
        assert detail.constraints.highest_playable_tone == "C7"
        assert detail.constraints.lowest_playable_tone == "E3"

    def test_case_detail_default_constraints(self, sample_timestamp):
        """Verify CaseDetail creates empty constraints by default."""
        detail = CaseDetail(
            id="case-detail-2",
            status=CaseStatus.NEW,
            instrumentIdentity="violin",
            createdAt=sample_timestamp,
            updatedAt=sample_timestamp,
        )
        assert detail.constraints is not None
        assert detail.constraints.restricted_tones == []
        assert detail.constraints.difficult_keys == []

    def test_case_detail_serialization(self, sample_timestamp):
        """Verify CaseDetail serializes constraints correctly."""
        detail = CaseDetail(
            id="case-detail-3",
            status=CaseStatus.COMPLETED,
            instrumentIdentity="cello",
            createdAt=sample_timestamp,
            updatedAt=sample_timestamp,
            constraints=CaseConstraints(
                comfort_range_min="C2",
                comfort_range_max="C5",
                preferred_keys=["D major", "G major"],
            ),
        )
        data = detail.model_dump()
        assert "constraints" in data
        assert data["constraints"]["comfort_range_min"] == "C2"
        assert len(data["constraints"]["preferred_keys"]) == 2


class TestCaseCreateRequest:
    """Tests for CaseCreateRequest schema."""

    def test_valid_create_request(self):
        """Verify valid create request passes validation."""
        request = CaseCreateRequest(instrument_identity="trumpet-bb")
        assert request.instrument_identity == "trumpet-bb"
        assert request.existing_case_action is None
        assert request.existing_case_id is None

    def test_create_request_with_reset_action(self):
        """Verify create request with reset action."""
        request = CaseCreateRequest(
            instrument_identity="alto-sax-eb",
            existing_case_action=ExistingCaseAction.RESET,
            existing_case_id="case-existing-1",
        )
        assert request.existing_case_action == ExistingCaseAction.RESET
        assert request.existing_case_id == "case-existing-1"

    def test_create_request_rejects_empty_instrument_identity(self):
        """Verify empty instrument identity is rejected."""
        with pytest.raises(ValidationError):
            CaseCreateRequest(instrument_identity="")

    def test_create_request_rejects_missing_instrument_identity(self):
        """Verify missing instrument identity is rejected."""
        with pytest.raises(ValidationError):
            CaseCreateRequest()


class TestCaseCreateResponse:
    """Tests for CaseCreateResponse schema."""

    @pytest.fixture
    def sample_timestamp(self):
        return datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc)

    def test_create_response_structure(self, sample_timestamp):
        """Verify create response has required structure."""
        summary = CaseSummary(
            id="case-new-1",
            status=CaseStatus.NEW,
            instrumentIdentity="horn",
            createdAt=sample_timestamp,
            updatedAt=sample_timestamp,
        )
        response = CaseCreateResponse(
            transpositionCaseId="case-new-1",
            status=CaseStatus.NEW,
            caseSummary=summary,
        )
        assert response.transpositionCaseId == "case-new-1"
        assert response.status == CaseStatus.NEW
        assert response.caseSummary.instrumentIdentity == "horn"

    def test_create_response_serialization(self, sample_timestamp):
        """Verify create response serializes correctly."""
        summary = CaseSummary(
            id="case-new-2",
            status=CaseStatus.INTERVIEW_IN_PROGRESS,
            instrumentIdentity="euphonium",
            createdAt=sample_timestamp,
            updatedAt=sample_timestamp,
        )
        response = CaseCreateResponse(
            transpositionCaseId="case-new-2",
            status=CaseStatus.INTERVIEW_IN_PROGRESS,
            caseSummary=summary,
        )
        data = response.model_dump()
        assert data["transpositionCaseId"] == "case-new-2"
        assert "caseSummary" in data
        assert data["caseSummary"]["status"] == "interview_in_progress"


class TestSchemaContractStability:
    """Tests ensuring schema contract stability for frontend consumption."""

    @pytest.fixture
    def sample_timestamp(self):
        return datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc)

    def test_case_summary_field_order_independent(self, sample_timestamp):
        """Verify CaseSummary accepts fields in any order."""
        summary = CaseSummary.model_validate(
            {
                "updatedAt": sample_timestamp,
                "instrumentIdentity": "oboe",
                "createdAt": sample_timestamp,
                "status": "new",
                "id": "case-order-1",
            }
        )
        assert summary.id == "case-order-1"
        assert summary.instrumentIdentity == "oboe"

    def test_case_status_string_comparison(self, sample_timestamp):
        """Verify CaseStatus works in string comparison for frontend filtering."""
        summary = CaseSummary(
            id="case-filter-1",
            status=CaseStatus.READY_FOR_UPLOAD,
            instrumentIdentity="bassoon",
            createdAt=sample_timestamp,
            updatedAt=sample_timestamp,
        )
        # Frontend may compare status as string
        assert summary.status == "ready_for_upload"
        assert summary.status.value == "ready_for_upload"

    def test_all_case_status_values_serializable(self, sample_timestamp):
        """Verify all status values serialize to expected strings."""
        for status in CaseStatus:
            summary = CaseSummary(
                id=f"case-status-{status.value}",
                status=status,
                instrumentIdentity="test",
                createdAt=sample_timestamp,
                updatedAt=sample_timestamp,
            )
            data = summary.model_dump()
            assert data["status"] == status.value
