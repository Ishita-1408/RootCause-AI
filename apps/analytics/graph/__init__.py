"""Structured Evidence Graph Module (Phase M)."""

from apps.analytics.graph.builder import build_evidence_graph
from apps.analytics.graph.models import (
    EdgeRelation,
    EvidenceGraph,
    GraphEdge,
    GraphNode,
    NodeType,
)

__all__ = [
    "EdgeRelation",
    "EvidenceGraph",
    "GraphEdge",
    "GraphNode",
    "NodeType",
    "build_evidence_graph",
]
