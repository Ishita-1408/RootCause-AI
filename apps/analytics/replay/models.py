"""Pydantic data models for Investigation Replay & Session Snapshots (Phase M)."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from apps.analytics.agent.models import InvestigationStepTrace, RankedRootCause
from apps.analytics.graph.models import EvidenceGraph


class ReplayStep(BaseModel):
    """Single step in an investigation replay sequence."""

    step_index: int
    step_title: str
    step_type: str
    status: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    active_node_id: str | None = None
    query_executed: str | None = None
    finding_summary: str | None = None
    intermediate_state: dict[str, Any] = Field(default_factory=dict)


class InvestigationSnapshot(BaseModel):
    """Complete, immutable snapshot of an autonomous investigation session."""

    session_id: str = Field(..., description="Unique investigation session ID")
    metric: str
    anomaly_date: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    observed_value: float
    baseline_value: float
    total_steps: int
    ranked_causes: list[RankedRootCause] = Field(default_factory=list)
    step_traces: list[InvestigationStepTrace] = Field(default_factory=list)
    evidence_graph: EvidenceGraph | None = None
    replay_steps: list[ReplayStep] = Field(default_factory=list)
    benchmark_version: str = "v2.0"
    metadata: dict[str, Any] = Field(default_factory=dict)
