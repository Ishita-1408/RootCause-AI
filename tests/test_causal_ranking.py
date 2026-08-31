"""Unit and integration tests for multi-signal causal ranking pipeline."""

from datetime import date

from apps.analytics.agent.ranker import calculate_root_cause_score, rank_evidence
from apps.analytics.rootcause.models import (
    AnomalySummary,
    DimensionContributor,
    OperationalIndicators,
    VolumeValueDecomposition,
)


def test_directional_alignment_explanatory_vs_countervailing() -> None:
    """Verify that a driver matching the anomaly direction receives higher weight."""
    aligned_score = calculate_root_cause_score(
        contribution_pct=60.0,
        absolute_change=-5000.0,
        dimension="order_volume",
        is_causal_mechanism=True,
        driver_direction="decrease",
        anomaly_direction="decrease",
    )
    countervailing_score = calculate_root_cause_score(
        contribution_pct=60.0,
        absolute_change=5000.0,
        dimension="order_volume",
        is_causal_mechanism=True,
        driver_direction="increase",
        anomaly_direction="decrease",
    )
    assert aligned_score > countervailing_score
    # Aligned score should be approximately 5x countervailing score
    assert aligned_score >= 4.0 * countervailing_score


def test_orders_count_metric_specificity() -> None:
    """Verify that orders_count investigations prioritize volume drivers over AOV."""
    summary = AnomalySummary(
        metric="orders_count",
        anomaly_date=date(2017, 11, 24),
        baseline_start_date=date(2017, 11, 17),
        baseline_end_date=date(2017, 11, 23),
        observed_value=500.0,
        baseline_value=200.0,
        absolute_change=300.0,
        percentage_change=150.0,
        direction="increase",
    )
    decomposition = VolumeValueDecomposition(
        observed_orders=500.0,
        baseline_orders=200.0,
        observed_aov=100.0,
        baseline_aov=100.0,
        volume_effect=30000.0,
        aov_effect=0.0,
        interaction_effect=0.0,
        total_change=30000.0,
        volume_contribution_pct=100.0,
        aov_contribution_pct=0.0,
        interaction_contribution_pct=0.0,
    )
    contributors = [
        DimensionContributor(
            dimension="customer_state",
            dimension_value="SP",
            observed_value=250.0,
            baseline_value=100.0,
            absolute_change=150.0,
            percentage_change=150.0,
            contribution_pct=50.0,
            direction="increase",
            rank=1,
        )
    ]

    ranked = rank_evidence(
        contributors=contributors,
        decomposition=decomposition,
        summary=summary,
    )

    assert len(ranked) >= 1
    assert ranked[0].causal_mechanism == "order_volume"
    assert ranked[0].causal_category == "macro_driver"
    assert "Surge" in ranked[0].title
    # Segment concentration is ranked lower than the causal mechanism
    assert ranked[1].causal_category == "segment_concentration"


def test_average_order_value_metric_specificity() -> None:
    """Verify that average_order_value investigations prioritize AOV drivers."""
    summary = AnomalySummary(
        metric="average_order_value",
        anomaly_date=date(2017, 5, 15),
        baseline_start_date=date(2017, 5, 8),
        baseline_end_date=date(2017, 5, 14),
        observed_value=250.0,
        baseline_value=120.0,
        absolute_change=130.0,
        percentage_change=108.3,
        direction="increase",
    )
    contributors = [
        DimensionContributor(
            dimension="product_category",
            dimension_value="relogios_presentes",
            observed_value=400.0,
            baseline_value=200.0,
            absolute_change=200.0,
            percentage_change=100.0,
            contribution_pct=65.0,
            direction="increase",
            rank=1,
        )
    ]

    ranked = rank_evidence(
        contributors=contributors,
        summary=summary,
    )

    assert len(ranked) >= 1
    assert ranked[0].causal_mechanism == "average_order_value"
    assert ranked[0].causal_category == "macro_driver"
    assert "Expansion" in ranked[0].title


def test_avg_review_score_operational_satisfaction_driver() -> None:
    """Verify that avg_review_score creates customer satisfaction driver."""
    summary = AnomalySummary(
        metric="avg_review_score",
        anomaly_date=date(2017, 11, 25),
        baseline_start_date=date(2017, 11, 18),
        baseline_end_date=date(2017, 11, 24),
        observed_value=3.2,
        baseline_value=4.2,
        absolute_change=-1.0,
        percentage_change=-23.8,
        direction="decrease",
    )
    contributors = [
        DimensionContributor(
            dimension="product_category",
            dimension_value="cama_mesa_banho",
            observed_value=2.8,
            baseline_value=4.1,
            absolute_change=-1.3,
            percentage_change=-31.7,
            contribution_pct=40.0,
            direction="decrease",
            rank=1,
        )
    ]

    ranked = rank_evidence(
        contributors=contributors,
        summary=summary,
    )

    assert len(ranked) >= 1
    assert ranked[0].causal_mechanism == "avg_review_score"
    assert ranked[0].causal_category == "operational_mechanism"
    assert "Decline" in ranked[0].title


def test_delivery_sla_operational_mechanism_ranking() -> None:
    """Verify that late_delivery_rate_pct prioritizes carrier SLA degradation."""
    summary = AnomalySummary(
        metric="late_delivery_rate_pct",
        anomaly_date=date(2017, 11, 24),
        baseline_start_date=date(2017, 11, 17),
        baseline_end_date=date(2017, 11, 23),
        observed_value=22.5,
        baseline_value=6.0,
        absolute_change=16.5,
        percentage_change=275.0,
        direction="increase",
    )
    op_signals = OperationalIndicators(
        observed_late_delivery_rate=22.5,
        baseline_late_delivery_rate=6.0,
        late_delivery_rate_change=16.5,
        observed_avg_delivery_days=15.0,
        baseline_avg_delivery_days=11.2,
        avg_delivery_days_change=3.8,
        observed_cancellation_rate=2.1,
        baseline_cancellation_rate=1.0,
        cancellation_rate_change=1.1,
        observed_avg_review_score=3.5,
        baseline_avg_review_score=4.2,
        avg_review_score_change=-0.7,
    )
    contributors = [
        DimensionContributor(
            dimension="customer_state",
            dimension_value="SP",
            observed_value=20.0,
            baseline_value=5.0,
            absolute_change=15.0,
            percentage_change=300.0,
            contribution_pct=70.0,
            direction="increase",
            rank=1,
        )
    ]

    ranked = rank_evidence(
        contributors=contributors,
        summary=summary,
        operational_signals=op_signals,
    )

    assert len(ranked) >= 1
    assert ranked[0].causal_mechanism == "delivery"
    assert ranked[0].causal_category == "operational_mechanism"
    assert "Degradation" in ranked[0].title


def test_distractor_penalty_on_low_percentage_shift() -> None:
    """Verify that high baseline volume with tiny shift gets distractor penalty."""
    high_shift_score = calculate_root_cause_score(
        contribution_pct=30.0,
        absolute_change=1000.0,
        dimension="customer_state",
        is_causal_mechanism=False,
        distractor_penalty=0.0,
    )
    distractor_score = calculate_root_cause_score(
        contribution_pct=30.0,
        absolute_change=1000.0,
        dimension="customer_state",
        is_causal_mechanism=False,
        distractor_penalty=15.0,
    )
    assert high_shift_score > distractor_score
