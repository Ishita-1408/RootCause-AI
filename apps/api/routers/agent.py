import json
import logging
from collections.abc import Iterator
from typing import Any

import psycopg
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse

from apps.analytics.agent import (
    InvestigationAgentRequest,
    InvestigationAgentResponse,
    run_autonomous_investigation,
    run_autonomous_investigation_stream,
)
from apps.api.db.connection import get_db_connection

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/agent",
    tags=["Autonomous Agent"],
)


@router.get(
    "/health",
    status_code=status.HTTP_200_OK,
    summary="Health check for autonomous investigation agent",
)
def agent_health() -> dict[str, str]:
    """Health check for autonomous investigation agent service."""
    return {"status": "healthy", "service": "autonomous_investigation_agent"}


@router.post(
    "/investigate",
    response_model=InvestigationAgentResponse,
    status_code=status.HTTP_200_OK,
    summary="Run autonomous multi-step business investigation",
    description=(
        "Executes an adaptive multi-step investigation against analytical marts. "
        "The agent dynamically plans, prioritizes, ranks root causes, tracks an "
        "audit trace, and synthesizes an executive decision memo."
    ),
)
def agent_investigate_endpoint(
    request: InvestigationAgentRequest,
) -> InvestigationAgentResponse:
    """Execute autonomous multi-step business investigation."""
    try:
        with get_db_connection() as conn:
            return run_autonomous_investigation(conn=conn, request=request)
    except ValueError as e:
        logger.warning(f"Validation error in agent investigation: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        ) from e
    except psycopg.Error as e:
        logger.error(f"Database error during agent investigation: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database service unavailable during agent investigation.",
        ) from e
    except Exception as e:
        logger.error(f"Unexpected error in agent investigation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to execute autonomous investigation.",
        ) from e


@router.post(
    "/investigate/stream",
    status_code=status.HTTP_200_OK,
    summary="Run autonomous investigation with Server-Sent Events (SSE)",
    description=(
        "Streams progressive investigation stages as real-time SSE events. "
        "Each stage reflects actual deterministic backend query milestones."
    ),
)
def agent_investigate_stream_endpoint(
    request: InvestigationAgentRequest,
) -> StreamingResponse:
    """Execute autonomous investigation yielding real-time SSE event stream."""

    def event_generator() -> Iterator[str]:
        try:
            with get_db_connection() as conn:
                for event in run_autonomous_investigation_stream(
                    conn=conn, request=request
                ):
                    event_name = event.get("event", "message")
                    event_data = json.dumps(event.get("data", {}))
                    yield f"event: {event_name}\ndata: {event_data}\n\n"
        except ValueError as e:
            error_data = json.dumps({"error": str(e), "type": "validation_error"})
            yield f"event: error\ndata: {error_data}\n\n"
        except Exception as e:
            logger.error(f"Unexpected streaming agent error: {e}")
            error_data = json.dumps(
                {"error": "Failed to stream investigation", "type": "server_error"}
            )
            yield f"event: error\ndata: {error_data}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get(
    "/graph/{session_id}",
    status_code=status.HTTP_200_OK,
    summary="Get Evidence Graph for an investigation session",
)
def get_evidence_graph_endpoint(session_id: str) -> dict[str, Any]:
    """Retrieve the structured Evidence Graph DAG for an investigation session."""
    from apps.analytics.replay.engine import get_investigation_snapshot

    snapshot = get_investigation_snapshot(session_id)
    if not snapshot or not snapshot.evidence_graph:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No evidence graph found for session {session_id}.",
        )
    return snapshot.evidence_graph.model_dump(mode="json")


@router.post(
    "/challenge",
    status_code=status.HTTP_200_OK,
    summary="Challenge an investigation conclusion with counterfactual inquiry",
)
def challenge_investigation_endpoint(
    request: dict[str, Any],
) -> dict[str, Any]:
    """Evaluate a user challenge query against the verified Evidence Graph."""
    from apps.analytics.challenge import ChallengeRequest, evaluate_challenge

    try:
        req = ChallengeRequest(**request)
        res = evaluate_challenge(req)
        return res.model_dump(mode="json")
    except Exception as e:
        logger.error(f"Error evaluating challenge: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid challenge request: {e}",
        ) from e


@router.get(
    "/replay/sessions",
    status_code=status.HTTP_200_OK,
    summary="List available investigation replay sessions",
)
def list_replay_sessions_endpoint() -> list[dict[str, Any]]:
    """List recent investigation sessions available for deterministic replay."""
    from apps.analytics.replay import list_recent_snapshots

    return list_recent_snapshots()


@router.get(
    "/replay/{session_id}",
    status_code=status.HTTP_200_OK,
    summary="Get full investigation replay snapshot by session ID",
)
def get_replay_snapshot_endpoint(session_id: str) -> dict[str, Any]:
    """Retrieve full immutable investigation snapshot for step-by-step playback."""
    from apps.analytics.replay import get_investigation_snapshot

    snapshot = get_investigation_snapshot(session_id)
    if not snapshot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No replay session found for session ID {session_id}.",
        )
    return snapshot.model_dump(mode="json")
