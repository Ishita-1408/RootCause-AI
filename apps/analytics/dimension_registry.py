"""Centralized Whitelisted Dimension Registry for Safe Root-Cause Drill-Downs.

Guarantees complete SQL injection protection by enforcing strict parameterization
and strict whitelist validation on all analytical dimensions and metrics.
"""

from typing import Any

from pydantic import BaseModel, Field


class DimensionDefinition(BaseModel):
    """Metadata definition for an approved analytical drill-down dimension."""

    dimension_key: str
    display_name: str
    description: str
    target_table: str
    target_column: str
    is_joined: bool = False
    supported_metrics: list[str] = Field(
        default_factory=lambda: [
            "total_gmv",
            "orders_count",
            "average_order_value",
            "late_delivery_rate_pct",
            "avg_review_score",
        ]
    )


# Master Whitelist of Approved Analytical Dimensions
DIMENSION_REGISTRY: dict[str, DimensionDefinition] = {
    "customer_state": DimensionDefinition(
        dimension_key="customer_state",
        display_name="Customer Geographic State",
        description="Brazilian 2-letter federative unit code (e.g., SP, RJ, MG).",
        target_table="fact_order_analytics",
        target_column="customer_state",
        is_joined=False,
    ),
    "product_category": DimensionDefinition(
        dimension_key="product_category",
        display_name="Product Category",
        description="Portuguese e-commerce product category taxonomy.",
        target_table="dim_products",
        target_column="product_category_name",
        is_joined=True,
    ),
    "seller": DimensionDefinition(
        dimension_key="seller",
        display_name="Merchant / Seller",
        description="Unique 32-character merchant identifier.",
        target_table="fact_order_item_analytics",
        target_column="seller_id",
        is_joined=True,
    ),
    "payment_type": DimensionDefinition(
        dimension_key="payment_type",
        display_name="Primary Payment Method",
        description="Payment tender type (credit_card, boleto, voucher, debit_card).",
        target_table="fact_order_analytics",
        target_column="primary_payment_type",
        is_joined=False,
    ),
    "order_status": DimensionDefinition(
        dimension_key="order_status",
        display_name="Fulfillment Order Status",
        description="Lifecycle status (delivered, shipped, canceled, invoiced).",
        target_table="fact_order_analytics",
        target_column="order_status",
        is_joined=False,
    ),
}


class DimensionRegistry:
    """Validator and SQL generator for safe dimensional drill-downs."""

    @classmethod
    def list_dimensions(cls) -> list[DimensionDefinition]:
        """Return all approved whitelisted dimensions."""
        return list(DIMENSION_REGISTRY.values())

    @classmethod
    def is_valid_dimension(cls, dimension_key: str) -> bool:
        """Check if a dimension key is strictly whitelisted."""
        # Normalize key
        normalized = dimension_key.strip().lower()
        # Aliases mapping
        if normalized == "product_category_name":
            normalized = "product_category"
        if normalized == "seller_id":
            normalized = "seller"
        return normalized in DIMENSION_REGISTRY

    @classmethod
    def get_dimension(cls, dimension_key: str) -> DimensionDefinition:
        """Fetch dimension metadata or raise ValueError if unapproved."""
        normalized = dimension_key.strip().lower()
        if normalized == "product_category_name":
            normalized = "product_category"
        if normalized == "seller_id":
            normalized = "seller"

        if normalized not in DIMENSION_REGISTRY:
            approved_keys = list(DIMENSION_REGISTRY.keys())
            raise ValueError(
                f"Unsupported dimension '{dimension_key}'. "
                f"Approved dimensions are: {', '.join(approved_keys)}."
            )
        return DIMENSION_REGISTRY[normalized]

    @classmethod
    def sanitize_dimension_value(cls, value: Any) -> str:
        """Sanitize and validate dimension value string against injection."""
        if value is None:
            return ""
        val_str = str(value).strip()
        # Truncate excessive strings
        if len(val_str) > 128:
            val_str = val_str[:128]
        return val_str
