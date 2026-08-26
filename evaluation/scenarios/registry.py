"""Canonical Benchmark Scenarios Registry for RootCause AI."""

from datetime import date

from evaluation.scenarios.models import GroundTruthRootCause, GroundTruthScenario

BENCHMARK_SCENARIOS: list[GroundTruthScenario] = [
    # Scenario 1: Warehouse / Fulfillment Capacity Contraction
    GroundTruthScenario(
        scenario_id="SCN-001",
        name="Warehouse Capacity Contraction",
        description=(
            "Warehouse fulfillment capacity decreases significantly during peak "
            "demand, triggering fulfillment bottlenecks, extended dispatch lead times, "
            "and regional delivery late rate spikes."
        ),
        primary_cause=GroundTruthRootCause(
            cause_id="logistics_fulfillment_bottleneck",
            dimension="delivery",
            dimension_value="late_delivery",
            causal_category="operational_mechanism",
            causal_mechanism="delivery",
            affected_dimension="customer_state",
            affected_value="SP",
            expected_contribution_pct=None,
        ),
        secondary_causes=[
            GroundTruthRootCause(
                cause_id="regional_geographic_concentration",
                dimension="customer_state",
                dimension_value="SP",
                causal_category="segment_concentration",
                causal_mechanism=None,
                affected_dimension="customer_state",
                affected_value="SP",
                expected_contribution_pct=None,
            )
        ],
        target_metric="late_delivery_rate_pct",
        anomaly_date=date(2017, 11, 24),
        comparison_days=7,
        expected_direction="increase",
        severity="critical",
        affected_dimensions=["delivery", "customer_state", "seller"],
        expected_evidence_signals=[
            "observed_late_delivery_rate > baseline_late_delivery_rate",
            "avg_delivery_days_change > 0",
        ],
        tags=["logistics", "fulfillment", "warehouse"],
    ),
    # Scenario 2: Marketing Spend Contraction
    GroundTruthScenario(
        scenario_id="SCN-002",
        name="Marketing Spend Contraction",
        description=(
            "Paid acquisition and performance marketing spend is throttled across "
            "major ad networks, causing a steep contraction in daily order volume "
            "while basket pricing remains neutral."
        ),
        primary_cause=GroundTruthRootCause(
            cause_id="order_volume_drop",
            dimension="order_volume",
            dimension_value=None,
            causal_category="macro_driver",
            causal_mechanism="order_volume",
            affected_dimension="product_category",
            affected_value="cama_mesa_banho",
            expected_contribution_pct=75.0,
            tolerance_pct=25.0,
        ),
        secondary_causes=[
            GroundTruthRootCause(
                cause_id="top_acquisition_category_drop",
                dimension="product_category",
                dimension_value="cama_mesa_banho",
                causal_category="segment_concentration",
                causal_mechanism=None,
                affected_dimension="product_category",
                affected_value="cama_mesa_banho",
                expected_contribution_pct=None,
            )
        ],
        target_metric="total_gmv",
        anomaly_date=date(2017, 11, 19),
        comparison_days=7,
        expected_direction="decrease",
        severity="critical",
        affected_dimensions=["order_volume", "product_category", "customer_state"],
        expected_evidence_signals=[
            "volume_contribution_pct > 50.0",
            "observed_orders < baseline_orders",
        ],
        tags=["marketing", "acquisition", "volume"],
    ),
    # Scenario 3: Product Pricing & Basket Shift
    GroundTruthScenario(
        scenario_id="SCN-003",
        name="Product Pricing & Basket Shift",
        description=(
            "Category-wide promotional discount depth is reduced, raising average "
            "order value and driving net revenue variation primarily through basket "
            "expansion rather than transaction volume."
        ),
        primary_cause=GroundTruthRootCause(
            cause_id="average_order_value_expansion",
            dimension="average_order_value",
            dimension_value=None,
            causal_category="macro_driver",
            causal_mechanism="average_order_value",
            affected_dimension="product_category",
            affected_value="relogios_presentes",
            expected_contribution_pct=60.0,
            tolerance_pct=25.0,
        ),
        secondary_causes=[
            GroundTruthRootCause(
                cause_id="high_ticket_category_shift",
                dimension="product_category",
                dimension_value="relogios_presentes",
                causal_category="segment_concentration",
                causal_mechanism=None,
                affected_dimension="product_category",
                affected_value="relogios_presentes",
                expected_contribution_pct=None,
            )
        ],
        target_metric="total_gmv",
        anomaly_date=date(2017, 11, 27),
        comparison_days=7,
        expected_direction="increase",
        severity="warning",
        affected_dimensions=["average_order_value", "product_category"],
        expected_evidence_signals=[
            "aov_contribution_pct > 40.0",
            "observed_aov > baseline_aov",
        ],
        tags=["pricing", "aov", "monetization"],
    ),
    # Scenario 4: Delivery Partner Performance Deterioration
    GroundTruthScenario(
        scenario_id="SCN-004",
        name="Delivery Partner Performance Deterioration",
        description=(
            "A major logistics carrier experiences carrier strikes and transit depot "
            "gridlock, causing shipment delays, customer friction, and late delivery "
            "rate degradation."
        ),
        primary_cause=GroundTruthRootCause(
            cause_id="carrier_sla_degradation",
            dimension="delivery",
            dimension_value="carrier_transit_delay",
            causal_category="operational_mechanism",
            causal_mechanism="delivery",
            affected_dimension="customer_state",
            affected_value="SP",
            expected_contribution_pct=None,
        ),
        secondary_causes=[
            GroundTruthRootCause(
                cause_id="customer_satisfaction_decline",
                dimension="avg_review_score",
                dimension_value=None,
                causal_category="operational_mechanism",
                causal_mechanism="avg_review_score",
                affected_dimension=None,
                affected_value=None,
                expected_contribution_pct=None,
            )
        ],
        target_metric="late_delivery_rate_pct",
        anomaly_date=date(2017, 11, 25),
        comparison_days=7,
        expected_direction="increase",
        severity="critical",
        affected_dimensions=["delivery", "customer_state"],
        expected_evidence_signals=[
            "observed_late_delivery_rate > baseline_late_delivery_rate"
        ],
        tags=["logistics", "carrier", "delivery_sla"],
    ),
    # Scenario 5: Payment Friction & Conversion Drop
    GroundTruthScenario(
        scenario_id="SCN-005",
        name="Payment Gateway Friction & Basket Contraction",
        description=(
            "Payment processing gateway latency and installment fee changes alter "
            "checkout basket composition, creating downward pressure on basket value."
        ),
        primary_cause=GroundTruthRootCause(
            cause_id="average_order_value_contraction",
            dimension="average_order_value",
            dimension_value=None,
            causal_category="macro_driver",
            causal_mechanism="average_order_value",
            affected_dimension=None,
            affected_value=None,
            expected_contribution_pct=45.0,
            tolerance_pct=25.0,
        ),
        secondary_causes=[
            GroundTruthRootCause(
                cause_id="order_volume_softening",
                dimension="order_volume",
                dimension_value=None,
                causal_category="macro_driver",
                causal_mechanism="order_volume",
                affected_dimension=None,
                affected_value=None,
                expected_contribution_pct=None,
            )
        ],
        target_metric="total_gmv",
        anomaly_date=date(2017, 11, 22),
        comparison_days=7,
        expected_direction="decrease",
        severity="warning",
        affected_dimensions=["average_order_value", "order_volume"],
        expected_evidence_signals=["aov_effect < 0", "observed_aov < baseline_aov"],
        tags=["payments", "conversion", "aov"],
    ),
    # Scenario 6: Customer Acquisition Demand Surge
    GroundTruthScenario(
        scenario_id="SCN-006",
        name="Customer Acquisition Demand Surge",
        description=(
            "A high-velocity viral campaign and shopping surge drives a "
            "massive order volume spike (almost 6x normal), with order count "
            "explaining the majority of the total revenue increase."
        ),
        primary_cause=GroundTruthRootCause(
            cause_id="order_volume_surge",
            dimension="order_volume",
            dimension_value=None,
            causal_category="macro_driver",
            causal_mechanism="order_volume",
            affected_dimension="customer_state",
            affected_value="SP",
            expected_contribution_pct=85.0,
            tolerance_pct=20.0,
        ),
        secondary_causes=[
            GroundTruthRootCause(
                cause_id="geographic_volume_hub_sp",
                dimension="customer_state",
                dimension_value="SP",
                causal_category="segment_concentration",
                causal_mechanism=None,
                affected_dimension="customer_state",
                affected_value="SP",
                expected_contribution_pct=32.0,
            )
        ],
        target_metric="total_gmv",
        anomaly_date=date(2017, 11, 24),
        comparison_days=7,
        expected_direction="increase",
        severity="critical",
        affected_dimensions=["order_volume", "customer_state", "product_category"],
        expected_evidence_signals=[
            "volume_contribution_pct > 60.0",
            "observed_orders > baseline_orders",
        ],
        tags=["acquisition", "volume", "black_friday"],
    ),
]


def get_scenario(scenario_id: str) -> GroundTruthScenario:
    """Retrieve a scenario by ID."""
    for s in BENCHMARK_SCENARIOS:
        if s.scenario_id.lower() == scenario_id.lower():
            return s
    raise KeyError(f"Scenario '{scenario_id}' not found in benchmark registry.")


def get_all_scenarios() -> list[GroundTruthScenario]:
    """Return all registered benchmark scenarios."""
    return list(BENCHMARK_SCENARIOS)
