from unittest.mock import patch

from fastapi.testclient import TestClient

from apps.api.main import app

client = TestClient(app)


def test_database_health_connected() -> None:
    """Test GET /health/database when database connection succeeds."""
    with patch(
        "apps.api.routers.database.check_database_connection",
        return_value=True,
    ):
        response = client.get("/health/database")
        assert response.status_code == 200
        assert response.json() == {
            "status": "ok",
            "database": "connected",
        }


def test_database_health_disconnected() -> None:
    """Test GET /health/database when database connection fails (503)."""
    with patch(
        "apps.api.routers.database.check_database_connection",
        return_value=False,
    ):
        response = client.get("/health/database")
        assert response.status_code == 503
        data = response.json()
        assert "detail" in data
        assert data["detail"] == "Database connection unavailable"
