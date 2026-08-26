"""Integration tests for Phase 5C AI Narrative FastAPI endpoint."""

from datetime import date

from fastapi.testclient import TestClient

from apps.analytics.investigation.models import (
    ContributionAnalysis,
    Contributor,
    InvestigationRequest,
    InvestigationResponse,
    InvestigationSummary,
)
from apps.api.main import app

client = TestClient(app)


def _build_test_investigation_response() -> InvestigationResponse:
    """Helper to build a valid InvestigationResponse."""
    req = InvestigationRequest(
        metric="total_gmv",
        current_start=date(2017, 11, 24),
        current_end=date(2017, 11, 24),
        baseline_start=date(2017, 11, 17),
        baseline_end=date(2017, 11, 17),
        dimensions=["customer_state"],
    )
    return InvestigationResponse(
        request=req,
        summary=InvestigationSummary(
            metric="total_gmv",
            direction="increase",
            total_current=152653.74,
            total_baseline=29209.07,
            total_change=123444.67,
            total_change_pct=422.62,
            primary_positive_dimension="customer_state",
            primary_positive_contributor="SP",
        ),
        analyses=[
            ContributionAnalysis(
                metric="total_gmv",
                dimension="customer_state",
                current_start=req.current_start,
                current_end=req.current_end,
                baseline_start=req.baseline_start,
                baseline_end=req.baseline_end,
                total_current=152653.74,
                total_baseline=29209.07,
                total_change=123444.67,
                total_change_pct=422.62,
                top_positive_contributors=[
                    Contributor(
                        dimension="customer_state",
                        value="SP",
                        current_value=36977.40,
                        baseline_value=7000.00,
                        absolute_change=29977.40,
                        percentage_change=428.25,
                        contribution_pct=24.28,
                        rank=1,
                    )
                ],
                top_negative_contributors=[],
                all_contributors_count=1,
            )
        ],
    )


def test_narrative_endpoint_success() -> None:
    """Test POST /api/v1/investigations/narrative endpoint."""
    inv = _build_test_investigation_response()
    payload = {"investigation": inv.model_dump(mode="json")}

    response = client.post(
        "/api/v1/investigations/narrative",
        json=payload,
    )

    assert response.status_code == 200
    data = response.json()
    assert "title" in data
    assert "executive_summary" in data
    assert "anomaly_statement" in data
    assert len(data["key_findings"]) >= 1
    assert len(data["root_causes"]) >= 1
    assert len(data["evidence_references"]) >= 1
    assert "disclaimer" in data
    assert data["narrator_type"] in ["llm", "deterministic_fallback"]


def test_narrative_endpoint_invalid_payload() -> None:
    """Test POST /api/v1/investigations/narrative rejects malformed payload."""
    response = client.post(
        "/api/v1/investigations/narrative",
        json={"invalid_field": {}},
    )
    assert response.status_code == 422
