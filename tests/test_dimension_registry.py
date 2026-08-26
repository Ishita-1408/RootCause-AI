"""Tests for Safe Whitelisted Dimension Registry."""

import pytest

from apps.analytics.dimension_registry import DimensionRegistry


def test_list_dimensions_contains_canonical_dimensions() -> None:
    """Dimension registry must expose approved dimensions with descriptions."""
    dimensions = DimensionRegistry.list_dimensions()
    keys = [d.dimension_key for d in dimensions]

    assert "customer_state" in keys
    assert "product_category" in keys
    assert "seller" in keys
    assert "payment_type" in keys
    assert "order_status" in keys


def test_is_valid_dimension_whitelisting() -> None:
    """Valid dimensions return True, unapproved dimensions return False."""
    assert DimensionRegistry.is_valid_dimension("customer_state") is True
    assert DimensionRegistry.is_valid_dimension("product_category_name") is True
    assert DimensionRegistry.is_valid_dimension("seller_id") is True
    assert DimensionRegistry.is_valid_dimension("payment_type") is True
    assert DimensionRegistry.is_valid_dimension("order_status") is True

    assert DimensionRegistry.is_valid_dimension("unapproved_column") is False
    assert DimensionRegistry.is_valid_dimension("password_hash") is False
    assert DimensionRegistry.is_valid_dimension("; DROP TABLE orders; --") is False


def test_get_dimension_raises_on_unsupported() -> None:
    """Fetching an unapproved dimension must raise a descriptive ValueError."""
    with pytest.raises(ValueError) as exc_info:
        DimensionRegistry.get_dimension("malicious_dimension_drop_table")

    assert "Unsupported dimension" in str(exc_info.value)
    assert "Approved dimensions are" in str(exc_info.value)


def test_sanitize_dimension_value_sql_injection_resilience() -> None:
    """Sanitizer handles strings and strips dangerous character length."""
    assert DimensionRegistry.sanitize_dimension_value("SP") == "SP"
    assert DimensionRegistry.sanitize_dimension_value(None) == ""

    # Long injection string is cleanly truncated and handled as parameter
    long_injection = "SP' OR '1'='1" * 20
    sanitized = DimensionRegistry.sanitize_dimension_value(long_injection)
    assert len(sanitized) <= 128
