"""Improved Investigation Agent Adapter (Current Production Agent).

Wraps the production AutonomousInvestigationAgent with:
- Formal Causal Reasoning & Segment Separation (Phase C)
- Structured Causal Evaluator v2 Compatibility
- Verified Evidence-Backed Claims (Phase H)
- Deterministic Online Claim Verification Firewall (Phase H)
"""

import psycopg

from apps.analytics.agent.agent import AutonomousInvestigationAgent
from apps.analytics.agent.models import (
    InvestigationAgentRequest,
    InvestigationAgentResponse,
)


class ImprovedInvestigationAgent:
    """Production Agent implementation with causal reasoning and claim firewall."""

    def __init__(self, conn: psycopg.Connection) -> None:
        self._agent = AutonomousInvestigationAgent(conn=conn)

    def run_investigation(
        self, request: InvestigationAgentRequest
    ) -> InvestigationAgentResponse:
        """Run production investigation pipeline."""
        return self._agent.run_investigation(request)
