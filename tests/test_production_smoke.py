"""Production smoke tests for RootCause AI deployment validation."""

from datetime import date
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from apps.analytics.anomaly.models import (
    AnomalyDetectionResponse,
    AnomalyResult,
)
from apps.analytics.rootcause.models import (
    AnomalySummary,
    DimensionContributor,
    OperationalIndicators,
    RootCauseInvestigationRequest,
    RootCauseInvestigationResponse,
    VolumeValueDecomposition,
)
from apps.api.main import app

client = TestClient(app)


# 1. Smoke Test: Application Liveness
def test_smoke_health_liveness() -> None:
    """Smoke test: verify /health and /api/v1/health return 200 OK."""
    for path in ("/health", "/api/v1/health"):
        res = client.get(path)
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "ok"
        assert data["app"] == "RootCause AI"


# 2. Smoke Test: Database Readiness
@patch("apps.api.routers.health.check_database_connection")
def test_smoke_database_readiness(mock_check_db: MagicMock) -> None:
    """Smoke test: verify /ready and /api/v1/ready return 200 when connected."""
    mock_check_db.return_value = True
    for path in ("/ready", "/api/v1/ready"):
        res = client.get(path)
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "ready"
        assert data["database"] == "connected"


# 3. Smoke Test: Anomaly Detection Endpoint
@patch("apps.api.routers.anomalies.run_anomaly_detection")
@patch("apps.api.routers.anomalies.get_db_connection")
def test_smoke_anomaly_detection_endpoint(
    mock_conn: MagicMock, mock_detect: MagicMock
) -> None:
    """Smoke test: verify /api/v1/anomalies/detect returns response."""
    mock_detect.return_value = AnomalyDetectionResponse(
        metric="total_gmv",
        start_date=date(2017, 11, 1),
        end_date=date(2017, 11, 30),
        window=7,
        z_threshold=2.0,
        minimum_history=7,
        total_observations=30,
        anomalies_count=1,
        results=[
            AnomalyResult(
                date=date(2017, 11, 24),
                metric="total_gmv",
                observed_value=152653.74,
                baseline_mean=31524.93,
                baseline_std=5000.0,
                z_score=4.25,
                severity="critical",
                is_anomaly=True,
                direction="increase",
            )
        ],
    )

    res = client.post(
        "/api/v1/anomalies/detect",
        json={
            "metric": "total_gmv",
            "start_date": "2017-11-01",
            "end_date": "2017-11-30",
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["anomalies_count"] == 1
    assert data["results"][0]["z_score"] == 4.25


# 4. Smoke Test: Deterministic Root-Cause Investigation Endpoint
@patch("apps.api.routers.rootcause.investigate_root_cause")
@patch("apps.api.routers.rootcause.get_db_connection")
def test_smoke_rootcause_investigation_endpoint(
    mock_conn: MagicMock, mock_investigate: MagicMock
) -> None:
    """Smoke test: verify /api/v1/rootcause/investigate returns decomposition."""
    mock_investigate.return_value = RootCauseInvestigationResponse(
        request=RootCauseInvestigationRequest(
            metric="total_gmv",
            anomaly_date=date(2017, 11, 24),
        ),
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
        ranked_contributors=[
            DimensionContributor(
                dimension="customer_state",
                dimension_value="SP",
                observed_value=50000.0,
                baseline_value=11448.32,
                absolute_change=38551.68,
                percentage_change=336.75,
                contribution_pct=31.83,
                direction="increase",
                rank=1,
            )
        ],
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
        explanation="TOTAL_GMV shifted +384.2% on 2017-11-24.",
        limitations="Associations only.",
    )

    res = client.post(
        "/api/v1/rootcause/investigate",
        json={
            "metric": "total_gmv",
            "anomaly_date": "2017-11-24",
            "comparison_days": 7,
            "dimensions": ["customer_state"],
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["summary"]["percentage_change"] == 384.2
    assert data["decomposition"]["volume_contribution_pct"] == 122.14


# 5. Smoke Test: AI Executive Investigation with Offline Fallback
@patch("apps.api.routers.ai.investigate_root_cause")
@patch("apps.api.routers.ai.get_db_connection")
def test_smoke_ai_investigate_fallback(
    mock_conn: MagicMock, mock_rc: MagicMock
) -> None:
    """Smoke test: verify /api/v1/ai/investigate falls back safely."""
    mock_rc.return_value = RootCauseInvestigationResponse(
        request=RootCauseInvestigationRequest(
            metric="total_gmv",
            anomaly_date=date(2017, 11, 24),
        ),
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
        explanation="TOTAL_GMV shifted +384.2%.",
        limitations="Non-causal.",
    )

    res = client.post(
        "/api/v1/ai/investigate",
        json={
            "metric": "total_gmv",
            "anomaly_date": "2017-11-24",
            "comparison_days": 7,
            "dimensions": ["customer_state"],
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert "TOTAL_GMV" in data["executive_summary"]
    assert data["is_fallback"] is True
