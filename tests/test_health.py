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
