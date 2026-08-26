"""Autonomous Investigation Agent Package for RootCause AI (Phase 8)."""

from apps.analytics.agent.agent import (
    AutonomousInvestigationAgent,
    run_autonomous_investigation,
    run_autonomous_investigation_stream,
)
from apps.analytics.agent.executor import execute_investigation_steps
from apps.analytics.agent.models import (
    ApprovedDimension,
    ApprovedMetric,
    InvestigationAgentRequest,
    InvestigationAgentResponse,
    InvestigationState,
    InvestigationStepTrace,
    RankedRootCause,
    StepStatus,
    StepType,
)
from apps.analytics.agent.planner import (
    adapt_plan_with_evidence,
    generate_initial_plan,
)
from apps.analytics.agent.policies import (
    should_skip_branch,
    should_terminate,
)
from apps.analytics.agent.ranker import (
    calculate_root_cause_score,
    rank_evidence,
)

__all__ = [
    "ApprovedDimension",
    "ApprovedMetric",
    "AutonomousInvestigationAgent",
    "InvestigationAgentRequest",
    "InvestigationAgentResponse",
    "InvestigationState",
    "InvestigationStepTrace",
    "RankedRootCause",
    "StepStatus",
    "StepType",
    "adapt_plan_with_evidence",
    "calculate_root_cause_score",
    "execute_investigation_steps",
    "generate_initial_plan",
    "rank_evidence",
    "run_autonomous_investigation",
    "run_autonomous_investigation_stream",
    "should_skip_branch",
    "should_terminate",
]
