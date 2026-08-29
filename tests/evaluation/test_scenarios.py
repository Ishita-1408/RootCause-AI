"""Unit tests for Benchmark Scenario definitions and Registry."""

import pytest

from evaluation.scenarios import (
    BENCHMARK_SCENARIOS,
    get_all_scenarios,
    get_scenario,
)


def test_scenario_registry_count() -> None:
    """Verify that at least 100 canonical incident scenarios are registered."""
    scenarios = get_all_scenarios()
    assert len(scenarios) >= 100
    assert len(BENCHMARK_SCENARIOS) >= 100


def test_scenario_difficulty_distribution() -> None:
    """Ensure Easy, Medium, and Hard tiers are all represented."""
    scenarios = get_all_scenarios()
    difficulties = {s.difficulty for s in scenarios}
    assert difficulties == {"easy", "medium", "hard"}

    easy_count = sum(1 for s in scenarios if s.difficulty == "easy")
    medium_count = sum(1 for s in scenarios if s.difficulty == "medium")
    hard_count = sum(1 for s in scenarios if s.difficulty == "hard")

    assert easy_count >= 20
    assert medium_count >= 30
    assert hard_count >= 15


def test_scenario_metric_coverage() -> None:
    """Ensure all 5 core business metrics are covered in the benchmark."""
    scenarios = get_all_scenarios()
    metrics = {s.target_metric for s in scenarios}
    expected_metrics = {
        "total_gmv",
        "orders_count",
        "average_order_value",
        "late_delivery_rate_pct",
        "avg_review_score",
    }
    assert expected_metrics.issubset(metrics)


def test_scenario_unique_ids() -> None:
    """Ensure all scenario IDs are unique and non-empty."""
    ids = [s.scenario_id for s in get_all_scenarios()]
    assert len(ids) == len(set(ids))
    for s_id in ids:
        assert s_id.startswith("SCN-")


def test_scenario_required_metadata() -> None:
    """Ensure all scenarios define valid targets, metrics, and ground truth."""
    for s in get_all_scenarios():
        assert s.name
        assert s.description
        assert s.primary_cause.cause_id
        assert s.primary_cause.dimension
        assert s.target_metric in [
            "total_gmv",
            "orders_count",
            "average_order_value",
            "late_delivery_rate_pct",
            "avg_review_score",
        ]
        assert s.comparison_days >= 1
        assert s.expected_direction in ["increase", "decrease", "normal"]
        assert s.severity in ["normal", "warning", "critical"]
        assert s.difficulty in ["easy", "medium", "hard"]
        assert isinstance(s.distractor_causes, list)


def test_no_ground_truth_leakage() -> None:
    """Verify that scenario ID and expected cause are decoupled and not leaked."""
    for s in get_all_scenarios():
        # Description should not directly expose internal ground truth cause_id token
        assert s.primary_cause.cause_id != s.name
        assert s.primary_cause.cause_id != s.scenario_id


def test_get_scenario_by_id_success() -> None:
    """Verify fetching existing scenario by ID."""
    s = get_scenario("SCN-001")
    assert s.scenario_id == "SCN-001"
    assert s.primary_cause.dimension == "delivery"


def test_get_scenario_by_id_case_insensitive() -> None:
    """Verify scenario lookup is case-insensitive."""
    s = get_scenario("scn-002")
    assert s.scenario_id == "SCN-002"
    assert s.primary_cause.dimension == "order_volume"


def test_get_scenario_by_id_not_found() -> None:
    """Verify KeyError is raised for invalid scenario ID."""
    with pytest.raises(KeyError, match="not found in benchmark registry"):
        get_scenario("SCN-999")


def test_canonical_scenarios_structured_definitions() -> None:
    """Regression test: all 6 canonical scenarios have structured definitions."""
    from typing import Literal

    from apps.analytics.agent.models import RankedRootCause
    from evaluation.metrics.evaluator import _matches_cause

    expected_canonical_mechanisms: dict[
        str,
        tuple[
            Literal["macro_driver", "operational_mechanism", "segment_concentration"],
            str,
        ],
    ] = {
        "SCN-001": ("operational_mechanism", "delivery"),
        "SCN-002": ("macro_driver", "order_volume"),
        "SCN-003": ("macro_driver", "average_order_value"),
        "SCN-004": ("operational_mechanism", "delivery"),
        "SCN-005": ("macro_driver", "average_order_value"),
        "SCN-006": ("macro_driver", "order_volume"),
    }

    for scn_id, (expected_cat, expected_mech) in expected_canonical_mechanisms.items():
        scenario = get_scenario(scn_id)
        assert scenario.primary_cause.causal_category == expected_cat, (
            f"{scn_id} wrong causal category"
        )
        assert scenario.primary_cause.causal_mechanism == expected_mech, (
            f"{scn_id} wrong causal mechanism"
        )

        # Construct a synthetic matching prediction
        matching_pred = RankedRootCause(
            rank=1,
            title=f"Prediction for {scn_id}",
            dimension=scenario.primary_cause.dimension,
            dimension_value="val",
            contribution_pct=80.0,
            absolute_change=1000.0,
            score=90.0,
            explanation="Test explanation",
            causal_category=expected_cat,
            causal_mechanism=expected_mech,
        )
        assert _matches_cause(matching_pred, scenario.primary_cause) is True, (
            f"{scn_id} failed structured match"
        )

        # Verify a segment-only prediction does NOT match
        segment_pred = RankedRootCause(
            rank=1,
            title="Customer State: SP",
            dimension="customer_state",
            dimension_value="SP",
            contribution_pct=50.0,
            absolute_change=500.0,
            score=80.0,
            explanation="Segment concentration",
            causal_category="segment_concentration",
            causal_mechanism=None,
        )
        assert _matches_cause(segment_pred, scenario.primary_cause) is False, (
            f"{scn_id} incorrectly matched segment concentration"
        )
