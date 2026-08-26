"""Pydantic data models for Structured Evidence Graph (Phase M)."""

from datetime import UTC, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

from apps.analytics.statistics.models import (
    CausalHierarchyLevel,
    CausalSupportLevel,
    ConfidenceInterval,
    StatisticalSignificance,
)

NodeType = Literal[
    "INCIDENT",
    "ANOMALY",
    "DRIVER",
    "EVIDENCE",
    "SEGMENT",
    "CORROBORATION",
    "ROOT_CAUSE",
]

EdgeRelation = Literal[
    "DETECTED_AS",
    "DECOMPOSED_INTO",
    "SUPPORTED_BY",
    "CONCENTRATED_IN",
    "CORROBORATED_BY",
    "ATTRIBUTED_TO",
]


class GraphNode(BaseModel):
    """Single node in the structured forensic Evidence Graph."""

    node_id: str = Field(..., description="Unique identifier for the node")
    node_type: NodeType = Field(..., description="Evidence hierarchy tier")
    title: str = Field(..., description="Human-readable node label")
    description: str = Field(..., description="Detailed explanation of evidence item")
    metric_name: str | None = Field(default=None, description="Associated KPI metric")
    observed_value: float | None = Field(
        default=None, description="Observed numerical value"
    )
    baseline_value: float | None = Field(
        default=None, description="Historical baseline value"
    )
    contribution_pct: float | None = Field(
        default=None, description="Contribution share %"
    )
    absolute_change: float | None = Field(
        default=None, description="Absolute change amount"
    )
    confidence: float = Field(
        default=1.0, ge=0.0, le=1.0, description="Statistical confidence score"
    )
    causal_level: CausalSupportLevel = Field(
        default="mechanistic", description="Causal hierarchy classification"
    )
    causal_hierarchy_tier: CausalHierarchyLevel = Field(
        default=3, description="Tier 1-5 in causal hierarchy"
    )
    confidence_interval: ConfidenceInterval | None = None
    significance: StatisticalSignificance | None = None
    provenance_query_id: str | None = Field(
        default=None, description="ID of deterministic analytical query"
    )
    details: dict[str, Any] = Field(default_factory=dict)


class GraphEdge(BaseModel):
    """Directed edge connecting evidence nodes with forensic relation semantics."""

    source_id: str = Field(..., description="Source node ID")
    target_id: str = Field(..., description="Target node ID")
    relation: EdgeRelation = Field(..., description="Forensic relationship type")
    label: str = Field(default="", description="Descriptive edge label")
    weight: float = Field(
        default=1.0, ge=0.0, description="Attribution weight or contribution magnitude"
    )
    is_primary_path: bool = Field(
        default=True,
        description="True if this edge forms the primary causal explanation chain",
    )
    details: dict[str, Any] = Field(default_factory=dict)


class EvidenceGraph(BaseModel):
    """Complete Directed Acyclic Graph (DAG) of forensic investigation evidence."""

    graph_id: str = Field(..., description="Unique graph identifier")
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    root_node_id: str = Field(..., description="Top-level Incident node ID")
    nodes: list[GraphNode] = Field(default_factory=list)
    edges: list[GraphEdge] = Field(default_factory=list)
    primary_chain_node_ids: list[str] = Field(
        default_factory=list,
        description="Ordered sequence of node IDs along primary root cause path",
    )
    summary_metrics: dict[str, Any] = Field(
        default_factory=dict,
        description="Graph-level summary statistics (total nodes, depth, confidence)",
    )
