"""FastAPI Integration and End-to-End Pipeline Tests for Phase 6."""

from datetime import date
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from apps.ai.models import AIInvestigationResponse
from apps.analytics.anomaly.models import (
    AnomalyDetectionResponse,
    AnomalyResult,
)
from apps.analytics.rootcause.models import (
    AnomalySummary,
    OperationalIndicators,
    RootCauseInvestigationRequest,
    RootCauseInvestigationResponse,
    VolumeValueDecomposition,
)
from apps.api.main import app

client = TestClient(app)


# 1. OpenAPI Documentation & Health Checks
def test_openapi_docs_and_schema_endpoint() -> None:
    """Test OpenAPI JSON schema is generated and contains all Phase 5-6 routes."""
    resp = client.get("/openapi.json")
    assert resp.status_code == 200
    schema = resp.json()
    paths = schema["paths"]

    assert "/api/v1/anomalies/detect" in paths
    assert "/api/v1/rootcause/investigate" in paths
    assert "/api/v1/ai/investigate" in paths
    assert "/api/v1/ai/explain" in paths
    assert "/api/v1/diagnostics/root-cause" in paths


def test_router_health_endpoints() -> None:
    """Test health endpoints for all routers."""
    for ep, svc in [
        ("/api/v1/anomalies/health", "anomaly_detector"),
        ("/api/v1/rootcause/health", "rootcause_engine"),
        ("/api/v1/ai/health", "ai_investigator"),
    ]:
        resp = client.get(ep)
        assert resp.status_code == 200
        assert resp.json()["service"] == svc


# 2. Phase 5A: Anomaly Detection API
@patch("apps.api.routers.anomalies.get_db_connection")
@patch("apps.api.routers.anomalies.run_anomaly_detection")
def test_detect_anomalies_api_endpoint(
    mock_run: MagicMock, mock_conn: MagicMock
) -> None:
    """Test POST /api/v1/anomalies/detect."""
    mock_run.return_value = AnomalyDetectionResponse(
        metric="total_gmv",
        product_category=None,
        start_date=date(2017, 11, 1),
        end_date=date(2017, 11, 30),
        window=7,
        z_threshold=2.0,
        minimum_history=7,
        total_observations=1,
        anomalies_count=1,
        results=[
            AnomalyResult(
                date=date(2017, 11, 24),
                metric="total_gmv",
                observed_value=152653.74,
                baseline_mean=31524.93,
                baseline_std=9958.12,
                z_score=12.16,
                severity="critical",
                is_anomaly=True,
                direction="increase",
            )
        ],
    )

    resp = client.post(
        "/api/v1/anomalies/detect",
        json={
            "metric": "total_gmv",
            "start_date": "2017-11-01",
            "end_date": "2017-11-30",
            "window": 7,
            "z_threshold": 2.0,
        },
    )

    assert resp.status_code == 200
    data = resp.json()
    assert data["metric"] == "total_gmv"
    assert data["anomalies_count"] == 1
    assert data["results"][0]["z_score"] == 12.16


def test_detect_anomalies_api_validation_error() -> None:
    """Test invalid date range validation in anomaly detection."""
    resp = client.post(
        "/api/v1/anomalies/detect",
        json={
            "metric": "total_gmv",
            "start_date": "2018-01-30",
            "end_date": "2018-01-01",  # Invalid: end before start
        },
    )
    assert resp.status_code == 422


# 3. Phase 5B: Root-Cause Drill-Down API
@patch("apps.api.routers.rootcause.get_db_connection")
@patch("apps.api.routers.rootcause.investigate_root_cause")
def test_rootcause_investigate_api_endpoint(
    mock_run: MagicMock, mock_conn: MagicMock
) -> None:
    """Test POST /api/v1/rootcause/investigate."""
    req = RootCauseInvestigationRequest(
        metric="total_gmv",
        anomaly_date=date(2017, 11, 24),
        comparison_days=7,
        dimensions=["product_category", "customer_state"],
    )
    mock_run.return_value = RootCauseInvestigationResponse(
        request=req,
        summary=AnomalySummary(
            metric="total_gmv",
            anomaly_date=date(2017, 11, 24),
            baseline_start_date=date(2017, 11, 17),
            baseline_end_date=date(2017, 11, 23),
            observed_value=152653.74,
            baseline_value=31524.93,
            absolute_change=121128.81,
            percentage_change=384.2,
            direction="increase",
        ),
        decomposition=VolumeValueDecomposition(
            observed_orders=1176.0,
            baseline_orders=207.0,
            observed_aov=129.81,
            baseline_aov=152.61,
            volume_effect=147944.71,
            aov_effect=-4709.80,
            interaction_effect=-22103.00,
            total_change=121128.81,
            volume_contribution_pct=122.14,
            aov_contribution_pct=-3.89,
            interaction_contribution_pct=-18.25,
        ),
        ranked_contributors=[],
        operational_indicators=OperationalIndicators(
            observed_late_delivery_rate=20.0,
            baseline_late_delivery_rate=14.2,
            late_delivery_rate_change=5.8,
            observed_avg_delivery_days=17.2,
            baseline_avg_delivery_days=12.5,
            avg_delivery_days_change=4.7,
            observed_cancellation_rate=0.4,
            baseline_cancellation_rate=0.2,
            cancellation_rate_change=0.2,
            observed_avg_review_score=3.73,
            baseline_avg_review_score=3.94,
            avg_review_score_change=-0.21,
        ),
        explanation="TOTAL_GMV increased +384.2% on 2017-11-24.",
        limitations="These findings identify associations, not causal relationships.",
    )

    resp = client.post(
        "/api/v1/rootcause/investigate",
        json={
            "metric": "total_gmv",
            "anomaly_date": "2017-11-24",
            "comparison_days": 7,
            "dimensions": ["product_category", "customer_state"],
        },
    )

    assert resp.status_code == 200
    data = resp.json()
    assert data["summary"]["percentage_change"] == 384.2
    assert data["decomposition"]["volume_effect"] == 147944.71


def test_rootcause_investigate_api_invalid_metric() -> None:
    """Test unapproved metric rejection in root-cause API."""
    resp = client.post(
        "/api/v1/rootcause/investigate",
        json={
            "metric": "unapproved_metric",
            "anomaly_date": "2017-11-24",
        },
    )
    assert resp.status_code == 422


# 4. Phase 5C: AI Investigation & Explain API
@patch("apps.api.routers.ai.get_db_connection")
@patch("apps.api.routers.ai.investigate_root_cause")
@patch("apps.api.routers.ai.investigate_with_ai")
def test_ai_investigate_api_endpoint(
    mock_ai: MagicMock, mock_rc: MagicMock, mock_conn: MagicMock
) -> None:
    """Test POST /api/v1/ai/investigate."""
    mock_ai.return_value = AIInvestigationResponse(
        investigation_title="Executive Memo: GMV Spike",
        executive_summary="GMV increased +384.2% on 2017-11-24.",
        key_findings=["Volume shifted +469.3%."],
        business_interpretation=["Promotional event alignment."],
        recommended_actions=["Align carrier dispatch."],
        limitations=["Non-causal."],
        model="gpt-4o-mini",
        is_fallback=False,
    )

    resp = client.post(
        "/api/v1/ai/investigate",
        json={
            "metric": "total_gmv",
            "anomaly_date": "2017-11-24",
            "comparison_days": 7,
        },
    )

    assert resp.status_code == 200
    data = resp.json()
    assert data["investigation_title"] == "Executive Memo: GMV Spike"
    assert data["model"] == "gpt-4o-mini"
