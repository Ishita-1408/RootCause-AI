"""Unit tests for Phase 4B Dimensional Breakdown and Contribution Engine."""

from datetime import date
from unittest.mock import MagicMock

import pytest

from apps.analytics.breakdowns import get_dimensional_breakdown


def test_dimensional_breakdown_unclamped_contribution() -> None:
    """Test that contributions > 100% and negative contributions are unclamped."""
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cur

    # Scenario: Total GMV declined by -100k
    # Slice A dropped -150k (150% contribution!)
    # Slice B grew +50k (-50% contribution!)
    mock_cur.fetchall.return_value = [
        {
            "slice_value": "SP",
            "current_revenue": 100000.0,
            "baseline_revenue": 250000.0,
            "current_orders": 1000.0,
            "baseline_orders": 2500.0,
            "current_freight": 20000.0,
            "baseline_freight": 50000.0,
        },
        {
            "slice_value": "RJ",
            "current_revenue": 150000.0,
            "baseline_revenue": 100000.0,
            "current_orders": 1500.0,
            "baseline_orders": 1000.0,
            "current_freight": 30000.0,
            "baseline_freight": 20000.0,
        },
    ]

    res = get_dimensional_breakdown(
        conn=mock_conn,
        metric="gmv",
        dimension="customer_state",
        current_start=date(2018, 5, 1),
        current_end=date(2018, 5, 31),
        baseline_start=date(2018, 4, 1),
        baseline_end=date(2018, 4, 30),
    )

    assert res.total_change == -100000.0
    assert len(res.slices) == 2

    slice_sp = res.slices[0]
    assert slice_sp.slice_value == "SP"
    assert slice_sp.absolute_change == -150000.0
    assert slice_sp.contribution_percentage == 150.0  # Unclamped!
    assert slice_sp.rank == 1

    slice_rj = res.slices[1]
    assert slice_rj.slice_value == "RJ"
    assert slice_rj.absolute_change == 50000.0
    assert slice_rj.contribution_percentage == -50.0  # Unclamped negative!


def test_dimensional_breakdown_zero_total_change() -> None:
    """Test that zero total change sets contribution_percentage to None."""
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cur

    mock_cur.fetchall.return_value = [
        {
            "slice_value": "SP",
            "current_revenue": 100000.0,
            "baseline_revenue": 100000.0,
            "current_orders": 1000.0,
            "baseline_orders": 1000.0,
            "current_freight": 20000.0,
            "baseline_freight": 20000.0,
        }
    ]

    res = get_dimensional_breakdown(
        conn=mock_conn,
        metric="gmv",
        dimension="customer_state",
        current_start=date(2018, 5, 1),
        current_end=date(2018, 5, 31),
        baseline_start=date(2018, 4, 1),
        baseline_end=date(2018, 4, 30),
    )

    assert res.total_change == 0.0
    assert res.slices[0].contribution_percentage is None


def test_dimensional_breakdown_invalid_inputs() -> None:
    """Test validation errors for invalid dimensions or metrics."""
    mock_conn = MagicMock()

    with pytest.raises(ValueError, match="Unsupported dimension"):
        get_dimensional_breakdown(
            conn=mock_conn,
            metric="gmv",
            dimension="invalid_dim",
            current_start=date(2018, 5, 1),
            current_end=date(2018, 5, 31),
            baseline_start=date(2018, 4, 1),
            baseline_end=date(2018, 4, 30),
        )

    with pytest.raises(ValueError, match="Unsupported metric"):
        get_dimensional_breakdown(
            conn=mock_conn,
            metric="invalid_metric",
            dimension="customer_state",
            current_start=date(2018, 5, 1),
            current_end=date(2018, 5, 31),
            baseline_start=date(2018, 4, 1),
            baseline_end=date(2018, 4, 30),
        )
