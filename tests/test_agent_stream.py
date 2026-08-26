from collections.abc import Iterator
from typing import Any
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from apps.analytics.agent.models import InvestigationAgentRequest
from apps.api.main import create_app


@pytest.fixture
def client() -> TestClient:
    """Create test client for agent stream tests."""
    app = create_app()
    return TestClient(app)


def test_agent_investigate_stream_lifecycle(
    monkeypatch: pytest.MonkeyPatch, client: TestClient
) -> None:
    """Test SSE streaming endpoint yields events across investigation stages."""
    from apps.api.routers import agent

    def mock_stream_generator(
        conn: object, request: InvestigationAgentRequest
    ) -> Iterator[dict[str, Any]]:
        yield {
            "event": "investigation_started",
            "data": {
                "investigation_id": "inv-mock-stream-123",
                "metric": request.metric,
                "anomaly_date": str(request.anomaly_date),
            },
        }
        yield {
            "event": "stage_update",
            "data": {
                "stage": 1,
                "title": "Detected Unusual Metric Shift",
                "status": "completed",
                "finding": "Anomaly on 2017-11-24 (+384.2% vs baseline)",
            },
        }
        yield {
            "event": "stage_update",
            "data": {
                "stage": 5,
                "title": "Reached Forensic Conclusion",
                "status": "completed",
                "finding": "Order Volume Surge explains 469% increase.",
            },
        }
        yield {
            "event": "investigation_completed",
            "data": {
                "investigation_id": "inv-mock-stream-123",
                "investigation_status": "completed",
                "steps_executed": 5,
                "executive_summary": "Order Volume Surge explains 469% increase.",
            },
        }

    monkeypatch.setattr(
        agent, "run_autonomous_investigation_stream", mock_stream_generator
    )
    monkeypatch.setattr(agent, "get_db_connection", MagicMock())

    payload = {
        "metric": "total_gmv",
        "anomaly_date": "2017-11-24",
        "comparison_days": 7,
        "max_investigation_steps": 5,
    }

    resp = client.post("/api/v1/agent/investigate/stream", json=payload)
    assert resp.status_code == 200
    assert "text/event-stream" in resp.headers["content-type"]

    body = resp.text
    assert "event: investigation_started" in body
    assert "event: stage_update" in body
    assert "event: investigation_completed" in body
    assert "inv-mock-stream-123" in body
