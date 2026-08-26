from datetime import UTC, datetime
from unittest.mock import MagicMock, patch
from uuid import uuid4

from fastapi.testclient import TestClient

from apps.api.main import app

client = TestClient(app)


def test_list_datasets_empty() -> None:
    """Test GET /api/v1/datasets when no datasets exist."""
    mock_cursor = MagicMock()
    mock_cursor.fetchall.return_value = []

    mock_conn = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

    with patch("apps.api.routers.datasets.get_db_connection") as mock_get_conn:
        mock_get_conn.return_value.__enter__.return_value = mock_conn

        response = client.get("/api/v1/datasets")
        assert response.status_code == 200
        assert response.json() == []


def test_list_datasets_success() -> None:
    """Test GET /api/v1/datasets returning dataset list."""
    sample_id = uuid4()
    now = datetime.now(UTC)
    mock_cursor = MagicMock()
    mock_cursor.fetchall.return_value = [
        {
            "id": sample_id,
            "name": "Olist Brazilian E-Commerce Dataset",
            "description": "Brazilian e-commerce dataset",
            "source": "Kaggle",
            "status": "registered",
            "created_at": now,
            "updated_at": now,
        }
    ]

    mock_conn = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

    with patch("apps.api.routers.datasets.get_db_connection") as mock_get_conn:
        mock_get_conn.return_value.__enter__.return_value = mock_conn

        response = client.get("/api/v1/datasets")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Olist Brazilian E-Commerce Dataset"
        assert data[0]["id"] == str(sample_id)


def test_create_dataset_success() -> None:
    """Test POST /api/v1/datasets inserting a new dataset."""
    sample_id = uuid4()
    now = datetime.now(UTC)
    mock_cursor = MagicMock()
    mock_cursor.fetchone.return_value = {
        "id": sample_id,
        "name": "Olist Brazilian E-Commerce Dataset",
        "description": "Brazilian e-commerce dataset for analysis",
        "source": "Kaggle",
        "status": "registered",
        "created_at": now,
        "updated_at": now,
    }

    mock_conn = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

    with patch("apps.api.routers.datasets.get_db_connection") as mock_get_conn:
        mock_get_conn.return_value.__enter__.return_value = mock_conn

        response = client.post(
            "/api/v1/datasets",
            json={
                "name": "Olist Brazilian E-Commerce Dataset",
                "description": "Brazilian e-commerce dataset for analysis",
                "source": "Kaggle",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["id"] == str(sample_id)
        assert data["name"] == "Olist Brazilian E-Commerce Dataset"
        assert data["status"] == "registered"


def test_create_dataset_validation_error() -> None:
    """Test POST /api/v1/datasets with invalid payload returns 422."""
    response = client.post("/api/v1/datasets", json={})
    assert response.status_code == 422


def test_list_datasets_db_error() -> None:
    """Test GET /api/v1/datasets returns 503 on database failure."""
    with patch(
        "apps.api.routers.datasets.get_db_connection",
        side_effect=Exception("DB connection error"),
    ):
        response = client.get("/api/v1/datasets")
        assert response.status_code == 503
        assert response.json()["detail"] == "Failed to retrieve datasets from database"
