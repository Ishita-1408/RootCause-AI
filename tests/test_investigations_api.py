"""Integration tests for Phase 5B Investigations FastAPI endpoints."""

from datetime import date
from unittest.mock import MagicMock, patch

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


@patch("apps.api.routers.investigations.get_db_connection")
@patch("apps.api.routers.investigations.run_investigation")
def test_investigate_contributions_endpoint_success(
    mock_run_inv: MagicMock, mock_conn: MagicMock
) -> None:
    """Test POST /api/v1/investigations/contributions endpoint."""
    req = InvestigationRequest(
        metric="total_gmv",
        current_start=date(2017, 11, 24),
        current_end=date(2017, 11, 24),
        baseline_start=date(2017, 11, 17),
        baseline_end=date(2017, 11, 17),
        dimensions=["customer_state"],
    )

    mock_run_inv.return_value = InvestigationResponse(
        request=req,
        summary=InvestigationSummary(
            metric="total_gmv",
            direction="increase",
            total_current=150000.0,
            total_baseline=30000.0,
            total_change=120000.0,
            total_change_pct=400.0,
            primary_positive_dimension="customer_state",
            primary_positive_contributor="SP",
        ),
        analyses=[
            ContributionAnalysis(
                metric="total_gmv",
                dimension="customer_state",
                current_start=date(2017, 11, 24),
                current_end=date(2017, 11, 24),
                baseline_start=date(2017, 11, 17),
                baseline_end=date(2017, 11, 17),
                total_current=150000.0,
                total_baseline=30000.0,
                total_change=120000.0,
                total_change_pct=400.0,
                top_positive_contributors=[
                    Contributor(
                        dimension="customer_state",
                        value="SP",
                        current_value=60000.0,
                        baseline_value=10000.0,
                        absolute_change=50000.0,
                        percentage_change=500.0,
                        contribution_pct=41.67,
                        rank=1,
                    )
                ],
                top_negative_contributors=[],
                all_contributors_count=1,
            )
        ],
    )

    response = client.post(
        "/api/v1/investigations/contributions",
        json={
            "metric": "total_gmv",
            "current_start": "2017-11-24",
            "current_end": "2017-11-24",
            "baseline_start": "2017-11-17",
            "baseline_end": "2017-11-17",
            "dimensions": ["customer_state"],
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["summary"]["direction"] == "increase"
    assert data["summary"]["primary_positive_contributor"] == "SP"
    assert len(data["analyses"]) == 1


def test_investigate_contributions_validation_error() -> None:
    """Test validation error for inverted date range."""
    response = client.post(
        "/api/v1/investigations/contributions",
        json={
            "metric": "total_gmv",
            "current_start": "2017-11-30",
            "current_end": "2017-11-01",  # Invalid range
            "baseline_start": "2017-10-01",
            "baseline_end": "2017-10-31",
            "dimensions": ["customer_state"],
        },
    )
    assert response.status_code == 422
