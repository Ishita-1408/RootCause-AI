"""Unit tests for Phase 5B Deterministic Root-Cause Contribution Engine."""

from datetime import date
from unittest.mock import MagicMock

import pytest

from apps.analytics.investigation.engine import (
    calculate_slice_metrics,
    run_contribution_analysis,
    run_investigation,
)
from apps.analytics.investigation.models import (
    InvestigationRequest,
)
from apps.analytics.investigation.queries import (
    DimensionSliceRecord,
    build_contribution_query,
)


def test_calculate_slice_metrics_growth_and_decline() -> None:
    """Test slice contribution with mixed positive and negative movements.

    Scenario: Total GMV declined by -R$ 100k
    Category A: -R$ 50k (50% contribution to drop)
    Category B: -R$ 70k (70% contribution to drop)
    Category C: +R$ 20k (-20% contribution to drop, offsetting)
    """
    slices: list[DimensionSliceRecord] = [
        {
            "slice_value": "Category_A",
            "current_value": 50000.0,
            "baseline_value": 100000.0,
        },
        {
            "slice_value": "Category_B",
            "current_value": 30000.0,
            "baseline_value": 100000.0,
        },
        {
            "slice_value": "Category_C",
            "current_value": 60000.0,
            "baseline_value": 40000.0,
        },
    ]

    tot_c, tot_b, tot_diff, tot_pct, pos_contribs, neg_contribs = (
        calculate_slice_metrics(
            slices=slices, dimension_name="product_category_name", limit=10
        )
    )

    assert tot_c == 140000.0
    assert tot_b == 240000.0
    assert tot_diff == -100000.0
    assert tot_pct == -41.67

    # Negative contributors (drivers of decline)
    assert len(neg_contribs) == 2
    assert neg_contribs[0].value == "Category_B"
    assert neg_contribs[0].absolute_change == -70000.0
    assert neg_contribs[0].contribution_pct == 70.0
    assert neg_contribs[0].rank == 1

    assert neg_contribs[1].value == "Category_A"
    assert neg_contribs[1].absolute_change == -50000.0
    assert neg_contribs[1].contribution_pct == 50.0
    assert neg_contribs[1].rank == 2

    # Positive contributors (offsetting growth)
    assert len(pos_contribs) == 1
    assert pos_contribs[0].value == "Category_C"
    assert pos_contribs[0].absolute_change == 20000.0
    assert pos_contribs[0].contribution_pct == -20.0
    assert pos_contribs[0].rank == 1


def test_calculate_slice_metrics_dimension_only_in_current_or_baseline() -> None:
    """Test handling of new dimension slices and churned slices."""
    slices: list[DimensionSliceRecord] = [
        # New category (exists only currently)
        {"slice_value": "New_Cat", "current_value": 5000.0, "baseline_value": 0.0},
        # Discontinued category (exists only in baseline)
        {"slice_value": "Old_Cat", "current_value": 0.0, "baseline_value": 8000.0},
    ]

    tot_c, tot_b, tot_diff, tot_pct, pos, neg = calculate_slice_metrics(
        slices=slices, dimension_name="product_category_name"
    )

    assert tot_c == 5000.0
    assert tot_b == 8000.0
    assert tot_diff == -3000.0

    # New_Cat is positive contributor
    assert len(pos) == 1
    assert pos[0].value == "New_Cat"
    assert pos[0].percentage_change == 100.0  # Zero baseline handling

    # Old_Cat is negative contributor
    assert len(neg) == 1
    assert neg[0].value == "Old_Cat"
    assert neg[0].percentage_change == -100.0


def test_calculate_slice_metrics_zero_total_change() -> None:
    """Test that zero total change sets contribution_pct safely to None."""
    slices: list[DimensionSliceRecord] = [
        {"slice_value": "SP", "current_value": 1000.0, "baseline_value": 500.0},
        {"slice_value": "RJ", "current_value": 500.0, "baseline_value": 1000.0},
    ]

    tot_c, tot_b, tot_diff, tot_pct, pos, neg = calculate_slice_metrics(
        slices=slices, dimension_name="customer_state"
    )

    assert tot_diff == 0.0
    assert pos[0].contribution_pct is None
    assert neg[0].contribution_pct is None


def test_calculate_slice_metrics_empty_slices() -> None:
    """Test empty slices sequence returns safe zeroes."""
    tot_c, tot_b, tot_diff, tot_pct, pos, neg = calculate_slice_metrics(
        slices=[], dimension_name="customer_state"
    )
    assert tot_c == 0.0
    assert tot_b == 0.0
    assert tot_diff == 0.0
    assert tot_pct == 0.0
    assert len(pos) == 0
    assert len(neg) == 0


def test_investigation_request_validation() -> None:
    """Test request date validation."""
    with pytest.raises(ValueError, match="current_end cannot be earlier"):
        InvestigationRequest(
            metric="total_gmv",
            current_start=date(2018, 5, 31),
            current_end=date(2018, 5, 1),
            baseline_start=date(2018, 4, 1),
            baseline_end=date(2018, 4, 30),
        )

    with pytest.raises(ValueError, match="baseline_end cannot be earlier"):
        InvestigationRequest(
            metric="total_gmv",
            current_start=date(2018, 5, 1),
            current_end=date(2018, 5, 31),
            baseline_start=date(2018, 4, 30),
            baseline_end=date(2018, 4, 1),
        )


def test_run_contribution_analysis_unsupported_validation() -> None:
    """Test validation errors for invalid metric or dimension."""
    mock_conn = MagicMock()

    with pytest.raises(ValueError, match="Unsupported metric"):
        run_contribution_analysis(
            conn=mock_conn,
            metric="invalid_metric",
            dimension="customer_state",
            current_start=date(2018, 5, 1),
            current_end=date(2018, 5, 31),
            baseline_start=date(2018, 4, 1),
            baseline_end=date(2018, 4, 30),
        )

    with pytest.raises(ValueError, match="Unsupported dimension"):
        run_contribution_analysis(
            conn=mock_conn,
            metric="total_gmv",
            dimension="invalid_dimension",
            current_start=date(2018, 5, 1),
            current_end=date(2018, 5, 31),
            baseline_start=date(2018, 4, 1),
            baseline_end=date(2018, 4, 30),
        )


def test_build_contribution_query_structure() -> None:
    """Test SQL query construction across supported dimensions."""
    query_state = build_contribution_query("total_gmv", "customer_state")
    assert "fact_order_analytics" in query_state
    assert "customer_state" in query_state
    assert "FULL OUTER JOIN" in query_state

    query_seller = build_contribution_query("orders_count", "seller_id")
    assert "order_items" in query_seller
    assert "seller_id" in query_seller

    query_cat = build_contribution_query("total_gmv", "product_category_name")
    assert "products" in query_cat
    assert "product_category_name" in query_cat


def test_run_investigation_orchestration_mocked() -> None:
    """Test full multi-dimensional investigation summary generation."""
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cur

    # Mock SQL return for 2 dimensions (state and category)
    mock_cur.fetchall.side_effect = [
        # customer_state slices
        [
            {"slice_value": "SP", "current_value": 80000.0, "baseline_value": 100000.0},
            {"slice_value": "RJ", "current_value": 30000.0, "baseline_value": 20000.0},
        ],
        # product_category_name slices
        [
            {
                "slice_value": "telefonia",
                "current_value": 20000.0,
                "baseline_value": 50000.0,
            },
            {
                "slice_value": "beleza_saude",
                "current_value": 90000.0,
                "baseline_value": 70000.0,
            },
        ],
    ]

    req = InvestigationRequest(
        metric="total_gmv",
        current_start=date(2018, 5, 1),
        current_end=date(2018, 5, 31),
        baseline_start=date(2018, 4, 1),
        baseline_end=date(2018, 4, 30),
        dimensions=["customer_state", "product_category_name"],
    )

    resp = run_investigation(conn=mock_conn, request=req)

    assert len(resp.analyses) == 2
    assert resp.summary.metric == "total_gmv"
    assert resp.summary.direction == "decrease"
    assert resp.summary.total_change == -10000.0

    # Primary negative contributor identified across dimensions
    assert resp.summary.primary_negative_dimension == "product_category_name"
    assert resp.summary.primary_negative_contributor == "telefonia"

    # Primary positive contributor identified
    assert resp.summary.primary_positive_dimension == "product_category_name"
    assert resp.summary.primary_positive_contributor == "beleza_saude"
