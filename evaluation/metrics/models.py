"""Pydantic data models for Benchmark Evaluation Results and Summaries."""

from pydantic import BaseModel, Field


class EvaluationResult(BaseModel):
    """Evaluation output for a single benchmark scenario."""

    scenario_id: str = Field(..., description="Unique scenario identifier")
    scenario_name: str = Field(..., description="Scenario title")

    # Ground Truth vs Prediction
    ground_truth_primary: str = Field(
        ..., description="Expected ground-truth primary cause"
    )
    predicted_root_causes: list[str] = Field(
        default_factory=list, description="Ordered list of predicted root causes"
    )

    # Accuracy & Ranking Metrics
    top1_correct: bool = Field(
        ..., description="True if primary ground truth cause is ranked #1"
    )
    top3_correct: bool = Field(
        ..., description="True if primary ground truth cause is in top 3"
    )
    reciprocal_rank: float = Field(
        ..., description="1 / rank of correct cause, or 0 if not found"
    )
    false_positive_rate: float = Field(
        default=0.0, description="Ratio of unsupported/spurious causes ranked at top"
    )
    contribution_error: float | None = Field(
        default=None,
        description="Absolute error in quantitative contribution % where defined",
    )

    # Evidence Grounding & Integrity
    evidence_grounded: bool = Field(
        default=True,
        description="True if all claims are supported by analytical query output",
    )
    unsupported_claim_rate: float = Field(
        default=0.0, description="Proportion of claims made without numerical evidence"
    )
    hallucination_rate: float = Field(
        default=0.0, description="Rate of claims contradicting or inventing data"
    )

    # Investigation Efficiency
    investigation_steps: int = Field(
        default=0, description="Sequential steps executed by agent"
    )
    tool_calls: int = Field(
        default=0, description="Total analytical SQL / engine queries executed"
    )
    branches_explored: int = Field(
        default=0, description="Number of dimensional branches drilled down"
    )
    branches_pruned: int = Field(
        default=0, description="Number of low-signal branches pruned"
    )
    execution_time_ms: float = Field(
        default=0.0, description="End-to-end execution latency in ms"
    )
    stopping_reason: str = Field(
        default="", description="Why the investigation concluded"
    )

    # Forensic Failure Analysis
    failure_explanation: str | None = Field(
        default=None,
        description="Detailed diagnostic if scenario did not meet Top-1/Grounding",
    )


class BenchmarkSummary(BaseModel):
    """Aggregated benchmark metrics across all evaluated scenarios."""

    scenarios_evaluated: int = Field(
        ..., description="Total number of scenarios executed"
    )
    top1_accuracy: float = Field(
        ..., description="Percentage of scenarios with correct top-1 cause"
    )
    top3_accuracy: float = Field(
        ..., description="Percentage of scenarios with correct cause in top 3"
    )
    mrr: float = Field(..., description="Mean Reciprocal Rank across all scenarios")
    false_positive_rate: float = Field(
        ..., description="Average false positive rate across scenarios"
    )
    mean_contribution_error: float | None = Field(
        default=None, description="Mean absolute contribution % error"
    )
    evidence_grounding_rate: float = Field(
        ..., description="Percentage of scenarios with 100% evidence grounding"
    )
    unsupported_claim_rate: float = Field(
        ..., description="Average unsupported claim rate"
    )
    hallucination_rate: float = Field(
        ..., description="Average hallucination rate (should strictly be 0.0)"
    )
    avg_steps: float = Field(
        ..., description="Average investigation steps per scenario"
    )
    avg_tool_calls: float = Field(
        ..., description="Average analytical queries per scenario"
    )
    avg_execution_time_ms: float = Field(
        ..., description="Average execution latency in milliseconds"
    )
    results: list[EvaluationResult] = Field(
        default_factory=list, description="Per-scenario evaluation results"
    )
