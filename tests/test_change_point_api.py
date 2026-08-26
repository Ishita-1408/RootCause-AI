"""Integration tests for Change-Point API endpoint."""

from datetime import date
from unittest.mock import patch

from fastapi.testclient import TestClient

from apps.analytics.anomaly.models import DailyKPIObservation
from apps.api.main import app

client = TestClient(app)


def test_change_point_endpoint_success() -> None:
    """Verify POST /api/v1/anomalies/change-point returns valid schema."""
    mock_obs = [
        DailyKPIObservation(date=date(2017, 1, 1), metric="total_gmv", value=100.0),
        DailyKPIObservation(date=date(2017, 1, 2), metric="total_gmv", value=102.0),
        DailyKPIObservation(date=date(2017, 1, 3), metric="total_gmv", value=98.0),
        DailyKPIObservation(date=date(2017, 1, 4), metric="total_gmv", value=101.0),
        DailyKPIObservation(date=date(2017, 1, 5), metric="total_gmv", value=160.0),
        DailyKPIObservation(date=date(2017, 1, 6), metric="total_gmv", value=162.0),
        DailyKPIObservation(date=date(2017, 1, 7), metric="total_gmv", value=158.0),
        DailyKPIObservation(date=date(2017, 1, 8), metric="total_gmv", value=161.0),
    ]

    with patch(
        "apps.analytics.change_detection.detector.fetch_daily_kpi_series",
        return_value=mock_obs,
    ):
        payload = {
            "metric": "total_gmv",
            "start_date": "2017-01-01",
            "end_date": "2017-01-08",
            "minimum_segment_size": 3,
        }
        resp = client.post("/api/v1/anomalies/change-point", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["metric"] == "total_gmv"
        assert "change_point" in data
        assert data["change_point"]["change_point_detected"] is True
        assert data["change_point"]["regime_type"] == "sustained_level_shift"


def test_change_point_endpoint_invalid_date_range() -> None:
    """Verify validation error on invalid date sequence."""
    payload = {
        "metric": "total_gmv",
        "start_date": "2017-01-10",
        "end_date": "2017-01-01",
    }
    resp = client.post("/api/v1/anomalies/change-point", json=payload)
    assert resp.status_code == 422
