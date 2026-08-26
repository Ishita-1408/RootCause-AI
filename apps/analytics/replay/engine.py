"""Deterministic Investigation Replay Engine (Phase M)."""

from typing import Any

from apps.analytics.agent.models import InvestigationAgentResponse
from apps.analytics.replay.models import InvestigationSnapshot, ReplayStep

_SESSION_STORE: dict[str, InvestigationSnapshot] = {}


def register_investigation_snapshot(
    response: InvestigationAgentResponse,
) -> InvestigationSnapshot:
    """Compile and register an immutable replay snapshot from an agent response."""
    session_id = response.investigation_id

    replay_steps: list[ReplayStep] = []
    for idx, trace in enumerate(response.trace, start=1):
        replay_steps.append(
            ReplayStep(
                step_index=idx,
                step_title=trace.step_title,
                step_type=trace.step_type,
                status=trace.status,
                timestamp=trace.executed_at,
                finding_summary=trace.finding_summary,
                intermediate_state=trace.details,
            )
        )

    obs_summary = response.anomaly_summary
    obs_val = (
        obs_summary.observed_value
        if obs_summary and obs_summary.observed_value is not None
        else 0.0
    )
    base_val = (
        obs_summary.baseline_value
        if obs_summary and obs_summary.baseline_value is not None
        else 0.0
    )

    snapshot = InvestigationSnapshot(
        session_id=session_id,
        metric=response.anomaly_summary.metric,
        anomaly_date=str(response.anomaly_summary.anomaly_date),
        observed_value=float(obs_val),
        baseline_value=float(base_val),
        total_steps=len(response.trace),
        ranked_causes=response.top_root_causes,
        step_traces=response.trace,
        evidence_graph=getattr(response, "evidence_graph", None),
        replay_steps=replay_steps,
        metadata={
            "steps_executed": response.steps_executed,
            "status": response.investigation_status,
        },
    )

    _SESSION_STORE[session_id] = snapshot
    return snapshot


def get_investigation_snapshot(session_id: str) -> InvestigationSnapshot | None:
    """Retrieve an existing investigation snapshot for deterministic playback."""
    return _SESSION_STORE.get(session_id)


def list_recent_snapshots(limit: int = 20) -> list[dict[str, Any]]:
    """List recent investigation snapshots."""
    items = list(_SESSION_STORE.values())[-limit:]
    return [
        {
            "session_id": s.session_id,
            "metric": s.metric,
            "anomaly_date": s.anomaly_date,
            "total_steps": s.total_steps,
            "top_cause": s.ranked_causes[0].title if s.ranked_causes else "Unknown",
            "created_at": s.created_at.isoformat(),
        }
        for s in reversed(items)
    ]
