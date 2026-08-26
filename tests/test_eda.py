"""Unit tests for EDA analytical calculation helpers and KPI formulas."""

from scripts.analytics_queries import (
    QUERY_CUSTOMER_ANALYSIS,
    QUERY_DATA_QUALITY_CHECKS,
    QUERY_DELIVERY_OPERATIONS,
    QUERY_MONTHLY_SALES_ANALYSIS,
    QUERY_OVERALL_BUSINESS_KPIS,
    QUERY_PRODUCT_CATEGORY_ANALYSIS,
    QUERY_REVIEW_SATISFACTION,
    QUERY_SELLER_ANALYSIS,
)
from scripts.eda_helpers import (
    calculate_aov,
    calculate_rate_pct,
    calculate_repeat_rate,
    format_currency_brl,
    format_pct,
)


def test_calculate_aov() -> None:
    """Test Average Order Value calculation and edge cases."""
    assert calculate_aov(1000.0, 10) == 100.0
    assert calculate_aov(0.0, 10) == 0.0
    assert calculate_aov(500.0, 0) == 0.0
    assert calculate_aov(500.0, -1) == 0.0


def test_calculate_rate_pct() -> None:
    """Test percentage calculation helper and division by zero protection."""
    assert calculate_rate_pct(25, 100) == 25.0
    assert calculate_rate_pct(1, 3) == (1 / 3) * 100.0
    assert calculate_rate_pct(10, 0) == 0.0
    assert calculate_rate_pct(0, 50) == 0.0


def test_calculate_repeat_rate() -> None:
    """Test repeat customer calculation."""
    assert calculate_repeat_rate(100, 10) == 10.0
    assert calculate_repeat_rate(0, 0) == 0.0


def test_formatting_helpers() -> None:
    """Test currency and percentage string formatting."""
    assert format_currency_brl(1234.56) == "R$ 1,234.56"
    assert format_currency_brl(0) == "R$ 0.00"
    assert format_currency_brl(None) == "R$ 0.00"

    assert format_pct(15.678, 1) == "15.7%"
    assert format_pct(15.678, 2) == "15.68%"
    assert format_pct(None) == "0.0%"


def test_query_definitions_presence() -> None:
    """Verify that all core analytical SQL queries are defined and non-empty."""
    queries = [
        QUERY_OVERALL_BUSINESS_KPIS,
        QUERY_MONTHLY_SALES_ANALYSIS,
        QUERY_PRODUCT_CATEGORY_ANALYSIS,
        QUERY_SELLER_ANALYSIS,
        QUERY_CUSTOMER_ANALYSIS,
        QUERY_DELIVERY_OPERATIONS,
        QUERY_REVIEW_SATISFACTION,
        QUERY_DATA_QUALITY_CHECKS,
    ]
    for q in queries:
        assert isinstance(q, str)
        assert len(q.strip()) > 50
        assert "SELECT" in q
