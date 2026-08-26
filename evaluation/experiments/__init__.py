"""Controlled Baseline vs Improved Agent Experiment Framework."""

from evaluation.experiments.baseline_agent import BaselineInvestigationAgent
from evaluation.experiments.comparison import (
    AggregateComparisonSummary,
    ScenarioComparisonResult,
    run_comparison_experiment,
)
from evaluation.experiments.improved_agent import ImprovedInvestigationAgent

__all__ = [
    "BaselineInvestigationAgent",
    "ImprovedInvestigationAgent",
    "ScenarioComparisonResult",
    "AggregateComparisonSummary",
    "run_comparison_experiment",
]
