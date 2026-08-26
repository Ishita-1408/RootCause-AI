from unittest.mock import patch

from fastapi.testclient import TestClient

from apps.api.main import app

client = TestClient(app)


def test_health_endpoint() -> None:
    """Test that GET /health returns 200 OK and expected payload."""
    response = client.get("/health")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "ok"
    assert data["app"] == "RootCause AI"
    assert data["version"] == "0.1.0"
    assert "environment" in data


def test_api_v1_health_endpoint() -> None:
    """Test that GET /api/v1/health returns 200 OK."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@patch("apps.api.routers.health.check_database_connection")
def test_readiness_endpoint_healthy(mock_check_db: object) -> None:
    """Test that GET /ready returns 200 OK when DB is reachable."""
    mock_check_db.return_value = True  # type: ignore[attr-defined]
    response = client.get("/ready")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "ready"
    assert data["database"] == "connected"


@patch("apps.api.routers.health.check_database_connection")
def test_readiness_endpoint_unhealthy(mock_check_db: object) -> None:
    """Test that GET /ready returns 503 when DB is unreachable."""
    mock_check_db.return_value = False  # type: ignore[attr-defined]
    response = client.get("/ready")
    assert response.status_code == 503
    assert "Database connection failed" in response.json()["detail"]
