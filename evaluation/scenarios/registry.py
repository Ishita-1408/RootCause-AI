"""Canonical Benchmark Scenarios Registry for RootCause AI.

Comprehensive Benchmark Suite: 115 Scenarios across 2016-2018 Olist Dataset.
Stratified by Difficulty: Easy, Medium, Hard.
Covering Metrics: total_gmv, orders_count, average_order_value,
late_delivery_rate_pct, avg_review_score.
"""

# ruff: noqa: E501  -- description strings in data registries may legitimately exceed 88 chars

from datetime import date

from evaluation.scenarios.models import GroundTruthRootCause, GroundTruthScenario

BENCHMARK_SCENARIOS: list[GroundTruthScenario] = [
    GroundTruthScenario(
        scenario_id="SCN-001",
        name="Warehouse Capacity Contraction",
        description=(
            "Warehouse fulfillment capacity decreases significantly during peak demand, triggering fulfillment bottlenecks, extended dispatch lead times, and regional delivery late rate spikes."
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
        distractor_causes=[
            "customer_state=SP",
            "seller_fulfillment_mix",
            "product_category=cama_mesa_banho",
        ],
        difficulty="easy",
        is_insufficient_evidence=False,
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
    GroundTruthScenario(
        scenario_id="SCN-002",
        name="Marketing Spend Contraction",
        description=(
            "Paid acquisition and performance marketing spend is throttled across major ad networks, causing a steep contraction in daily order volume while basket pricing remains neutral."
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
        distractor_causes=[
            "product_category=cama_mesa_banho",
            "customer_state=SP",
            "average_order_value_contraction",
        ],
        difficulty="easy",
        is_insufficient_evidence=False,
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
    GroundTruthScenario(
        scenario_id="SCN-003",
        name="Product Pricing & Basket Shift",
        description=(
            "Category-wide promotional discount depth is reduced, raising average order value and driving net revenue variation primarily through basket expansion rather than transaction volume."
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
        distractor_causes=[
            "order_volume_surge",
            "product_category=relogios_presentes",
            "customer_state=SP",
        ],
        difficulty="medium",
        is_insufficient_evidence=False,
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
    GroundTruthScenario(
        scenario_id="SCN-004",
        name="Delivery Partner Performance Deterioration",
        description=(
            "A major logistics carrier experiences carrier strikes and transit depot gridlock, causing shipment delays, customer friction, and late delivery rate degradation."
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
        distractor_causes=["customer_state=SP", "order_volume_spike", "seller_delay"],
        difficulty="easy",
        is_insufficient_evidence=False,
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
    GroundTruthScenario(
        scenario_id="SCN-005",
        name="Payment Gateway Friction & Basket Contraction",
        description=(
            "Payment processing gateway latency and installment fee changes alter checkout basket composition, creating downward pressure on basket value."
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
        distractor_causes=[
            "order_volume_drop",
            "customer_state=SP",
            "product_category=cama_mesa_banho",
        ],
        difficulty="medium",
        is_insufficient_evidence=False,
        target_metric="total_gmv",
        anomaly_date=date(2017, 11, 22),
        comparison_days=7,
        expected_direction="decrease",
        severity="warning",
        affected_dimensions=["average_order_value", "order_volume"],
        expected_evidence_signals=["aov_effect < 0", "observed_aov < baseline_aov"],
        tags=["payments", "conversion", "aov"],
    ),
    GroundTruthScenario(
        scenario_id="SCN-006",
        name="Customer Acquisition Demand Surge",
        description=(
            "A high-velocity viral campaign and shopping surge drives a massive order volume spike (almost 6x normal), with order count explaining the majority of the total revenue increase."
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
        distractor_causes=[
            "customer_state=SP",
            "product_category=cama_mesa_banho",
            "average_order_value_expansion",
        ],
        difficulty="easy",
        is_insufficient_evidence=False,
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
    GroundTruthScenario(
        scenario_id="SCN-007",
        name="New Year E-Commerce Volume Expansion",
        description=(
            "Post-holiday shopping resumption creates a significant order volume expansion across core retail states."
        ),
        primary_cause=GroundTruthRootCause(
            cause_id="order_volume_surge",
            dimension="order_volume",
            dimension_value=None,
            causal_category="macro_driver",
            causal_mechanism="order_volume",
            affected_dimension="customer_state",
            affected_value="SP",
            expected_contribution_pct=82.0,
        ),
        secondary_causes=[
            GroundTruthRootCause(
                cause_id="sp_volume_hub",
                dimension="customer_state",
                dimension_value="SP",
                causal_category="segment_concentration",
                causal_mechanism=None,
                affected_dimension="customer_state",
                affected_value="SP",
                expected_contribution_pct=40.0,
            )
        ],
        distractor_causes=["customer_state=SP", "average_order_value_expansion"],
        difficulty="easy",
        is_insufficient_evidence=False,
        target_metric="total_gmv",
        anomaly_date=date(2017, 1, 10),
        comparison_days=7,
        expected_direction="increase",
        severity="warning",
        affected_dimensions=["order_volume", "customer_state"],
        expected_evidence_signals=["volume_contribution_pct > 70.0"],
        tags=["seasonal", "volume"],
    ),
    GroundTruthScenario(
        scenario_id="SCN-008",
        name="High-End Watch Promotional Campaign",
        description=(
            "A high-ticket watch and luxury gifts promotion drives substantial basket expansion, dominating total GMV growth."
        ),
        primary_cause=GroundTruthRootCause(
            cause_id="average_order_value_expansion",
            dimension="average_order_value",
            dimension_value=None,
            causal_category="macro_driver",
            causal_mechanism="average_order_value",
            affected_dimension="product_category",
            affected_value="relogios_presentes",
            expected_contribution_pct=74.0,
        ),
        secondary_causes=[
            GroundTruthRootCause(
                cause_id="relogios_category_spike",
                dimension="product_category",
                dimension_value="relogios_presentes",
                causal_category="segment_concentration",
                causal_mechanism=None,
                affected_dimension="product_category",
                affected_value="relogios_presentes",
                expected_contribution_pct=47.4,
            )
        ],
        distractor_causes=[
            "product_category=relogios_presentes",
            "order_volume_surge",
            "customer_state=SP",
        ],
        difficulty="easy",
        is_insufficient_evidence=False,
        target_metric="total_gmv",
        anomaly_date=date(2017, 3, 15),
        comparison_days=7,
        expected_direction="increase",
        severity="warning",
        affected_dimensions=["average_order_value", "product_category"],
        expected_evidence_signals=["aov_contribution_pct > 50.0"],
        tags=["pricing", "promotions"],
    ),
    GroundTruthScenario(
        scenario_id="SCN-009",
        name="IT Hardware Premium Equipment Bulk Order",
        description=(
            "Significant acquisition of enterprise and consumer computing accessories elevates average transaction ticket."
        ),
        primary_cause=GroundTruthRootCause(
            cause_id="average_order_value_expansion",
            dimension="average_order_value",
            dimension_value=None,
            causal_category="macro_driver",
            causal_mechanism="average_order_value",
            affected_dimension="product_category",
            affected_value="informatica_acessorios",
            expected_contribution_pct=92.0,
        ),
        secondary_causes=[
            GroundTruthRootCause(
                cause_id="informatica_slice_surge",
                dimension="product_category",
                dimension_value="informatica_acessorios",
                causal_category="segment_concentration",
                causal_mechanism=None,
                affected_dimension="product_category",
                affected_value="informatica_acessorios",
                expected_contribution_pct=80.0,
            )
        ],
        distractor_causes=[
            "product_category=informatica_acessorios",
            "customer_state=SP",
        ],
        difficulty="easy",
        is_insufficient_evidence=False,
        target_metric="total_gmv",
        anomaly_date=date(2017, 5, 10),
        comparison_days=7,
        expected_direction="increase",
        severity="warning",
        affected_dimensions=["average_order_value", "product_category"],
        expected_evidence_signals=["aov_contribution_pct > 75.0"],
        tags=["b2b", "hardware"],
    ),
    GroundTruthScenario(
        scenario_id="SCN-010",
        name="Rio de Janeiro Regional Acquisition Shock",
        description=(
            "Targeted regional growth campaign in RJ triggers high revenue variance through combined volume and basket growth."
        ),
        primary_cause=GroundTruthRootCause(
            cause_id="order_volume_surge",
            dimension="order_volume",
            dimension_value=None,
            causal_category="macro_driver",
            causal_mechanism="order_volume",
            affected_dimension="customer_state",
            affected_value="RJ",
            expected_contribution_pct=54.9,
        ),
        secondary_causes=[
            GroundTruthRootCause(
                cause_id="rj_geographic_concentration",
                dimension="customer_state",
                dimension_value="RJ",
                causal_category="segment_concentration",
                causal_mechanism=None,
                affected_dimension="customer_state",
                affected_value="RJ",
                expected_contribution_pct=44.6,
            )
        ],
        distractor_causes=[
            "customer_state=RJ",
            "average_order_value_expansion",
            "customer_state=SP",
        ],
        difficulty="medium",
        is_insufficient_evidence=False,
        target_metric="total_gmv",
        anomaly_date=date(2017, 7, 18),
        comparison_days=7,
        expected_direction="increase",
        severity="warning",
        affected_dimensions=["order_volume", "customer_state"],
        expected_evidence_signals=["volume_contribution_pct > 40.0"],
        tags=["regional", "growth"],
    ),
    GroundTruthScenario(
        scenario_id="SCN-011",
        name="Mid-Month Category Mix Shift",
        description=(
            "Equal contributions from order contraction and basket adjustments create competing drivers for total revenue drop."
        ),
        primary_cause=GroundTruthRootCause(
            cause_id="order_volume_drop",
            dimension="order_volume",
            dimension_value=None,
            causal_category="macro_driver",
            causal_mechanism="order_volume",
            affected_dimension="customer_state",
            affected_value="SP",
            expected_contribution_pct=52.0,
        ),
        secondary_causes=[
            GroundTruthRootCause(
                cause_id="sp_volume_contraction",
                dimension="customer_state",
                dimension_value="SP",
                causal_category="segment_concentration",
                causal_mechanism=None,
                affected_dimension="customer_state",
                affected_value="SP",
                expected_contribution_pct=48.0,
            )
        ],
        distractor_causes=[
            "average_order_value_contraction",
            "customer_state=SP",
            "product_category=beleza_saude",
        ],
        difficulty="hard",
        is_insufficient_evidence=False,
        target_metric="total_gmv",
        anomaly_date=date(2017, 9, 20),
        comparison_days=7,
        expected_direction="decrease",
        severity="warning",
        affected_dimensions=["order_volume", "average_order_value"],
        expected_evidence_signals=["volume_contribution_pct > 45.0"],
        tags=["competing_drivers", "noise"],
    ),
    GroundTruthScenario(
        scenario_id="SCN-012",
        name="Post-Black Friday Demand Hangover",
        description=(
            "Severe drop in transaction volume following peak retail events leads to sharp revenue contraction."
        ),
        primary_cause=GroundTruthRootCause(
            cause_id="order_volume_drop",
            dimension="order_volume",
            dimension_value=None,
            causal_category="macro_driver",
            causal_mechanism="order_volume",
            affected_dimension="customer_state",
            affected_value="SP",
            expected_contribution_pct=88.0,
        ),
        secondary_causes=[
            GroundTruthRootCause(
                cause_id="sp_macro_drop",
                dimension="customer_state",
                dimension_value="SP",
                causal_category="segment_concentration",
                causal_mechanism=None,
                affected_dimension="customer_state",
                affected_value="SP",
                expected_contribution_pct=35.0,
            )
        ],
        distractor_causes=["customer_state=SP", "product_category=cama_mesa_banho"],
        difficulty="easy",
        is_insufficient_evidence=False,
        target_metric="total_gmv",
        anomaly_date=date(2017, 12, 6),
        comparison_days=7,
        expected_direction="decrease",
        severity="critical",
        affected_dimensions=["order_volume", "customer_state"],
        expected_evidence_signals=["volume_contribution_pct > 70.0"],
        tags=["seasonality", "contraction"],
    ),
    GroundTruthScenario(
        scenario_id="SCN-013",
        name="Christmas Last-Minute Gifting Surge",
        description=(
            "Late holiday gift buying triggers rapid volume surge across toys and consumer gifts."
        ),
        primary_cause=GroundTruthRootCause(
            cause_id="order_volume_surge",
            dimension="order_volume",
            dimension_value=None,
            causal_category="macro_driver",
            causal_mechanism="order_volume",
            affected_dimension="product_category",
            affected_value="brinquedos",
            expected_contribution_pct=78.0,
        ),
        secondary_causes=[
            GroundTruthRootCause(
                cause_id="toys_category_spike",
                dimension="product_category",
                dimension_value="brinquedos",
                causal_category="segment_concentration",
                causal_mechanism=None,
                affected_dimension="product_category",
                affected_value="brinquedos",
                expected_contribution_pct=38.0,
            )
        ],
        distractor_causes=["product_category=brinquedos", "customer_state=SP"],
        difficulty="easy",
        is_insufficient_evidence=False,
        target_metric="total_gmv",
        anomaly_date=date(2017, 12, 18),
        comparison_days=7,
        expected_direction="increase",
        severity="warning",
        affected_dimensions=["order_volume", "product_category"],
        expected_evidence_signals=["volume_contribution_pct > 60.0"],
        tags=["holiday", "gifting"],
    ),
    GroundTruthScenario(
        scenario_id="SCN-014",
        name="Q1 Clearance Sale AOV Contraction",
        description=(
            "Deep discount clearance sales lower average ticket price, causing revenue softening despite steady volume."
        ),
        primary_cause=GroundTruthRootCause(
            cause_id="average_order_value_contraction",
            dimension="average_order_value",
            dimension_value=None,
            causal_category="macro_driver",
            causal_mechanism="average_order_value",
            affected_dimension="product_category",
            affected_value="cama_mesa_banho",
            expected_contribution_pct=65.0,
        ),
        secondary_causes=[
            GroundTruthRootCause(
                cause_id="bed_bath_clearance",
                dimension="product_category",
                dimension_value="cama_mesa_banho",
                causal_category="segment_concentration",
                causal_mechanism=None,
                affected_dimension="product_category",
                affected_value="cama_mesa_banho",
                expected_contribution_pct=42.0,
            )
        ],
        distractor_causes=["order_volume_drop", "product_category=cama_mesa_banho"],
        difficulty="medium",
        is_insufficient_evidence=False,
        target_metric="total_gmv",
        anomaly_date=date(2018, 1, 24),
        comparison_days=7,
        expected_direction="decrease",
        severity="warning",
        affected_dimensions=["average_order_value", "product_category"],
        expected_evidence_signals=["aov_contribution_pct > 50.0"],
        tags=["discounting", "clearance"],
    ),
    GroundTruthScenario(
        scenario_id="SCN-015",
        name="Carnival Week Operational Softening",
        description=(
            "National holiday festivities lead to nationwide commercial pause, decreasing order volume."
        ),
        primary_cause=GroundTruthRootCause(
            cause_id="order_volume_drop",
            dimension="order_volume",
            dimension_value=None,
            causal_category="macro_driver",
            causal_mechanism="order_volume",
            affected_dimension="customer_state",
            affected_value="SP",
            expected_contribution_pct=84.0,
        ),
        secondary_causes=[
            GroundTruthRootCause(
                cause_id="sp_carnival_slowdown",
                dimension="customer_state",
                dimension_value="SP",
                causal_category="segment_concentration",
                causal_mechanism=None,
                affected_dimension="customer_state",
                affected_value="SP",
                expected_contribution_pct=40.0,
            )
        ],
        distractor_causes=["customer_state=SP", "customer_state=RJ"],
        difficulty="easy",
        is_insufficient_evidence=False,
        target_metric="total_gmv",
        anomaly_date=date(2018, 2, 14),
        comparison_days=7,
        expected_direction="decrease",
        severity="warning",
        affected_dimensions=["order_volume", "customer_state"],
        expected_evidence_signals=["volume_contribution_pct > 70.0"],
        tags=["holiday", "national"],
    ),
    GroundTruthScenario(
        scenario_id="SCN-016",
        name="Post-Carnival Recovery Surge",
        description=(
            "Commercial activity bounces back with elevated order placement across industrial and consumer sectors."
        ),
        primary_cause=GroundTruthRootCause(
            cause_id="order_volume_surge",
            dimension="order_volume",
            dimension_value=None,
            causal_category="macro_driver",
            causal_mechanism="order_volume",
            affected_dimension="customer_state",
            affected_value="SP",
            expected_contribution_pct=68.0,
        ),
        secondary_causes=[
            GroundTruthRootCause(
                cause_id="sp_post_holiday_rebound",
                dimension="customer_state",
                dimension_value="SP",
                causal_category="segment_concentration",
                causal_mechanism=None,
                affected_dimension="customer_state",
                affected_value="SP",
                expected_contribution_pct=36.0,
            )
        ],
        distractor_causes=["customer_state=SP", "average_order_value_expansion"],
        difficulty="medium",
        is_insufficient_evidence=False,
        target_metric="total_gmv",
        anomaly_date=date(2018, 2, 21),
        comparison_days=7,
        expected_direction="increase",
        severity="warning",
        affected_dimensions=["order_volume", "customer_state"],
        expected_evidence_signals=["volume_contribution_pct > 50.0"],
        tags=["rebound", "recovery"],
    ),
    GroundTruthScenario(
        scenario_id="SCN-017",
        name="Luxury Watch & Jewelry Basket Contraction",
        description=(
            "Drop in high-ticket luxury item orders depresses average order value and total GMV."
        ),
        primary_cause=GroundTruthRootCause(
            cause_id="average_order_value_contraction",
            dimension="average_order_value",
            dimension_value=None,
            causal_category="macro_driver",
            causal_mechanism="average_order_value",
            affected_dimension="product_category",
            affected_value="relogios_presentes",
            expected_contribution_pct=82.0,
        ),
        secondary_causes=[
            GroundTruthRootCause(
                cause_id="relogios_drop",
                dimension="product_category",
                dimension_value="relogios_presentes",
                causal_category="segment_concentration",
                causal_mechanism=None,
                affected_dimension="product_category",
                affected_value="relogios_presentes",
                expected_contribution_pct=47.9,
            )
        ],
        distractor_causes=["product_category=relogios_presentes", "order_volume_drop"],
        difficulty="easy",
        is_insufficient_evidence=False,
        target_metric="total_gmv",
        anomaly_date=date(2018, 3, 22),
        comparison_days=7,
        expected_direction="decrease",
        severity="warning",
        affected_dimensions=["average_order_value", "product_category"],
        expected_evidence_signals=["aov_contribution_pct > 70.0"],
        tags=["luxury", "basket"],
    ),
    GroundTruthScenario(
        scenario_id="SCN-018",
        name="Mother's Day Early Promotion Volume Wave",
        description=(
            "Pre-Mother's day marketing blitz accelerates early order intake across beauty, health, and fashion."
        ),
        primary_cause=GroundTruthRootCause(
            cause_id="order_volume_surge",
            dimension="order_volume",
            dimension_value=None,
            causal_category="macro_driver",
            causal_mechanism="order_volume",
            affected_dimension="product_category",
            affected_value="beleza_saude",
            expected_contribution_pct=76.0,
        ),
        secondary_causes=[
            GroundTruthRootCause(
                cause_id="beauty_category_surge",
                dimension="product_category",
                dimension_value="beleza_saude",
                causal_category="segment_concentration",
                causal_mechanism=None,
                affected_dimension="product_category",
                affected_value="beleza_saude",
                expected_contribution_pct=44.0,
            )
        ],
        distractor_causes=["product_category=beleza_saude", "customer_state=SP"],
        difficulty="easy",
        is_insufficient_evidence=False,
        target_metric="total_gmv",
        anomaly_date=date(2018, 5, 3),
        comparison_days=7,
        expected_direction="increase",
        severity="warning",
        affected_dimensions=["order_volume", "product_category"],
        expected_evidence_signals=["volume_contribution_pct > 60.0"],
        tags=["promotions", "seasonal"],
    ),
    GroundTruthScenario(
        scenario_id="SCN-019",
        name="Mother's Day Peak Order Volume Surge",
        description=(
            "Mother's Day week sales climax drives high order velocity across all southeastern states."
        ),
        primary_cause=GroundTruthRootCause(
            cause_id="order_volume_surge",
            dimension="order_volume",
            dimension_value=None,
            causal_category="macro_driver",
            causal_mechanism="order_volume",
            affected_dimension="customer_state",
            affected_value="SP",
            expected_contribution_pct=68.5,
        ),
        secondary_causes=[
            GroundTruthRootCause(
                cause_id="sp_volume_peak",
                dimension="customer_state",
                dimension_value="SP",
                causal_category="segment_concentration",
                causal_mechanism=None,
                affected_dimension="customer_state",
                affected_value="SP",
                expected_contribution_pct=49.4,
            )
        ],
        distractor_causes=["customer_state=SP", "average_order_value_expansion"],
        difficulty="medium",
        is_insufficient_evidence=False,
        target_metric="total_gmv",
        anomaly_date=date(2018, 5, 16),
        comparison_days=7,
        expected_direction="increase",
        severity="critical",
        affected_dimensions=["order_volume", "customer_state"],
        expected_evidence_signals=["volume_contribution_pct > 55.0"],
        tags=["mothers_day", "volume"],
    ),
    GroundTruthScenario(
        scenario_id="SCN-020",
        name="Heavy Freight Furniture Basket Expansion",
        description=(
            "Surge in high-value office and home furniture orders elevates average ticket size."
        ),
        primary_cause=GroundTruthRootCause(
            cause_id="average_order_value_expansion",
            dimension="average_order_value",
            dimension_value=None,
            causal_category="macro_driver",
            causal_mechanism="average_order_value",
            affected_dimension="product_category",
            affected_value="moveis_escritorio",
            expected_contribution_pct=62.0,
        ),
        secondary_causes=[
            GroundTruthRootCause(
                cause_id="office_furniture_spike",
                dimension="product_category",
                dimension_value="moveis_escritorio",
                causal_category="segment_concentration",
                causal_mechanism=None,
                affected_dimension="product_category",
                affected_value="moveis_escritorio",
                expected_contribution_pct=38.0,
            )
        ],
        distractor_causes=["product_category=moveis_escritorio", "order_volume_surge"],
        difficulty="medium",
        is_insufficient_evidence=False,
        target_metric="total_gmv",
        anomaly_date=date(2018, 6, 12),
        comparison_days=7,
        expected_direction="increase",
        severity="warning",
        affected_dimensions=["average_order_value", "product_category"],
        expected_evidence_signals=["aov_contribution_pct > 50.0"],
        tags=["furniture", "b2b"],
    ),
    GroundTruthScenario(
        scenario_id="SCN-021",
        name="Espirito Santo Regional Basket Shift",
        description=(
            "High-value commercial transactions in ES explain majority of positive GMV deviation."
        ),
        primary_cause=GroundTruthRootCause(
            cause_id="average_order_value_expansion",
            dimension="average_order_value",
            dimension_value=None,
            causal_category="macro_driver",
            causal_mechanism="average_order_value",
            affected_dimension="customer_state",
            affected_value="ES",
            expected_contribution_pct=68.1,
        ),
        secondary_causes=[
            GroundTruthRootCause(
                cause_id="es_state_spike",
                dimension="customer_state",
                dimension_value="ES",
                causal_category="segment_concentration",
                causal_mechanism=None,
                affected_dimension="customer_state",
                affected_value="ES",
                expected_contribution_pct=120.8,
            )
        ],
        distractor_causes=["customer_state=ES", "order_volume_surge"],
        difficulty="medium",
        is_insufficient_evidence=False,
        target_metric="total_gmv",
        anomaly_date=date(2018, 7, 25),
        comparison_days=7,
        expected_direction="increase",
        severity="warning",
        affected_dimensions=["average_order_value", "customer_state"],
        expected_evidence_signals=["aov_contribution_pct > 50.0"],
        tags=["regional", "basket"],
    ),
    GroundTruthScenario(
        scenario_id="SCN-022",
        name="Sports & Leisure Equipment Mid-Winter Surge",
        description=(
            "Winter fitness campaign boosts order volume across sports equipment category."
        ),
        primary_cause=GroundTruthRootCause(
            cause_id="order_volume_surge",
            dimension="order_volume",
            dimension_value=None,
            causal_category="macro_driver",
            causal_mechanism="order_volume",
            affected_dimension="product_category",
            affected_value="esporte_lazer",
            expected_contribution_pct=75.0,
        ),
        secondary_causes=[
            GroundTruthRootCause(
                cause_id="sports_category_spike",
                dimension="product_category",
                dimension_value="esporte_lazer",
                causal_category="segment_concentration",
                causal_mechanism=None,
                affected_dimension="product_category",
                affected_value="esporte_lazer",
                expected_contribution_pct=41.0,
            )
        ],
        distractor_causes=["product_category=esporte_lazer", "customer_state=SP"],
        difficulty="easy",
        is_insufficient_evidence=False,
        target_metric="total_gmv",
        anomaly_date=date(2018, 8, 8),
        comparison_days=7,
        expected_direction="increase",
        severity="warning",
        affected_dimensions=["order_volume", "product_category"],
        expected_evidence_signals=["volume_contribution_pct > 60.0"],
        tags=["fitness", "seasonal"],
    ),
    GroundTruthScenario(
        scenario_id="SCN-023",
        name="Diffuse Multi-Category Revenue Contraction",
        description=(
            "Broad softening across multiple unrelated categories with weak single-driver concentration."
        ),
        primary_cause=GroundTruthRootCause(
            cause_id="order_volume_drop",
            dimension="order_volume",
            dimension_value=None,
            causal_category="macro_driver",
            causal_mechanism="order_volume",
            affected_dimension=None,
            affected_value=None,
            expected_contribution_pct=51.0,
        ),
        secondary_causes=[],
        distractor_causes=[
            "average_order_value_contraction",
            "product_category=beleza_saude",
            "product_category=cama_mesa_banho",
        ],
        difficulty="hard",
        is_insufficient_evidence=True,
        target_metric="total_gmv",
        anomaly_date=date(2018, 8, 20),
        comparison_days=7,
        expected_direction="decrease",
        severity="warning",
        affected_dimensions=["order_volume", "product_category"],
        expected_evidence_signals=["volume_contribution_pct > 45.0"],
        tags=["diffuse", "multi_category"],
    ),
    GroundTruthScenario(
        scenario_id="SCN-024",
        name="National Campaign Traffic Wave",
        description=(
            "Aggressive digital acquisition campaign boosts nationwide order counts significantly."
        ),
        primary_cause=GroundTruthRootCause(
            cause_id="order_volume_surge",
            dimension="order_volume",
            dimension_value=None,
            causal_category="macro_driver",
            causal_mechanism="order_volume",
            affected_dimension="customer_state",
            affected_value="SP",
            expected_contribution_pct=80.0,
        ),
        secondary_causes=[
            GroundTruthRootCause(
                cause_id="sp_order_volume_hub",
                dimension="customer_state",
                dimension_value="SP",
                causal_category="segment_concentration",
                causal_mechanism=None,
                affected_dimension="customer_state",
                affected_value="SP",
                expected_contribution_pct=42.0,
            )
        ],
        distractor_causes=["customer_state=SP", "customer_state=RJ"],
        difficulty="easy",
        is_insufficient_evidence=False,
        target_metric="orders_count",
        anomaly_date=date(2017, 1, 26),
        comparison_days=7,
        expected_direction="increase",
        severity="warning",
        affected_dimensions=["order_volume", "customer_state"],
        expected_evidence_signals=["observed_orders > baseline_orders"],
        tags=["orders", "traffic"],
    ),
    GroundTruthScenario(
        scenario_id="SCN-025",
        name="Checkout Flow Performance Degradation",
        description=(
            "Mobile app checkout bug depresses total completed orders across primary state hubs."
        ),
        primary_cause=GroundTruthRootCause(
            cause_id="order_volume_drop",
            dimension="order_volume",
            dimension_value=None,
            causal_category="macro_driver",
            causal_mechanism="order_volume",
            affected_dimension="customer_state",
            affected_value="SP",
            expected_contribution_pct=85.0,
        ),
        secondary_causes=[
            GroundTruthRootCause(
                cause_id="sp_checkout_friction",
                dimension="customer_state",
                dimension_value="SP",
                causal_category="segment_concentration",
                causal_mechanism=None,
                affected_dimension="customer_state",
                affected_value="SP",
                expected_contribution_pct=44.0,
            )
        ],
        distractor_causes=["customer_state=SP", "customer_state=MG"],
        difficulty="easy",
        is_insufficient_evidence=False,
        target_metric="orders_count",
        anomaly_date=date(2017, 2, 8),
        comparison_days=7,
        expected_direction="decrease",
        severity="critical",
        affected_dimensions=["order_volume", "customer_state"],
        expected_evidence_signals=["observed_orders < baseline_orders"],
        tags=["checkout", "friction"],
    ),
    GroundTruthScenario(
        scenario_id="SCN-026",
        name="Consumer Tech Discount Flash Sale",
        description=(
            "Flash promotion on phone accessories generates heavy order transaction volume."
        ),
        primary_cause=GroundTruthRootCause(
            cause_id="order_volume_surge",
            dimension="order_volume",
            dimension_value=None,
            causal_category="macro_driver",
            causal_mechanism="order_volume",
            affected_dimension="product_category",
            affected_value="telefonia",
            expected_contribution_pct=78.0,
        ),
        secondary_causes=[
            GroundTruthRootCause(
                cause_id="telecom_volume_surge",
                dimension="product_category",
                dimension_value="telefonia",
                causal_category="segment_concentration",
                causal_mechanism=None,
                affected_dimension="product_category",
                affected_value="telefonia",
                expected_contribution_pct=45.0,
            )
        ],
        distractor_causes=["product_category=telefonia", "customer_state=SP"],
        difficulty="easy",
        is_insufficient_evidence=False,
        target_metric="orders_count",
        anomaly_date=date(2017, 4, 12),
        comparison_days=7,
        expected_direction="increase",
        severity="warning",
        affected_dimensions=["order_volume", "product_category"],
        expected_evidence_signals=["observed_orders > baseline_orders"],
        tags=["flash_sale", "telecom"],
    ),
    GroundTruthScenario(
        scenario_id="SCN-027",
        name="Minas Gerais Regional Adoption Wave",
        description=(
            "Targeted localized expansion leads to sharp rise in orders originating in MG."
        ),
        primary_cause=GroundTruthRootCause(
            cause_id="order_volume_surge",
            dimension="order_volume",
            dimension_value=None,
            causal_category="macro_driver",
            causal_mechanism="order_volume",
            affected_dimension="customer_state",
            affected_value="MG",
            expected_contribution_pct=64.0,
        ),
        secondary_causes=[
            GroundTruthRootCause(
                cause_id="mg_regional_adoption",
                dimension="customer_state",
                dimension_value="MG",
                causal_category="segment_concentration",
                causal_mechanism=None,
                affected_dimension="customer_state",
                affected_value="MG",
                expected_contribution_pct=39.0,
            )
        ],
        distractor_causes=["customer_state=MG", "customer_state=SP"],
        difficulty="medium",
        is_insufficient_evidence=False,
        target_metric="orders_count",
        anomaly_date=date(2017, 6, 7),
        comparison_days=7,
        expected_direction="increase",
        severity="warning",
        affected_dimensions=["order_volume", "customer_state"],
        expected_evidence_signals=["observed_orders > baseline_orders"],
        tags=["regional", "expansion"],
    ),
    GroundTruthScenario(
        scenario_id="SCN-028",
        name="Parana Consumer Activity Acceleration",
        description=(
            "Accelerating order counts in southern state of PR driving regional volume expansion."
        ),
        primary_cause=GroundTruthRootCause(
            cause_id="order_volume_surge",
            dimension="order_volume",
            dimension_value=None,
            causal_category="macro_driver",
            causal_mechanism="order_volume",
            affected_dimension="customer_state",
            affected_value="PR",
            expected_contribution_pct=62.0,
        ),
        secondary_causes=[
            GroundTruthRootCause(
                cause_id="pr_regional_surge",
                dimension="customer_state",
                dimension_value="PR",
                causal_category="segment_concentration",
                causal_mechanism=None,
                affected_dimension="customer_state",
                affected_value="PR",
                expected_contribution_pct=35.0,
            )
        ],
        distractor_causes=["customer_state=PR", "customer_state=SP"],
        difficulty="medium",
        is_insufficient_evidence=False,
        target_metric="orders_count",
        anomaly_date=date(2017, 8, 15),
        comparison_days=7,
        expected_direction="increase",
        severity="warning",
        affected_dimensions=["order_volume", "customer_state"],
        expected_evidence_signals=["observed_orders > baseline_orders"],
        tags=["regional", "south"],
    ),
    GroundTruthScenario(
        scenario_id="SCN-029",
        name="Home & Bath Essentials Weekly Spike",
        description=(
            "Household essentials promotional catalog drives heavy repeat order placement."
        ),
        primary_cause=GroundTruthRootCause(
            cause_id="order_volume_surge",
            dimension="order_volume",
            dimension_value=None,
            causal_category="macro_driver",
            causal_mechanism="order_volume",
            affected_dimension="product_category",
            affected_value="cama_mesa_banho",
            expected_contribution_pct=77.0,
        ),
        secondary_causes=[
            GroundTruthRootCause(
                cause_id="bed_bath_volume_driver",
                dimension="product_category",
                dimension_value="cama_mesa_banho",
                causal_category="segment_concentration",
                causal_mechanism=None,
                affected_dimension="product_category",
                affected_value="cama_mesa_banho",
                expected_contribution_pct=48.0,
            )
        ],
        distractor_causes=["product_category=cama_mesa_banho", "customer_state=SP"],
        difficulty="easy",
        is_insufficient_evidence=False,
        target_metric="orders_count",
        anomaly_date=date(2017, 10, 18),
        comparison_days=7,
        expected_direction="increase",
        severity="warning",
        affected_dimensions=["order_volume", "product_category"],
        expected_evidence_signals=["observed_orders > baseline_orders"],
        tags=["home", "catalog"],
    ),
    GroundTruthScenario(
        scenario_id="SCN-030",
        name="Southern Logistics Bottleneck Order Dampening",
        description=(
            "Regional transportation blockades suppress order intake across southern states."
        ),
        primary_cause=GroundTruthRootCause(
            cause_id="order_volume_drop",
            dimension="order_volume",
            dimension_value=None,
            causal_category="macro_driver",
            causal_mechanism="order_volume",
            affected_dimension="customer_state",
            affected_value="RS",
            expected_contribution_pct=58.0,
        ),
        secondary_causes=[
            GroundTruthRootCause(
                cause_id="rs_order_slowdown",
                dimension="customer_state",
                dimension_value="RS",
                causal_category="segment_concentration",
                causal_mechanism=None,
                affected_dimension="customer_state",
                affected_value="RS",
                expected_contribution_pct=34.0,
            )
        ],
        distractor_causes=["customer_state=RS", "customer_state=SC", "delivery"],
        difficulty="medium",
        is_insufficient_evidence=False,
        target_metric="orders_count",
        anomaly_date=date(2018, 3, 7),
        comparison_days=7,
        expected_direction="decrease",
        severity="warning",
        affected_dimensions=["order_volume", "customer_state"],
        expected_evidence_signals=["observed_orders < baseline_orders"],
        tags=["regional", "logistics"],
    ),
    GroundTruthScenario(
        scenario_id="SCN-031",
        name="Garden & Outdoor Spring Category Lift",
        description=(
            "Spring weather shift boosts transaction frequency in garden and outdoor furnishings."
        ),
        primary_cause=GroundTruthRootCause(
            cause_id="order_volume_surge",
            dimension="order_volume",
            dimension_value=None,
            causal_category="macro_driver",
            causal_mechanism="order_volume",
            affected_dimension="product_category",
            affected_value="ferramentas_jardim",
            expected_contribution_pct=65.0,
        ),
        secondary_causes=[
            GroundTruthRootCause(
                cause_id="garden_volume_lift",
                dimension="product_category",
                dimension_value="ferramentas_jardim",
                causal_category="segment_concentration",
                causal_mechanism=None,
                affected_dimension="product_category",
                affected_value="ferramentas_jardim",
                expected_contribution_pct=37.0,
            )
        ],
        distractor_causes=["product_category=ferramentas_jardim", "customer_state=SP"],
        difficulty="medium",
        is_insufficient_evidence=False,
        target_metric="orders_count",
        anomaly_date=date(2018, 4, 18),
        comparison_days=7,
        expected_direction="increase",
        severity="warning",
        affected_dimensions=["order_volume", "product_category"],
        expected_evidence_signals=["observed_orders > baseline_orders"],
        tags=["outdoor", "seasonal"],
    ),
    GroundTruthScenario(
        scenario_id="SCN-032",
        name="Health & Wellness Loyalty Promotion",
        description=(
            "Loyalty program re-engagement emails produce significant order count spike in vitamins and health."
        ),
        primary_cause=GroundTruthRootCause(
            cause_id="order_volume_surge",
            dimension="order_volume",
            dimension_value=None,
            causal_category="macro_driver",
            causal_mechanism="order_volume",
            affected_dimension="product_category",
            affected_value="beleza_saude",
            expected_contribution_pct=79.0,
        ),
        secondary_causes=[
            GroundTruthRootCause(
                cause_id="health_loyalty_lift",
                dimension="product_category",
                dimension_value="beleza_saude",
                causal_category="segment_concentration",
                causal_mechanism=None,
                affected_dimension="product_category",
                affected_value="beleza_saude",
                expected_contribution_pct=46.0,
            )
        ],
        distractor_causes=["product_category=beleza_saude", "customer_state=SP"],
        difficulty="easy",
        is_insufficient_evidence=False,
        target_metric="orders_count",
        anomaly_date=date(2018, 6, 25),
        comparison_days=7,
        expected_direction="increase",
        severity="warning",
        affected_dimensions=["order_volume", "product_category"],
        expected_evidence_signals=["observed_orders > baseline_orders"],
        tags=["loyalty", "health"],
    ),
    GroundTruthScenario(
        scenario_id="SCN-033",
        name="Consumer Electronics High Ticket Promotion",
        description=(
            "Televisions and high-end audio hardware campaign expands average ticket size substantially."
        ),
        primary_cause=GroundTruthRootCause(
            cause_id="average_order_value_expansion",
            dimension="average_order_value",
            dimension_value=None,
            causal_category="macro_driver",
            causal_mechanism="average_order_value",
            affected_dimension="product_category",
            affected_value="eletronicos",
            expected_contribution_pct=85.0,
        ),
        secondary_causes=[
            GroundTruthRootCause(
                cause_id="electronics_ticket_surge",
                dimension="product_category",
                dimension_value="eletronicos",
                causal_category="segment_concentration",
                causal_mechanism=None,
                affected_dimension="product_category",
                affected_value="eletronicos",
                expected_contribution_pct=52.0,
            )
        ],
        distractor_causes=["product_category=eletronicos", "order_volume_surge"],
        difficulty="easy",
        is_insufficient_evidence=False,
        target_metric="average_order_value",
        anomaly_date=date(2017, 2, 22),
        comparison_days=7,
        expected_direction="increase",
        severity="warning",
        affected_dimensions=["average_order_value", "product_category"],
        expected_evidence_signals=["observed_aov > baseline_aov"],
        tags=["electronics", "ticket"],
    ),
    GroundTruthScenario(
        scenario_id="SCN-034",
        name="Small Ticket Stationery Basket Compression",
        description=(
            "Heavy back-to-school small accessories promotion reduces basket average spend."
        ),
        primary_cause=GroundTruthRootCause(
            cause_id="average_order_value_contraction",
            dimension="average_order_value",
            dimension_value=None,
            causal_category="macro_driver",
            causal_mechanism="average_order_value",
            affected_dimension="product_category",
            affected_value="papelaria",
            expected_contribution_pct=78.0,
        ),
        secondary_causes=[
            GroundTruthRootCause(
                cause_id="stationery_small_ticket",
                dimension="product_category",
                dimension_value="papelaria",
                causal_category="segment_concentration",
                causal_mechanism=None,
                affected_dimension="product_category",
                affected_value="papelaria",
                expected_contribution_pct=45.0,
            )
        ],
        distractor_causes=["product_category=papelaria", "order_volume_surge"],
        difficulty="easy",
        is_insufficient_evidence=False,
        target_metric="average_order_value",
        anomaly_date=date(2017, 3, 28),
        comparison_days=7,
        expected_direction="decrease",
        severity="warning",
        affected_dimensions=["average_order_value", "product_category"],
        expected_evidence_signals=["observed_aov < baseline_aov"],
        tags=["back_to_school", "discount"],
    ),
    GroundTruthScenario(
        scenario_id="SCN-035",
        name="Musical Instruments Premium Bundle Shift",
        description=(
            "Sale of professional musical instruments lifts overall storewide basket spend."
        ),
        primary_cause=GroundTruthRootCause(
            cause_id="average_order_value_expansion",
            dimension="average_order_value",
            dimension_value=None,
            causal_category="macro_driver",
            causal_mechanism="average_order_value",
            affected_dimension="product_category",
            affected_value="instrumentos_musicais",
            expected_contribution_pct=68.0,
        ),
        secondary_causes=[
            GroundTruthRootCause(
                cause_id="instruments_high_spend",
                dimension="product_category",
                dimension_value="instrumentos_musicais",
                causal_category="segment_concentration",
                causal_mechanism=None,
                affected_dimension="product_category",
                affected_value="instrumentos_musicais",
                expected_contribution_pct=41.0,
            )
        ],
        distractor_causes=[
            "product_category=instrumentos_musicais",
            "order_volume_drop",
        ],
        difficulty="medium",
        is_insufficient_evidence=False,
        target_metric="average_order_value",
        anomaly_date=date(2017, 4, 25),
        comparison_days=7,
        expected_direction="increase",
        severity="warning",
        affected_dimensions=["average_order_value", "product_category"],
        expected_evidence_signals=["observed_aov > baseline_aov"],
        tags=["niche", "instruments"],
    ),
    GroundTruthScenario(
        scenario_id="SCN-036",
        name="Automotive Parts Bulk Purchase Wave",
        description=(
            "Commercial garage multi-item tire and mechanical parts orders increase average order size."
        ),
        primary_cause=GroundTruthRootCause(
            cause_id="average_order_value_expansion",
            dimension="average_order_value",
            dimension_value=None,
            causal_category="macro_driver",
            causal_mechanism="average_order_value",
            affected_dimension="product_category",
            affected_value="automotivo",
            expected_contribution_pct=66.0,
        ),
        secondary_causes=[
            GroundTruthRootCause(
                cause_id="auto_parts_aov_lift",
                dimension="product_category",
                dimension_value="automotivo",
                causal_category="segment_concentration",
                causal_mechanism=None,
                affected_dimension="product_category",
                affected_value="automotivo",
                expected_contribution_pct=39.0,
            )
        ],
        distractor_causes=["product_category=automotivo", "customer_state=SP"],
        difficulty="medium",
        is_insufficient_evidence=False,
        target_metric="average_order_value",
        anomaly_date=date(2017, 6, 20),
        comparison_days=7,
        expected_direction="increase",
        severity="warning",
        affected_dimensions=["average_order_value", "product_category"],
        expected_evidence_signals=["observed_aov > baseline_aov"],
        tags=["automotive", "b2b"],
    ),
    GroundTruthScenario(
        scenario_id="SCN-037",
        name="Baby Products Essentials Bundle Promotion",
        description=(
            "Discounted bundles for infant formula and nursery goods drive down individual item pricing."
        ),
        primary_cause=GroundTruthRootCause(
            cause_id="average_order_value_contraction",
            dimension="average_order_value",
            dimension_value=None,
            causal_category="macro_driver",
            causal_mechanism="average_order_value",
            affected_dimension="product_category",
            affected_value="bebes",
            expected_contribution_pct=74.0,
        ),
        secondary_causes=[
            GroundTruthRootCause(
                cause_id="baby_products_bundle_discount",
                dimension="product_category",
                dimension_value="bebes",
                causal_category="segment_concentration",
                causal_mechanism=None,
                affected_dimension="product_category",
                affected_value="bebes",
                expected_contribution_pct=43.0,
            )
        ],
        distractor_causes=["product_category=bebes", "order_volume_surge"],
        difficulty="easy",
        is_insufficient_evidence=False,
        target_metric="average_order_value",
        anomaly_date=date(2017, 8, 2),
        comparison_days=7,
        expected_direction="decrease",
        severity="warning",
        affected_dimensions=["average_order_value", "product_category"],
        expected_evidence_signals=["observed_aov < baseline_aov"],
        tags=["nursery", "discount"],
    ),
    GroundTruthScenario(
        scenario_id="SCN-038",
        name="IT Computer Hardware Institutional Orders",
        description=(
            "Bulk server and networking gear orders create high average transaction ticket."
        ),
        primary_cause=GroundTruthRootCause(
            cause_id="average_order_value_expansion",
            dimension="average_order_value",
            dimension_value=None,
            causal_category="macro_driver",
            causal_mechanism="average_order_value",
            affected_dimension="product_category",
            affected_value="informatica_acessorios",
            expected_contribution_pct=88.0,
        ),
        secondary_causes=[
            GroundTruthRootCause(
                cause_id="it_hardware_bulk_lift",
                dimension="product_category",
                dimension_value="informatica_acessorios",
                causal_category="segment_concentration",
                causal_mechanism=None,
                affected_dimension="product_category",
                affected_value="informatica_acessorios",
                expected_contribution_pct=56.0,
            )
        ],
        distractor_causes=[
            "product_category=informatica_acessorios",
            "customer_state=SP",
        ],
        difficulty="easy",
        is_insufficient_evidence=False,
        target_metric="average_order_value",
        anomaly_date=date(2017, 10, 4),
        comparison_days=7,
        expected_direction="increase",
        severity="critical",
        affected_dimensions=["average_order_value", "product_category"],
        expected_evidence_signals=["observed_aov > baseline_aov"],
        tags=["enterprise", "hardware"],
    ),
    GroundTruthScenario(
        scenario_id="SCN-039",
        name="Winter Heating & Home Appliance Lift",
        description=(
            "Appliance purchases during seasonal cold front drive average order values higher."
        ),
        primary_cause=GroundTruthRootCause(
            cause_id="average_order_value_expansion",
            dimension="average_order_value",
            dimension_value=None,
            causal_category="macro_driver",
            causal_mechanism="average_order_value",
            affected_dimension="product_category",
            affected_value="eletrodomesticos",
            expected_contribution_pct=67.0,
        ),
        secondary_causes=[
            GroundTruthRootCause(
                cause_id="appliances_aov_boost",
                dimension="product_category",
                dimension_value="eletrodomesticos",
                causal_category="segment_concentration",
                causal_mechanism=None,
                affected_dimension="product_category",
                affected_value="eletrodomesticos",
                expected_contribution_pct=40.0,
            )
        ],
        distractor_causes=["product_category=eletrodomesticos", "order_volume_surge"],
        difficulty="medium",
        is_insufficient_evidence=False,
        target_metric="average_order_value",
        anomaly_date=date(2018, 5, 29),
        comparison_days=7,
        expected_direction="increase",
        severity="warning",
        affected_dimensions=["average_order_value", "product_category"],
        expected_evidence_signals=["observed_aov > baseline_aov"],
        tags=["appliances", "winter"],
    ),
    GroundTruthScenario(
        scenario_id="SCN-040",
        name="Industrial Machinery Specialized Equipment",
        description=(
            "Specialized construction tool purchases create noticeable positive skew in basket value."
        ),
        primary_cause=GroundTruthRootCause(
            cause_id="average_order_value_expansion",
            dimension="average_order_value",
            dimension_value=None,
            causal_category="macro_driver",
            causal_mechanism="average_order_value",
            affected_dimension="product_category",
            affected_value="construcao_ferramentas_construcao",
            expected_contribution_pct=80.0,
        ),
        secondary_causes=[
            GroundTruthRootCause(
                cause_id="construction_tools_spike",
                dimension="product_category",
                dimension_value="construcao_ferramentas_construcao",
                causal_category="segment_concentration",
                causal_mechanism=None,
                affected_dimension="product_category",
                affected_value="construcao_ferramentas_construcao",
                expected_contribution_pct=49.0,
            )
        ],
        distractor_causes=[
            "product_category=construcao_ferramentas_construcao",
            "customer_state=SP",
        ],
        difficulty="easy",
        is_insufficient_evidence=False,
        target_metric="average_order_value",
        anomaly_date=date(2018, 7, 16),
        comparison_days=7,
        expected_direction="increase",
        severity="warning",
        affected_dimensions=["average_order_value", "product_category"],
        expected_evidence_signals=["observed_aov > baseline_aov"],
        tags=["industrial", "tools"],
    ),
    GroundTruthScenario(
        scenario_id="SCN-041",
        name="Heavy Rainfall Coastal Transit Gridlock",
        description=(
            "Flooding and highway closures along the BR-101 transit corridor delay freight dispatches."
        ),
        primary_cause=GroundTruthRootCause(
            cause_id="carrier_sla_degradation",
            dimension="delivery",
            dimension_value="carrier_transit_delay",
            causal_category="operational_mechanism",
            causal_mechanism="delivery",
            affected_dimension="customer_state",
            affected_value="RJ",
            expected_contribution_pct=None,
        ),
        secondary_causes=[
            GroundTruthRootCause(
                cause_id="rj_flood_delays",
                dimension="customer_state",
                dimension_value="RJ",
                causal_category="segment_concentration",
                causal_mechanism=None,
                affected_dimension="customer_state",
                affected_value="RJ",
                expected_contribution_pct=None,
            )
        ],
        distractor_causes=[
            "customer_state=RJ",
            "customer_state=SP",
            "seller_dispatch_delay",
        ],
        difficulty="easy",
        is_insufficient_evidence=False,
        target_metric="late_delivery_rate_pct",
        anomaly_date=date(2017, 3, 5),
        comparison_days=7,
        expected_direction="increase",
        severity="critical",
        affected_dimensions=["delivery", "customer_state"],
        expected_evidence_signals=[
            "observed_late_delivery_rate > baseline_late_delivery_rate"
        ],
        tags=["weather", "logistics"],
    ),
    GroundTruthScenario(
        scenario_id="SCN-042",
        name="Postal Carrier Operational Backlog",
        description=(
            "National postal distribution center union work-to-rule slowdown inflates late delivery percentages."
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
                cause_id="sp_postal_slowdown",
                dimension="customer_state",
                dimension_value="SP",
                causal_category="segment_concentration",
                causal_mechanism=None,
                affected_dimension="customer_state",
                affected_value="SP",
                expected_contribution_pct=None,
            )
        ],
        distractor_causes=["customer_state=SP", "seller_dispatch_delay"],
        difficulty="easy",
        is_insufficient_evidence=False,
        target_metric="late_delivery_rate_pct",
        anomaly_date=date(2017, 5, 23),
        comparison_days=7,
        expected_direction="increase",
        severity="critical",
        affected_dimensions=["delivery", "customer_state"],
        expected_evidence_signals=[
            "observed_late_delivery_rate > baseline_late_delivery_rate"
        ],
        tags=["postal", "carrier"],
    ),
    GroundTruthScenario(
        scenario_id="SCN-043",
        name="Northeast Hub Cross-Dock Congestion",
        description=(
            "Freight transfers in northeastern distribution hubs back up, elevating regional delay rates."
        ),
        primary_cause=GroundTruthRootCause(
            cause_id="carrier_sla_degradation",
            dimension="delivery",
            dimension_value="carrier_transit_delay",
            causal_category="operational_mechanism",
            causal_mechanism="delivery",
            affected_dimension="customer_state",
            affected_value="BA",
            expected_contribution_pct=None,
        ),
        secondary_causes=[
            GroundTruthRootCause(
                cause_id="ba_hub_congestion",
                dimension="customer_state",
                dimension_value="BA",
                causal_category="segment_concentration",
                causal_mechanism=None,
                affected_dimension="customer_state",
                affected_value="BA",
                expected_contribution_pct=None,
            )
        ],
        distractor_causes=["customer_state=BA", "customer_state=PE"],
        difficulty="medium",
        is_insufficient_evidence=False,
        target_metric="late_delivery_rate_pct",
        anomaly_date=date(2017, 8, 29),
        comparison_days=7,
        expected_direction="increase",
        severity="warning",
        affected_dimensions=["delivery", "customer_state"],
        expected_evidence_signals=[
            "observed_late_delivery_rate > baseline_late_delivery_rate"
        ],
        tags=["regional", "cross_dock"],
    ),
    GroundTruthScenario(
        scenario_id="SCN-044",
        name="Post-Holiday Logistics Sorting Overload",
        description=(
            "Huge shipment volumes from holiday promotions overwhelm carrier regional sorting depots."
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
                cause_id="sorting_overload_sp",
                dimension="customer_state",
                dimension_value="SP",
                causal_category="segment_concentration",
                causal_mechanism=None,
                affected_dimension="customer_state",
                affected_value="SP",
                expected_contribution_pct=None,
            )
        ],
        distractor_causes=[
            "customer_state=SP",
            "customer_state=RJ",
            "seller_dispatch_delay",
        ],
        difficulty="easy",
        is_insufficient_evidence=False,
        target_metric="late_delivery_rate_pct",
        anomaly_date=date(2017, 12, 18),
        comparison_days=7,
        expected_direction="increase",
        severity="critical",
        affected_dimensions=["delivery", "customer_state"],
        expected_evidence_signals=[
            "observed_late_delivery_rate > baseline_late_delivery_rate"
        ],
        tags=["depot", "overload"],
    ),
    GroundTruthScenario(
        scenario_id="SCN-045",
        name="New Year Fleet Maintenance Bottleneck",
        description=(
            "Contracted logistics fleet scheduled maintenance reduces available long-haul transit capacity."
        ),
        primary_cause=GroundTruthRootCause(
            cause_id="carrier_sla_degradation",
            dimension="delivery",
            dimension_value="carrier_transit_delay",
            causal_category="operational_mechanism",
            causal_mechanism="delivery",
            affected_dimension="customer_state",
            affected_value="MG",
            expected_contribution_pct=None,
        ),
        secondary_causes=[
            GroundTruthRootCause(
                cause_id="mg_fleet_shortage",
                dimension="customer_state",
                dimension_value="MG",
                causal_category="segment_concentration",
                causal_mechanism=None,
                affected_dimension="customer_state",
                affected_value="MG",
                expected_contribution_pct=None,
            )
        ],
        distractor_causes=["customer_state=MG", "customer_state=SP"],
        difficulty="medium",
        is_insufficient_evidence=False,
        target_metric="late_delivery_rate_pct",
        anomaly_date=date(2018, 1, 9),
        comparison_days=7,
        expected_direction="increase",
        severity="warning",
        affected_dimensions=["delivery", "customer_state"],
        expected_evidence_signals=[
            "observed_late_delivery_rate > baseline_late_delivery_rate"
        ],
        tags=["fleet", "maintenance"],
    ),
    GroundTruthScenario(
        scenario_id="SCN-046",
        name="Nationwide Truckers Strike Logistics Freeze",
        description=(
            "Massive transportation blockade freezes interstate cargo movement, driving record late delivery rates."
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
                cause_id="strike_logistics_collapse",
                dimension="customer_state",
                dimension_value="SP",
                causal_category="segment_concentration",
                causal_mechanism=None,
                affected_dimension="customer_state",
                affected_value="SP",
                expected_contribution_pct=None,
            )
        ],
        distractor_causes=[
            "customer_state=SP",
            "customer_state=RJ",
            "customer_state=MG",
        ],
        difficulty="easy",
        is_insufficient_evidence=False,
        target_metric="late_delivery_rate_pct",
        anomaly_date=date(2018, 3, 15),
        comparison_days=7,
        expected_direction="increase",
        severity="critical",
        affected_dimensions=["delivery", "customer_state"],
        expected_evidence_signals=[
            "observed_late_delivery_rate > baseline_late_delivery_rate"
        ],
        tags=["strike", "crisis"],
    ),
    GroundTruthScenario(
        scenario_id="SCN-047",
        name="Midwest Agricultural Harvest Transit Squeeze",
        description=(
            "Grain harvest peak monopolizes regional freight capacity, causing e-commerce parcel delays in GO and MT."
        ),
        primary_cause=GroundTruthRootCause(
            cause_id="carrier_sla_degradation",
            dimension="delivery",
            dimension_value="carrier_transit_delay",
            causal_category="operational_mechanism",
            causal_mechanism="delivery",
            affected_dimension="customer_state",
            affected_value="GO",
            expected_contribution_pct=None,
        ),
        secondary_causes=[
            GroundTruthRootCause(
                cause_id="go_freight_squeeze",
                dimension="customer_state",
                dimension_value="GO",
                causal_category="segment_concentration",
                causal_mechanism=None,
                affected_dimension="customer_state",
                affected_value="GO",
                expected_contribution_pct=None,
            )
        ],
        distractor_causes=["customer_state=GO", "customer_state=DF"],
        difficulty="medium",
        is_insufficient_evidence=False,
        target_metric="late_delivery_rate_pct",
        anomaly_date=date(2018, 4, 5),
        comparison_days=7,
        expected_direction="increase",
        severity="warning",
        affected_dimensions=["delivery", "customer_state"],
        expected_evidence_signals=[
            "observed_late_delivery_rate > baseline_late_delivery_rate"
        ],
        tags=["agricultural", "capacity"],
    ),
    GroundTruthScenario(
        scenario_id="SCN-048",
        name="Logistics Delivery Delay Customer Backlash",
        description=(
            "Extended shipping delays from regional freight congestion drive sharp deterioration in review scores."
        ),
        primary_cause=GroundTruthRootCause(
            cause_id="customer_satisfaction_decline",
            dimension="avg_review_score",
            dimension_value=None,
            causal_category="operational_mechanism",
            causal_mechanism="avg_review_score",
            affected_dimension="delivery",
            affected_value="late_delivery",
            expected_contribution_pct=None,
        ),
        secondary_causes=[
            GroundTruthRootCause(
                cause_id="delivery_friction_spillover",
                dimension="delivery",
                dimension_value="late_delivery",
                causal_category="operational_mechanism",
                causal_mechanism="delivery",
                affected_dimension=None,
                affected_value=None,
                expected_contribution_pct=None,
            )
        ],
        distractor_causes=["delivery", "product_category=relogios_presentes"],
        difficulty="easy",
        is_insufficient_evidence=False,
        target_metric="avg_review_score",
        anomaly_date=date(2017, 3, 15),
        comparison_days=7,
        expected_direction="decrease",
        severity="warning",
        affected_dimensions=["avg_review_score", "delivery"],
        expected_evidence_signals=[
            "observed_avg_review_score < baseline_avg_review_score"
        ],
        tags=["sentiment", "feedback"],
    ),
    GroundTruthScenario(
        scenario_id="SCN-049",
        name="Holiday Season Delayed Orders Review Penalty",
        description=(
            "Delayed Christmas deliveries result in severe negative customer sentiment in post-holiday reviews."
        ),
        primary_cause=GroundTruthRootCause(
            cause_id="customer_satisfaction_decline",
            dimension="avg_review_score",
            dimension_value=None,
            causal_category="operational_mechanism",
            causal_mechanism="avg_review_score",
            affected_dimension="delivery",
            affected_value="late_delivery",
            expected_contribution_pct=None,
        ),
        secondary_causes=[
            GroundTruthRootCause(
                cause_id="black_friday_review_drop",
                dimension="delivery",
                dimension_value="late_delivery",
                causal_category="operational_mechanism",
                causal_mechanism="delivery",
                affected_dimension=None,
                affected_value=None,
                expected_contribution_pct=None,
            )
        ],
        distractor_causes=["delivery", "customer_state=SP"],
        difficulty="easy",
        is_insufficient_evidence=False,
        target_metric="avg_review_score",
        anomaly_date=date(2017, 11, 24),
        comparison_days=7,
        expected_direction="decrease",
        severity="critical",
        affected_dimensions=["avg_review_score", "delivery"],
        expected_evidence_signals=[
            "observed_avg_review_score < baseline_avg_review_score"
        ],
        tags=["satisfaction", "reviews"],
    ),
    GroundTruthScenario(
        scenario_id="SCN-050",
        name="Packaging Quality Deterioration in Fragile Goods",
        description=(
            "Supplier packaging changes lead to item damage in transit, triggering negative product reviews."
        ),
        primary_cause=GroundTruthRootCause(
            cause_id="customer_satisfaction_decline",
            dimension="avg_review_score",
            dimension_value=None,
            causal_category="operational_mechanism",
            causal_mechanism="avg_review_score",
            affected_dimension="product_category",
            affected_value="utilidades_domesticas",
            expected_contribution_pct=None,
        ),
        secondary_causes=[
            GroundTruthRootCause(
                cause_id="fragile_goods_breakage",
                dimension="product_category",
                dimension_value="utilidades_domesticas",
                causal_category="segment_concentration",
                causal_mechanism=None,
                affected_dimension="product_category",
                affected_value="utilidades_domesticas",
                expected_contribution_pct=None,
            )
        ],
        distractor_causes=["product_category=utilidades_domesticas", "delivery"],
        difficulty="medium",
        is_insufficient_evidence=False,
        target_metric="avg_review_score",
        anomaly_date=date(2018, 1, 15),
        comparison_days=7,
        expected_direction="decrease",
        severity="warning",
        affected_dimensions=["avg_review_score", "product_category"],
        expected_evidence_signals=[
            "observed_avg_review_score < baseline_avg_review_score"
        ],
        tags=["quality", "damages"],
    ),
    GroundTruthScenario(
        scenario_id="SCN-051",
        name="Carrier SLA Degradation Sentiment Impact",
        description=(
            "Widespread delivery delays during March freight strike heavily depress platform-wide rating averages."
        ),
        primary_cause=GroundTruthRootCause(
            cause_id="customer_satisfaction_decline",
            dimension="avg_review_score",
            dimension_value=None,
            causal_category="operational_mechanism",
            causal_mechanism="avg_review_score",
            affected_dimension="delivery",
            affected_value="late_delivery",
            expected_contribution_pct=None,
        ),
        secondary_causes=[
            GroundTruthRootCause(
                cause_id="strike_review_collapse",
                dimension="delivery",
                dimension_value="late_delivery",
                causal_category="operational_mechanism",
                causal_mechanism="delivery",
                affected_dimension=None,
                affected_value=None,
                expected_contribution_pct=None,
            )
        ],
        distractor_causes=["delivery", "customer_state=SP"],
        difficulty="easy",
        is_insufficient_evidence=False,
        target_metric="avg_review_score",
        anomaly_date=date(2018, 3, 22),
        comparison_days=7,
        expected_direction="decrease",
        severity="critical",
        affected_dimensions=["avg_review_score", "delivery"],
        expected_evidence_signals=[
            "observed_avg_review_score < baseline_avg_review_score"
        ],
        tags=["strike", "sentiment"],
    ),
    GroundTruthScenario(
        scenario_id="SCN-052",
        name="High-Volume Seller Dispatch Quality Slip",
        description=(
            "A major marketplace seller experiences staff shortages, leading to packaging errors and low scores."
        ),
        primary_cause=GroundTruthRootCause(
            cause_id="customer_satisfaction_decline",
            dimension="avg_review_score",
            dimension_value=None,
            causal_category="operational_mechanism",
            causal_mechanism="avg_review_score",
            affected_dimension="seller",
            affected_value="seller_dispatch",
            expected_contribution_pct=None,
        ),
        secondary_causes=[
            GroundTruthRootCause(
                cause_id="seller_quality_slip",
                dimension="seller",
                dimension_value=None,
                causal_category="segment_concentration",
                causal_mechanism=None,
                affected_dimension="seller",
                affected_value=None,
                expected_contribution_pct=None,
            )
        ],
        distractor_causes=["seller", "delivery"],
        difficulty="medium",
        is_insufficient_evidence=False,
        target_metric="avg_review_score",
        anomaly_date=date(2018, 5, 16),
        comparison_days=7,
        expected_direction="decrease",
        severity="warning",
        affected_dimensions=["avg_review_score", "seller"],
        expected_evidence_signals=[
            "observed_avg_review_score < baseline_avg_review_score"
        ],
        tags=["seller", "quality"],
    ),
    # --- EASY (SCN-053 to SCN-067) ---
    GroundTruthScenario(
        scenario_id="SCN-053",
        name="Mid-Year Flash Sale Volume Surge",
        description=(
            "A weekend flash sale event drives a single-day order volume spike across broad "
            "categories, with transaction count more than doubling against the prior-week baseline."
        ),
        primary_cause=GroundTruthRootCause(
            cause_id="order_volume_surge",
            dimension="order_volume",
            dimension_value=None,
            causal_category="macro_driver",
            causal_mechanism="order_volume",
            affected_dimension="customer_state",
            affected_value="SP",
            expected_contribution_pct=82.0,
        ),
        secondary_causes=[
            GroundTruthRootCause(
                cause_id="sp_acquisition_hub",
                dimension="customer_state",
                dimension_value="SP",
                causal_category="segment_concentration",
                causal_mechanism=None,
                affected_dimension="customer_state",
                affected_value="SP",
                expected_contribution_pct=38.0,
            )
        ],
        distractor_causes=[
            "average_order_value_expansion",
            "product_category=cama_mesa_banho",
            "customer_state=RJ",
        ],
        difficulty="easy",
        is_insufficient_evidence=False,
        target_metric="total_gmv",
        anomaly_date=date(2017, 7, 1),
        comparison_days=7,
        expected_direction="increase",
        severity="warning",
        affected_dimensions=["order_volume", "customer_state"],
        expected_evidence_signals=[
            "volume_contribution_pct > 70.0",
            "observed_orders > baseline_orders",
        ],
        tags=["flash_sale", "volume", "promotional"],
    ),
    GroundTruthScenario(
        scenario_id="SCN-054",
        name="September Post-Holiday Volume Contraction",
        description=(
            "Following an extended late-August promotional period, September sees a sharp volume "
            "hangover as purchase appetite is exhausted and order rates fall below the prior-week "
            "level."
        ),
        primary_cause=GroundTruthRootCause(
            cause_id="order_volume_drop",
            dimension="order_volume",
            dimension_value=None,
            causal_category="macro_driver",
            causal_mechanism="order_volume",
            affected_dimension="customer_state",
            affected_value="SP",
            expected_contribution_pct=79.0,
        ),
        secondary_causes=[
            GroundTruthRootCause(
                cause_id="sp_volume_softening",
                dimension="customer_state",
                dimension_value="SP",
                causal_category="segment_concentration",
                causal_mechanism=None,
                affected_dimension="customer_state",
                affected_value="SP",
                expected_contribution_pct=None,
            )
        ],
        distractor_causes=[
            "average_order_value_contraction",
            "product_category=beleza_saude",
            "late_delivery_rate_increase",
        ],
        difficulty="easy",
        is_insufficient_evidence=False,
        target_metric="total_gmv",
        anomaly_date=date(2017, 9, 30),
        comparison_days=7,
        expected_direction="decrease",
        severity="warning",
        affected_dimensions=["order_volume", "customer_state"],
        expected_evidence_signals=[
            "volume_contribution_pct > 65.0",
            "observed_orders < baseline_orders",
        ],
        tags=["seasonal", "hangover", "volume_contraction"],
    ),
    GroundTruthScenario(
        scenario_id="SCN-055",
        name="December Holiday Order Volume Expansion",
        description=(
            "Early December holiday shopping creates a sharp uplift in daily order count across "
            "consumer goods categories, with Brazil's core retail states leading the demand surge."
        ),
        primary_cause=GroundTruthRootCause(
            cause_id="order_volume_surge",
            dimension="order_volume",
            dimension_value=None,
            causal_category="macro_driver",
            causal_mechanism="order_volume",
            affected_dimension="customer_state",
            affected_value="SP",
            expected_contribution_pct=83.0,
        ),
        secondary_causes=[
            GroundTruthRootCause(
                cause_id="sp_holiday_hub",
                dimension="customer_state",
                dimension_value="SP",
                causal_category="segment_concentration",
                causal_mechanism=None,
                affected_dimension="customer_state",
                affected_value="SP",
                expected_contribution_pct=42.0,
            )
        ],
        distractor_causes=[
            "average_order_value_expansion",
            "product_category=brinquedos",
            "customer_state=RJ",
        ],
        difficulty="easy",
        is_insufficient_evidence=False,
        target_metric="orders_count",
        anomaly_date=date(2017, 12, 20),
        comparison_days=7,
        expected_direction="increase",
        severity="warning",
        affected_dimensions=["order_volume", "customer_state"],
        expected_evidence_signals=[
            "observed_orders > baseline_orders",
            "volume_contribution_pct > 75.0",
        ],
        tags=["holiday", "seasonal", "december"],
    ),
    GroundTruthScenario(
        scenario_id="SCN-056",
        name="Post-New Year January Demand Drop",
        description=(
            "Consumer spending fatigue and budget recovery after the holiday season create a "
            "sustained post-new-year demand trough, with order volumes dropping sharply in "
            "the third week of January."
        ),
        primary_cause=GroundTruthRootCause(
            cause_id="order_volume_drop",
            dimension="order_volume",
            dimension_value=None,
            causal_category="macro_driver",
            causal_mechanism="order_volume",
            affected_dimension="customer_state",
            affected_value="SP",
            expected_contribution_pct=77.0,
        ),
        secondary_causes=[
            GroundTruthRootCause(
                cause_id="sp_january_slowdown",
                dimension="customer_state",
                dimension_value="SP",
                causal_category="segment_concentration",
                causal_mechanism=None,
                affected_dimension="customer_state",
                affected_value="SP",
                expected_contribution_pct=None,
            )
        ],
        distractor_causes=[
            "average_order_value_contraction",
            "late_delivery_rate_increase",
            "product_category=cama_mesa_banho",
        ],
        difficulty="easy",
        is_insufficient_evidence=False,
        target_metric="orders_count",
        anomaly_date=date(2017, 1, 20),
        comparison_days=7,
        expected_direction="decrease",
        severity="warning",
        affected_dimensions=["order_volume", "customer_state"],
        expected_evidence_signals=[
            "observed_orders < baseline_orders",
            "volume_contribution_pct > 65.0",
        ],
        tags=["seasonal", "january", "demand_trough"],
    ),
    GroundTruthScenario(
        scenario_id="SCN-057",
        name="Luxury Watch Gifting Basket Surge",
        description=(
            "A targeted promotional campaign on luxury watches and premium gifts drives a "
            "significant expansion in average basket value, with the relogios_presentes category "
            "generating outsized ticket sizes relative to the baseline period."
        ),
        primary_cause=GroundTruthRootCause(
            cause_id="average_order_value_expansion",
            dimension="average_order_value",
            dimension_value=None,
            causal_category="macro_driver",
            causal_mechanism="average_order_value",
            affected_dimension="product_category",
            affected_value="relogios_presentes",
            expected_contribution_pct=72.0,
        ),
        secondary_causes=[
            GroundTruthRootCause(
                cause_id="luxury_category_mix_shift",
                dimension="product_category",
                dimension_value="relogios_presentes",
                causal_category="segment_concentration",
                causal_mechanism=None,
                affected_dimension="product_category",
                affected_value="relogios_presentes",
                expected_contribution_pct=None,
            )
        ],
        distractor_causes=[
            "order_volume_surge",
            "customer_state=SP",
            "product_category=eletrodomesticos",
        ],
        difficulty="easy",
        is_insufficient_evidence=False,
        target_metric="average_order_value",
        anomaly_date=date(2017, 5, 15),
        comparison_days=7,
        expected_direction="increase",
        severity="warning",
        affected_dimensions=["average_order_value", "product_category"],
        expected_evidence_signals=[
            "aov_contribution_pct > 60.0",
            "observed_aov > baseline_aov",
        ],
        tags=["luxury", "gifting", "basket_expansion"],
    ),
    GroundTruthScenario(
        scenario_id="SCN-058",
        name="Electronics Price War AOV Collapse",
        description=(
            "Competitive price slashing in the computer accessories and consumer electronics "
            "segment drives average ticket sizes sharply lower as buyers shift toward discounted "
            "commodity items."
        ),
        primary_cause=GroundTruthRootCause(
            cause_id="average_order_value_contraction",
            dimension="average_order_value",
            dimension_value=None,
            causal_category="macro_driver",
            causal_mechanism="average_order_value",
            affected_dimension="product_category",
            affected_value="informatica_acessorios",
            expected_contribution_pct=68.0,
        ),
        secondary_causes=[
            GroundTruthRootCause(
                cause_id="tech_category_discount_mix",
                dimension="product_category",
                dimension_value="informatica_acessorios",
                causal_category="segment_concentration",
                causal_mechanism=None,
                affected_dimension="product_category",
                affected_value="informatica_acessorios",
                expected_contribution_pct=None,
            )
        ],
        distractor_causes=[
            "order_volume_drop",
            "customer_state=SP",
            "product_category=beleza_saude",
        ],
        difficulty="easy",
        is_insufficient_evidence=False,
        target_metric="average_order_value",
        anomaly_date=date(2017, 8, 10),
        comparison_days=7,
        expected_direction="decrease",
        severity="warning",
        affected_dimensions=["average_order_value", "product_category"],
        expected_evidence_signals=[
            "aov_contribution_pct > 55.0",
            "observed_aov < baseline_aov",
        ],
        tags=["electronics", "price_war", "basket_contraction"],
    ),
    GroundTruthScenario(
        scenario_id="SCN-059",
        name="Northeast Regional Logistics Bottleneck",
        description=(
            "Severe port congestion and freight capacity constraints in Brazil's northeast create "
            "a regional delivery delay spike concentrated in BA, CE, and PE states."
        ),
        primary_cause=GroundTruthRootCause(
            cause_id="logistics_fulfillment_bottleneck",
            dimension="delivery",
            dimension_value="late_delivery",
            causal_category="operational_mechanism",
            causal_mechanism="delivery",
            affected_dimension="customer_state",
            affected_value="BA",
            expected_contribution_pct=None,
        ),
        secondary_causes=[
            GroundTruthRootCause(
                cause_id="northeast_regional_concentration",
                dimension="customer_state",
                dimension_value="BA",
                causal_category="segment_concentration",
                causal_mechanism=None,
                affected_dimension="customer_state",
                affected_value="BA",
                expected_contribution_pct=None,
            )
        ],
        distractor_causes=[
            "customer_state=SP",
            "order_volume_surge",
            "product_category=moveis_decoracao",
        ],
        difficulty="easy",
        is_insufficient_evidence=False,
        target_metric="late_delivery_rate_pct",
        anomaly_date=date(2017, 6, 10),
        comparison_days=7,
        expected_direction="increase",
        severity="warning",
        affected_dimensions=["delivery", "customer_state"],
        expected_evidence_signals=[
            "observed_late_delivery_rate > baseline_late_delivery_rate",
            "avg_delivery_days_change > 0",
        ],
        tags=["logistics", "northeast", "regional_bottleneck"],
    ),
    GroundTruthScenario(
        scenario_id="SCN-060",
        name="Southern State Carrier Recovery",
        description=(
            "Following a prior-month freight disruption, logistics carriers in Brazil's south "
            "restore normal transit SLAs, driving a significant drop in the late delivery rate."
        ),
        primary_cause=GroundTruthRootCause(
            cause_id="carrier_sla_degradation",
            dimension="delivery",
            dimension_value="carrier_transit_delay",
            causal_category="operational_mechanism",
            causal_mechanism="delivery",
            affected_dimension="customer_state",
            affected_value="RS",
            expected_contribution_pct=None,
        ),
        secondary_causes=[
            GroundTruthRootCause(
                cause_id="rs_sc_pr_recovery",
                dimension="customer_state",
                dimension_value="RS",
                causal_category="segment_concentration",
                causal_mechanism=None,
                affected_dimension="customer_state",
                affected_value="RS",
                expected_contribution_pct=None,
            )
        ],
        distractor_causes=[
            "order_volume_drop",
            "customer_state=SP",
            "product_category=construcao_ferramentas_seguranca",
        ],
        difficulty="easy",
        is_insufficient_evidence=False,
        target_metric="late_delivery_rate_pct",
        anomaly_date=date(2017, 4, 1),
        comparison_days=7,
        expected_direction="decrease",
        severity="warning",
        affected_dimensions=["delivery", "customer_state"],
        expected_evidence_signals=[
            "observed_late_delivery_rate < baseline_late_delivery_rate"
        ],
        tags=["logistics", "south", "carrier_recovery"],
    ),
    GroundTruthScenario(
        scenario_id="SCN-061",
        name="Product Damage Complaint Surge",
        description=(
            "A batch of items dispatched with inadequate protective packaging results in high "
            "damage-in-transit rates, triggering a wave of 1-star and 2-star reviews concentrated "
            "in household goods."
        ),
        primary_cause=GroundTruthRootCause(
            cause_id="customer_satisfaction_decline",
            dimension="avg_review_score",
            dimension_value=None,
            causal_category="operational_mechanism",
            causal_mechanism="avg_review_score",
            affected_dimension="product_category",
            affected_value="utilidades_domesticas",
            expected_contribution_pct=None,
        ),
        secondary_causes=[
            GroundTruthRootCause(
                cause_id="domestic_goods_damage_cluster",
                dimension="product_category",
                dimension_value="utilidades_domesticas",
                causal_category="segment_concentration",
                causal_mechanism=None,
                affected_dimension="product_category",
                affected_value="utilidades_domesticas",
                expected_contribution_pct=None,
            )
        ],
        distractor_causes=["delivery", "customer_state=SP", "order_volume_surge"],
        difficulty="easy",
        is_insufficient_evidence=False,
        target_metric="avg_review_score",
        anomaly_date=date(2017, 5, 20),
        comparison_days=7,
        expected_direction="decrease",
        severity="warning",
        affected_dimensions=["avg_review_score", "product_category"],
        expected_evidence_signals=[
            "observed_avg_review_score < baseline_avg_review_score"
        ],
        tags=["quality", "damage", "complaints"],
    ),
    GroundTruthScenario(
        scenario_id="SCN-062",
        name="Customer Service Improvement Sentiment Lift",
        description=(
            "Following a platform-wide customer support initiative with faster response times "
            "and proactive order tracking, buyer satisfaction scores improve markedly over "
            "the comparison week."
        ),
        primary_cause=GroundTruthRootCause(
            cause_id="customer_satisfaction_decline",
            dimension="avg_review_score",
            dimension_value=None,
            causal_category="operational_mechanism",
            causal_mechanism="avg_review_score",
            affected_dimension="delivery",
            affected_value="late_delivery",
            expected_contribution_pct=None,
        ),
        secondary_causes=[
            GroundTruthRootCause(
                cause_id="delivery_improvement_driver",
                dimension="delivery",
                dimension_value="late_delivery",
                causal_category="operational_mechanism",
                causal_mechanism="delivery",
                affected_dimension=None,
                affected_value=None,
                expected_contribution_pct=None,
            )
        ],
        distractor_causes=[
            "order_volume_drop",
            "product_category=cama_mesa_banho",
            "average_order_value_expansion",
        ],
        difficulty="easy",
        is_insufficient_evidence=False,
        target_metric="avg_review_score",
        anomaly_date=date(2017, 3, 10),
        comparison_days=7,
        expected_direction="increase",
        severity="normal",
        affected_dimensions=["avg_review_score", "delivery"],
        expected_evidence_signals=[
            "observed_avg_review_score > baseline_avg_review_score"
        ],
        tags=["sentiment", "improvement", "customer_service"],
    ),
    GroundTruthScenario(
        scenario_id="SCN-063",
        name="Furniture Category Volume Expansion",
        description=(
            "A targeted home improvement campaign drives significant unit volume growth in the "
            "furniture and decor category, lifting total GMV predominantly through order count "
            "expansion."
        ),
        primary_cause=GroundTruthRootCause(
            cause_id="order_volume_surge",
            dimension="order_volume",
            dimension_value=None,
            causal_category="macro_driver",
            causal_mechanism="order_volume",
            affected_dimension="product_category",
            affected_value="moveis_decoracao",
            expected_contribution_pct=76.0,
        ),
        secondary_causes=[
            GroundTruthRootCause(
                cause_id="furniture_category_uplift",
                dimension="product_category",
                dimension_value="moveis_decoracao",
                causal_category="segment_concentration",
                causal_mechanism=None,
                affected_dimension="product_category",
                affected_value="moveis_decoracao",
                expected_contribution_pct=None,
            )
        ],
        distractor_causes=[
            "average_order_value_expansion",
            "customer_state=SP",
            "product_category=cama_mesa_banho",
        ],
        difficulty="easy",
        is_insufficient_evidence=False,
        target_metric="total_gmv",
        anomaly_date=date(2017, 11, 15),
        comparison_days=7,
        expected_direction="increase",
        severity="warning",
        affected_dimensions=["order_volume", "product_category"],
        expected_evidence_signals=[
            "volume_contribution_pct > 65.0",
            "observed_orders > baseline_orders",
        ],
        tags=["furniture", "home_improvement", "category_expansion"],
    ),
    GroundTruthScenario(
        scenario_id="SCN-064",
        name="Post-Valentine Gift Order Drop",
        description=(
            "Following Brazil's June Dia dos Namorados gift-buying peak, the following week "
            "sees a sharp demand hangover as purchase intent normalizes."
        ),
        primary_cause=GroundTruthRootCause(
            cause_id="order_volume_drop",
            dimension="order_volume",
            dimension_value=None,
            causal_category="macro_driver",
            causal_mechanism="order_volume",
            affected_dimension="product_category",
            affected_value="relogios_presentes",
            expected_contribution_pct=75.0,
        ),
        secondary_causes=[
            GroundTruthRootCause(
                cause_id="gifting_category_hangover",
                dimension="product_category",
                dimension_value="relogios_presentes",
                causal_category="segment_concentration",
                causal_mechanism=None,
                affected_dimension="product_category",
                affected_value="relogios_presentes",
                expected_contribution_pct=None,
            )
        ],
        distractor_causes=[
            "average_order_value_contraction",
            "customer_state=SP",
            "product_category=beleza_saude",
        ],
        difficulty="easy",
        is_insufficient_evidence=False,
        target_metric="orders_count",
        anomaly_date=date(2017, 6, 20),
        comparison_days=7,
        expected_direction="decrease",
        severity="warning",
        affected_dimensions=["order_volume", "product_category"],
        expected_evidence_signals=[
            "observed_orders < baseline_orders",
            "volume_contribution_pct > 60.0",
        ],
        tags=["seasonal", "valentines", "gifting_hangover"],
    ),
    GroundTruthScenario(
        scenario_id="SCN-065",
        name="Electronics Super-Sale AOV Spike",
        description=(
            "A major electronics promotion combining bundle deals and instalment financing "
            "drives a sharp increase in average ticket value, with high-end devices lifting "
            "the basket."
        ),
        primary_cause=GroundTruthRootCause(
            cause_id="average_order_value_expansion",
            dimension="average_order_value",
            dimension_value=None,
            causal_category="macro_driver",
            causal_mechanism="average_order_value",
            affected_dimension="product_category",
            affected_value="eletrodomesticos",
            expected_contribution_pct=70.0,
        ),
        secondary_causes=[
            GroundTruthRootCause(
                cause_id="appliance_bundle_mix",
                dimension="product_category",
                dimension_value="eletrodomesticos",
                causal_category="segment_concentration",
                causal_mechanism=None,
                affected_dimension="product_category",
                affected_value="eletrodomesticos",
                expected_contribution_pct=None,
            )
        ],
        distractor_causes=[
            "order_volume_surge",
            "customer_state=SP",
            "product_category=informatica_acessorios",
        ],
        difficulty="easy",
        is_insufficient_evidence=False,
        target_metric="total_gmv",
        anomaly_date=date(2017, 3, 25),
        comparison_days=7,
        expected_direction="increase",
        severity="warning",
        affected_dimensions=["average_order_value", "product_category"],
        expected_evidence_signals=[
            "aov_contribution_pct > 55.0",
            "observed_aov > baseline_aov",
        ],
        tags=["electronics", "promotion", "basket_expansion"],
    ),
    GroundTruthScenario(
        scenario_id="SCN-066",
        name="Carnival Week Order Freeze",
        description=(
            "Brazil's Carnival holiday week causes a nationwide commercial pause: logistics are "
            "disrupted, discretionary spending halts, and order volume collapses across all "
            "categories and states."
        ),
        primary_cause=GroundTruthRootCause(
            cause_id="order_volume_drop",
            dimension="order_volume",
            dimension_value=None,
            causal_category="macro_driver",
            causal_mechanism="order_volume",
            affected_dimension="customer_state",
            affected_value="SP",
            expected_contribution_pct=85.0,
        ),
        secondary_causes=[
            GroundTruthRootCause(
                cause_id="sp_carnival_freeze",
                dimension="customer_state",
                dimension_value="SP",
                causal_category="segment_concentration",
                causal_mechanism=None,
                affected_dimension="customer_state",
                affected_value="SP",
                expected_contribution_pct=None,
            )
        ],
        distractor_causes=[
            "average_order_value_contraction",
            "carrier_sla_degradation",
            "product_category=cama_mesa_banho",
        ],
        difficulty="easy",
        is_insufficient_evidence=False,
        target_metric="total_gmv",
        anomaly_date=date(2017, 2, 27),
        comparison_days=7,
        expected_direction="decrease",
        severity="critical",
        affected_dimensions=["order_volume", "customer_state"],
        expected_evidence_signals=[
            "volume_contribution_pct > 75.0",
            "observed_orders < baseline_orders",
        ],
        tags=["seasonal", "carnival", "holiday_freeze"],
    ),
    GroundTruthScenario(
        scenario_id="SCN-067",
        name="Mother's Day Category Gift Surge",
        description=(
            "Brazil's Dia das Maes in May triggers a concentrated gift-buying surge in beauty, "
            "perfume, and household accessories, lifting GMV almost entirely through volume "
            "expansion."
        ),
        primary_cause=GroundTruthRootCause(
            cause_id="order_volume_surge",
            dimension="order_volume",
            dimension_value=None,
            causal_category="macro_driver",
            causal_mechanism="order_volume",
            affected_dimension="product_category",
            affected_value="beleza_saude",
            expected_contribution_pct=78.0,
        ),
        secondary_causes=[
            GroundTruthRootCause(
                cause_id="beauty_mothers_day_spike",
                dimension="product_category",
                dimension_value="beleza_saude",
                causal_category="segment_concentration",
                causal_mechanism=None,
                affected_dimension="product_category",
                affected_value="beleza_saude",
                expected_contribution_pct=None,
            )
        ],
        distractor_causes=[
            "average_order_value_expansion",
            "customer_state=RJ",
            "product_category=relogios_presentes",
        ],
        difficulty="easy",
        is_insufficient_evidence=False,
        target_metric="total_gmv",
        anomaly_date=date(2017, 5, 13),
        comparison_days=7,
        expected_direction="increase",
        severity="warning",
        affected_dimensions=["order_volume", "product_category"],
        expected_evidence_signals=[
            "volume_contribution_pct > 65.0",
            "observed_orders > baseline_orders",
        ],
        tags=["seasonal", "mothers_day", "category_surge"],
    ),
    # --- MEDIUM (SCN-068 to SCN-095) ---
    GroundTruthScenario(
        scenario_id="SCN-068",
        name="Black Friday Volume and AOV Combined Effect",
        description=(
            "Brazil's Black Friday generates a simultaneous volume surge and basket expansion: "
            "promotional bundles lift AOV while acquisition campaigns multiply order count. "
            "Both mechanisms contribute meaningfully, making isolated attribution non-trivial."
        ),
        primary_cause=GroundTruthRootCause(
            cause_id="order_volume_surge",
            dimension="order_volume",
            dimension_value=None,
            causal_category="macro_driver",
            causal_mechanism="order_volume",
            affected_dimension="customer_state",
            affected_value="SP",
            expected_contribution_pct=62.0,
        ),
        secondary_causes=[
            GroundTruthRootCause(
                cause_id="average_order_value_expansion",
                dimension="average_order_value",
                dimension_value=None,
                causal_category="macro_driver",
                causal_mechanism="average_order_value",
                affected_dimension=None,
                affected_value=None,
                expected_contribution_pct=38.0,
            )
        ],
        distractor_causes=[
            "product_category=cama_mesa_banho",
            "customer_state=RJ",
            "carrier_sla_degradation",
        ],
        difficulty="medium",
        is_insufficient_evidence=False,
        target_metric="total_gmv",
        anomaly_date=date(2017, 11, 25),
        comparison_days=7,
        expected_direction="increase",
        severity="critical",
        affected_dimensions=["order_volume", "average_order_value", "customer_state"],
        expected_evidence_signals=[
            "volume_contribution_pct > 50.0",
            "aov_contribution_pct > 25.0",
            "observed_orders > baseline_orders",
        ],
        tags=["black_friday", "multi_driver", "promotional"],
    ),
    GroundTruthScenario(
        scenario_id="SCN-069",
        name="Q3 Revenue Softening Mixed AOV and Volume Signal",
        description=(
            "A mid-August revenue decline shows both average basket contraction and a moderate "
            "volume reduction. The AOV signal is marginally stronger but both mechanisms are "
            "active, requiring careful decomposition to identify the primary driver."
        ),
        primary_cause=GroundTruthRootCause(
            cause_id="average_order_value_contraction",
            dimension="average_order_value",
            dimension_value=None,
            causal_category="macro_driver",
            causal_mechanism="average_order_value",
            affected_dimension="product_category",
            affected_value="cama_mesa_banho",
            expected_contribution_pct=55.0,
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
                expected_contribution_pct=45.0,
            )
        ],
        distractor_causes=[
            "carrier_sla_degradation",
            "customer_state=SP",
            "product_category=beleza_saude",
        ],
        difficulty="medium",
        is_insufficient_evidence=False,
        target_metric="total_gmv",
        anomaly_date=date(2017, 8, 20),
        comparison_days=7,
        expected_direction="decrease",
        severity="warning",
        affected_dimensions=["average_order_value", "order_volume", "product_category"],
        expected_evidence_signals=[
            "aov_contribution_pct > 40.0",
            "observed_aov < baseline_aov",
            "observed_orders < baseline_orders",
        ],
        tags=["competing_drivers", "q3", "revenue_softening"],
    ),
    GroundTruthScenario(
        scenario_id="SCN-070",
        name="Late Delivery Cascade into Review Score Decline",
        description=(
            "A logistics disruption causing delivery SLA breaches in Sao Paulo during January "
            "produces a lagged cascade into customer satisfaction scores, as buyers submit reviews "
            "for late-arriving holiday orders. The review decline requires connecting delivery "
            "signals to the review dimension."
        ),
        primary_cause=GroundTruthRootCause(
            cause_id="customer_satisfaction_decline",
            dimension="avg_review_score",
            dimension_value=None,
            causal_category="operational_mechanism",
            causal_mechanism="avg_review_score",
            affected_dimension="delivery",
            affected_value="late_delivery",
            expected_contribution_pct=None,
        ),
        secondary_causes=[
            GroundTruthRootCause(
                cause_id="delivery_friction_cascade",
                dimension="delivery",
                dimension_value="late_delivery",
                causal_category="operational_mechanism",
                causal_mechanism="delivery",
                affected_dimension=None,
                affected_value=None,
                expected_contribution_pct=None,
            )
        ],
        distractor_causes=[
            "product_category=cama_mesa_banho",
            "order_volume_surge",
            "customer_state=SP",
        ],
        difficulty="medium",
        is_insufficient_evidence=False,
        target_metric="avg_review_score",
        anomaly_date=date(2018, 1, 20),
        comparison_days=7,
        expected_direction="decrease",
        severity="warning",
        affected_dimensions=["avg_review_score", "delivery"],
        expected_evidence_signals=[
            "observed_avg_review_score < baseline_avg_review_score",
            "observed_late_delivery_rate > baseline_late_delivery_rate",
        ],
        tags=["causal_chain", "delivery_cascade", "sentiment"],
    ),
    GroundTruthScenario(
        scenario_id="SCN-071",
        name="Electronics Promo Volume Surge with Category Mix Shift",
        description=(
            "An October consumer electronics promotion produces a clear volume uplift primarily "
            "through informatica_acessorios and telephonia categories, with a secondary basket "
            "compression from budget accessories dominating the category mix."
        ),
        primary_cause=GroundTruthRootCause(
            cause_id="order_volume_surge",
            dimension="order_volume",
            dimension_value=None,
            causal_category="macro_driver",
            causal_mechanism="order_volume",
            affected_dimension="product_category",
            affected_value="informatica_acessorios",
            expected_contribution_pct=65.0,
        ),
        secondary_causes=[
            GroundTruthRootCause(
                cause_id="tech_category_concentration",
                dimension="product_category",
                dimension_value="informatica_acessorios",
                causal_category="segment_concentration",
                causal_mechanism=None,
                affected_dimension="product_category",
                affected_value="informatica_acessorios",
                expected_contribution_pct=None,
            )
        ],
        distractor_causes=[
            "average_order_value_expansion",
            "customer_state=SP",
            "product_category=eletrodomesticos",
        ],
        difficulty="medium",
        is_insufficient_evidence=False,
        target_metric="total_gmv",
        anomaly_date=date(2017, 10, 15),
        comparison_days=7,
        expected_direction="increase",
        severity="warning",
        affected_dimensions=["order_volume", "product_category"],
        expected_evidence_signals=[
            "volume_contribution_pct > 55.0",
            "observed_orders > baseline_orders",
        ],
        tags=["electronics", "category_mix", "promotional"],
    ),
    GroundTruthScenario(
        scenario_id="SCN-072",
        name="Regional Delivery Delay with Multi-State Exposure",
        description=(
            "A routing software failure at a major distribution hub creates delivery delays that "
            "disproportionately affect MG and RJ states, raising the national late delivery rate "
            "through concentrated multi-state SLA breaches."
        ),
        primary_cause=GroundTruthRootCause(
            cause_id="logistics_fulfillment_bottleneck",
            dimension="delivery",
            dimension_value="late_delivery",
            causal_category="operational_mechanism",
            causal_mechanism="delivery",
            affected_dimension="customer_state",
            affected_value="MG",
            expected_contribution_pct=None,
        ),
        secondary_causes=[
            GroundTruthRootCause(
                cause_id="rj_mg_hub_impact",
                dimension="customer_state",
                dimension_value="RJ",
                causal_category="segment_concentration",
                causal_mechanism=None,
                affected_dimension="customer_state",
                affected_value="RJ",
                expected_contribution_pct=None,
            )
        ],
        distractor_causes=[
            "customer_state=SP",
            "order_volume_surge",
            "product_category=moveis_decoracao",
        ],
        difficulty="medium",
        is_insufficient_evidence=False,
        target_metric="late_delivery_rate_pct",
        anomaly_date=date(2017, 9, 5),
        comparison_days=7,
        expected_direction="increase",
        severity="warning",
        affected_dimensions=["delivery", "customer_state"],
        expected_evidence_signals=[
            "observed_late_delivery_rate > baseline_late_delivery_rate",
            "avg_delivery_days_change > 0",
        ],
        tags=["logistics", "multi_state", "hub_failure"],
    ),
    GroundTruthScenario(
        scenario_id="SCN-073",
        name="Beauty Category Volume and Basket Simultaneous Uplift",
        description=(
            "A beleza_saude promotional period with bundled product sets drives concurrent order "
            "volume and basket value growth, requiring examination of both decomposition axes to "
            "confirm which mechanism dominates."
        ),
        primary_cause=GroundTruthRootCause(
            cause_id="order_volume_surge",
            dimension="order_volume",
            dimension_value=None,
            causal_category="macro_driver",
            causal_mechanism="order_volume",
            affected_dimension="product_category",
            affected_value="beleza_saude",
            expected_contribution_pct=58.0,
        ),
        secondary_causes=[
            GroundTruthRootCause(
                cause_id="beauty_bundle_aov_lift",
                dimension="average_order_value",
                dimension_value=None,
                causal_category="macro_driver",
                causal_mechanism="average_order_value",
                affected_dimension="product_category",
                affected_value="beleza_saude",
                expected_contribution_pct=42.0,
            )
        ],
        distractor_causes=[
            "customer_state=SP",
            "product_category=cama_mesa_banho",
            "carrier_sla_degradation",
        ],
        difficulty="medium",
        is_insufficient_evidence=False,
        target_metric="total_gmv",
        anomaly_date=date(2017, 4, 20),
        comparison_days=7,
        expected_direction="increase",
        severity="warning",
        affected_dimensions=["order_volume", "average_order_value", "product_category"],
        expected_evidence_signals=[
            "volume_contribution_pct > 45.0",
            "aov_contribution_pct > 30.0",
            "observed_orders > baseline_orders",
        ],
        tags=["beauty", "multi_driver", "promotional"],
    ),
    GroundTruthScenario(
        scenario_id="SCN-074",
        name="Post-Black Friday Demand Hangover with Category Rotation",
        description=(
            "The week following Black Friday 2017 shows a sharp volume contraction as purchase "
            "appetite is exhausted, amplified by a category composition shift away from high-value "
            "electronics toward lower-ticket items, compressing both volume and AOV simultaneously."
        ),
        primary_cause=GroundTruthRootCause(
            cause_id="order_volume_drop",
            dimension="order_volume",
            dimension_value=None,
            causal_category="macro_driver",
            causal_mechanism="order_volume",
            affected_dimension="customer_state",
            affected_value="SP",
            expected_contribution_pct=65.0,
        ),
        secondary_causes=[
            GroundTruthRootCause(
                cause_id="post_bfriday_aov_compression",
                dimension="average_order_value",
                dimension_value=None,
                causal_category="macro_driver",
                causal_mechanism="average_order_value",
                affected_dimension=None,
                affected_value=None,
                expected_contribution_pct=35.0,
            )
        ],
        distractor_causes=[
            "carrier_sla_degradation",
            "product_category=cama_mesa_banho",
            "customer_state=MG",
        ],
        difficulty="medium",
        is_insufficient_evidence=False,
        target_metric="total_gmv",
        anomaly_date=date(2017, 12, 5),
        comparison_days=7,
        expected_direction="decrease",
        severity="critical",
        affected_dimensions=["order_volume", "average_order_value", "customer_state"],
        expected_evidence_signals=[
            "volume_contribution_pct > 50.0",
            "observed_orders < baseline_orders",
        ],
        tags=["black_friday", "hangover", "multi_driver"],
    ),
    GroundTruthScenario(
        scenario_id="SCN-075",
        name="SP Hub Volume Concentration Shift Driving GMV Decline",
        description=(
            "A disproportionate volume contraction originating in Sao Paulo -- accounting for "
            "over a third of total orders -- creates a revenue decline that requires distinguishing "
            "whether it is a macro demand shift or an SP-specific platform issue."
        ),
        primary_cause=GroundTruthRootCause(
            cause_id="order_volume_drop",
            dimension="order_volume",
            dimension_value=None,
            causal_category="macro_driver",
            causal_mechanism="order_volume",
            affected_dimension="customer_state",
            affected_value="SP",
            expected_contribution_pct=68.0,
        ),
        secondary_causes=[
            GroundTruthRootCause(
                cause_id="sp_concentration_amplifier",
                dimension="customer_state",
                dimension_value="SP",
                causal_category="segment_concentration",
                causal_mechanism=None,
                affected_dimension="customer_state",
                affected_value="SP",
                expected_contribution_pct=None,
            )
        ],
        distractor_causes=[
            "average_order_value_contraction",
            "customer_state=RJ",
            "carrier_sla_degradation",
        ],
        difficulty="medium",
        is_insufficient_evidence=False,
        target_metric="orders_count",
        anomaly_date=date(2017, 7, 15),
        comparison_days=7,
        expected_direction="decrease",
        severity="warning",
        affected_dimensions=["order_volume", "customer_state"],
        expected_evidence_signals=[
            "volume_contribution_pct > 55.0",
            "observed_orders < baseline_orders",
        ],
        tags=["sp_concentration", "volume", "regional"],
    ),
    GroundTruthScenario(
        scenario_id="SCN-076",
        name="Category Mix Shift into High-Ticket Items",
        description=(
            "A November shift in consumer category preferences toward electronics and home "
            "appliances drives a significant basket expansion, with average order value rising "
            "while order count remains broadly stable -- requiring decomposition to isolate "
            "AOV as the primary driver."
        ),
        primary_cause=GroundTruthRootCause(
            cause_id="average_order_value_expansion",
            dimension="average_order_value",
            dimension_value=None,
            causal_category="macro_driver",
            causal_mechanism="average_order_value",
            affected_dimension="product_category",
            affected_value="eletrodomesticos",
            expected_contribution_pct=67.0,
        ),
        secondary_causes=[
            GroundTruthRootCause(
                cause_id="appliance_category_mix_shift",
                dimension="product_category",
                dimension_value="eletrodomesticos",
                causal_category="segment_concentration",
                causal_mechanism=None,
                affected_dimension="product_category",
                affected_value="eletrodomesticos",
                expected_contribution_pct=None,
            )
        ],
        distractor_causes=[
            "order_volume_surge",
            "customer_state=SP",
            "product_category=informatica_acessorios",
        ],
        difficulty="medium",
        is_insufficient_evidence=False,
        target_metric="average_order_value",
        anomaly_date=date(2017, 11, 1),
        comparison_days=7,
        expected_direction="increase",
        severity="warning",
        affected_dimensions=["average_order_value", "product_category"],
        expected_evidence_signals=[
            "aov_contribution_pct > 55.0",
            "observed_aov > baseline_aov",
        ],
        tags=["category_mix", "high_ticket", "basket_expansion"],
    ),
    GroundTruthScenario(
        scenario_id="SCN-077",
        name="Delivery SLA Breach Suppressing New Order Volume",
        description=(
            "Persistent delivery delays that are visible to prospective buyers through platform "
            "reviews suppress new purchase intent, creating a secondary volume contraction "
            "following the initial SLA degradation."
        ),
        primary_cause=GroundTruthRootCause(
            cause_id="order_volume_drop",
            dimension="order_volume",
            dimension_value=None,
            causal_category="macro_driver",
            causal_mechanism="order_volume",
            affected_dimension="customer_state",
            affected_value="SP",
            expected_contribution_pct=60.0,
        ),
        secondary_causes=[
            GroundTruthRootCause(
                cause_id="delivery_sla_demand_suppression",
                dimension="delivery",
                dimension_value="late_delivery",
                causal_category="operational_mechanism",
                causal_mechanism="delivery",
                affected_dimension=None,
                affected_value=None,
                expected_contribution_pct=None,
            )
        ],
        distractor_causes=[
            "average_order_value_contraction",
            "product_category=moveis_decoracao",
            "customer_state=RJ",
        ],
        difficulty="medium",
        is_insufficient_evidence=False,
        target_metric="total_gmv",
        anomaly_date=date(2017, 8, 1),
        comparison_days=7,
        expected_direction="decrease",
        severity="warning",
        affected_dimensions=["order_volume", "delivery", "customer_state"],
        expected_evidence_signals=[
            "volume_contribution_pct > 50.0",
            "observed_late_delivery_rate > baseline_late_delivery_rate",
        ],
        tags=["delivery_demand_link", "causal_chain", "volume_suppression"],
    ),
    GroundTruthScenario(
        scenario_id="SCN-078",
        name="Platform-Wide Review Score Drift from Multiple Sellers",
        description=(
            "A broad quality deterioration across multiple large sellers -- shipping delays, "
            "packaging issues, and mismatched product descriptions -- drives a platform-wide "
            "review score decline not concentrated in a single category or region."
        ),
        primary_cause=GroundTruthRootCause(
            cause_id="customer_satisfaction_decline",
            dimension="avg_review_score",
            dimension_value=None,
            causal_category="operational_mechanism",
            causal_mechanism="avg_review_score",
            affected_dimension="seller",
            affected_value="seller_dispatch",
            expected_contribution_pct=None,
        ),
        secondary_causes=[
            GroundTruthRootCause(
                cause_id="multi_seller_quality_drop",
                dimension="seller",
                dimension_value=None,
                causal_category="segment_concentration",
                causal_mechanism=None,
                affected_dimension="seller",
                affected_value=None,
                expected_contribution_pct=None,
            )
        ],
        distractor_causes=[
            "delivery",
            "product_category=cama_mesa_banho",
            "customer_state=SP",
        ],
        difficulty="medium",
        is_insufficient_evidence=False,
        target_metric="avg_review_score",
        anomaly_date=date(2018, 2, 10),
        comparison_days=7,
        expected_direction="decrease",
        severity="warning",
        affected_dimensions=["avg_review_score", "seller"],
        expected_evidence_signals=[
            "observed_avg_review_score < baseline_avg_review_score"
        ],
        tags=["seller_quality", "platform_wide", "multi_seller"],
    ),
    GroundTruthScenario(
        scenario_id="SCN-079",
        name="Q1 2017 Seasonal Volume Ramp with Regional Concentration",
        description=(
            "March 2017 sees a broad post-carnival volume recovery across the platform, but the "
            "recovery is disproportionately concentrated in Sao Paulo. The challenge is "
            "distinguishing whether this is a macro volume trend or an SP platform campaign."
        ),
        primary_cause=GroundTruthRootCause(
            cause_id="order_volume_surge",
            dimension="order_volume",
            dimension_value=None,
            causal_category="macro_driver",
            causal_mechanism="order_volume",
            affected_dimension="customer_state",
            affected_value="SP",
            expected_contribution_pct=63.0,
        ),
        secondary_causes=[
            GroundTruthRootCause(
                cause_id="sp_post_carnival_amplification",
                dimension="customer_state",
                dimension_value="SP",
                causal_category="segment_concentration",
                causal_mechanism=None,
                affected_dimension="customer_state",
                affected_value="SP",
                expected_contribution_pct=None,
            )
        ],
        distractor_causes=[
            "average_order_value_expansion",
            "product_category=beleza_saude",
            "customer_state=RJ",
        ],
        difficulty="medium",
        is_insufficient_evidence=False,
        target_metric="orders_count",
        anomaly_date=date(2017, 3, 15),
        comparison_days=7,
        expected_direction="increase",
        severity="warning",
        affected_dimensions=["order_volume", "customer_state"],
        expected_evidence_signals=[
            "volume_contribution_pct > 55.0",
            "observed_orders > baseline_orders",
        ],
        tags=["seasonal", "q1", "sp_concentration"],
    ),
    GroundTruthScenario(
        scenario_id="SCN-080",
        name="Post-Christmas Late Delivery Review Penalty",
        description=(
            "Christmas delivery congestion causes a lagged review score decline as disappointed "
            "buyers receive late gifts and submit negative reviews in the final week of December. "
            "The review decline occurs simultaneously with a delivery SLA spike, requiring "
            "cross-metric analysis."
        ),
        primary_cause=GroundTruthRootCause(
            cause_id="customer_satisfaction_decline",
            dimension="avg_review_score",
            dimension_value=None,
            causal_category="operational_mechanism",
            causal_mechanism="avg_review_score",
            affected_dimension="delivery",
            affected_value="late_delivery",
            expected_contribution_pct=None,
        ),
        secondary_causes=[
            GroundTruthRootCause(
                cause_id="christmas_delivery_late_cascade",
                dimension="delivery",
                dimension_value="late_delivery",
                causal_category="operational_mechanism",
                causal_mechanism="delivery",
                affected_dimension=None,
                affected_value=None,
                expected_contribution_pct=None,
            )
        ],
        distractor_causes=[
            "product_category=brinquedos",
            "customer_state=SP",
            "order_volume_surge",
        ],
        difficulty="medium",
        is_insufficient_evidence=False,
        target_metric="avg_review_score",
        anomaly_date=date(2017, 12, 28),
        comparison_days=7,
        expected_direction="decrease",
        severity="critical",
        affected_dimensions=["avg_review_score", "delivery"],
        expected_evidence_signals=[
            "observed_avg_review_score < baseline_avg_review_score",
            "observed_late_delivery_rate > baseline_late_delivery_rate",
        ],
        tags=["christmas", "delivery_cascade", "multi_metric"],
    ),
    GroundTruthScenario(
        scenario_id="SCN-081",
        name="Furniture and Decor Basket Mix Uplift",
        description=(
            "A home improvement campaign in October drives both average basket growth (larger "
            "furniture items) and category volume expansion, requiring decomposition to confirm "
            "whether AOV or volume is the primary GMV lever."
        ),
        primary_cause=GroundTruthRootCause(
            cause_id="average_order_value_expansion",
            dimension="average_order_value",
            dimension_value=None,
            causal_category="macro_driver",
            causal_mechanism="average_order_value",
            affected_dimension="product_category",
            affected_value="moveis_decoracao",
            expected_contribution_pct=57.0,
        ),
        secondary_causes=[
            GroundTruthRootCause(
                cause_id="furniture_category_volume_uplift",
                dimension="order_volume",
                dimension_value=None,
                causal_category="macro_driver",
                causal_mechanism="order_volume",
                affected_dimension="product_category",
                affected_value="moveis_decoracao",
                expected_contribution_pct=43.0,
            )
        ],
        distractor_causes=[
            "customer_state=SP",
            "product_category=eletrodomesticos",
            "carrier_sla_degradation",
        ],
        difficulty="medium",
        is_insufficient_evidence=False,
        target_metric="total_gmv",
        anomaly_date=date(2017, 10, 20),
        comparison_days=7,
        expected_direction="increase",
        severity="warning",
        affected_dimensions=["average_order_value", "order_volume", "product_category"],
        expected_evidence_signals=[
            "aov_contribution_pct > 45.0",
            "observed_aov > baseline_aov",
        ],
        tags=["furniture", "home_improvement", "multi_driver"],
    ),
    GroundTruthScenario(
        scenario_id="SCN-082",
        name="Mid-Year Review Score Recovery via Delivery Improvement",
        description=(
            "After a period of elevated late delivery rates, logistics improvements in June drive "
            "a platform-wide recovery in customer satisfaction scores. The challenge: establishing "
            "that the delivery improvement -- not just reduced volume -- is the causal mechanism."
        ),
        primary_cause=GroundTruthRootCause(
            cause_id="customer_satisfaction_decline",
            dimension="avg_review_score",
            dimension_value=None,
            causal_category="operational_mechanism",
            causal_mechanism="avg_review_score",
            affected_dimension="delivery",
            affected_value="late_delivery",
            expected_contribution_pct=None,
        ),
        secondary_causes=[
            GroundTruthRootCause(
                cause_id="delivery_recovery_driver",
                dimension="delivery",
                dimension_value="late_delivery",
                causal_category="operational_mechanism",
                causal_mechanism="delivery",
                affected_dimension=None,
                affected_value=None,
                expected_contribution_pct=None,
            )
        ],
        distractor_causes=[
            "order_volume_drop",
            "customer_state=SP",
            "product_category=beleza_saude",
        ],
        difficulty="medium",
        is_insufficient_evidence=False,
        target_metric="avg_review_score",
        anomaly_date=date(2017, 6, 15),
        comparison_days=7,
        expected_direction="increase",
        severity="normal",
        affected_dimensions=["avg_review_score", "delivery"],
        expected_evidence_signals=[
            "observed_avg_review_score > baseline_avg_review_score",
            "observed_late_delivery_rate < baseline_late_delivery_rate",
        ],
        tags=["sentiment", "recovery", "delivery_improvement"],
    ),
    GroundTruthScenario(
        scenario_id="SCN-083",
        name="RJ Revenue Drop Combining Volume and State Concentration",
        description=(
            "Rio de Janeiro sees a concentrated volume decline coinciding with a local logistics "
            "event, but the analysis must determine whether the RJ drop is a state-specific "
            "operational issue or a broader volume contraction that manifests most visibly in RJ."
        ),
        primary_cause=GroundTruthRootCause(
            cause_id="order_volume_drop",
            dimension="order_volume",
            dimension_value=None,
            causal_category="macro_driver",
            causal_mechanism="order_volume",
            affected_dimension="customer_state",
            affected_value="RJ",
            expected_contribution_pct=66.0,
        ),
        secondary_causes=[
            GroundTruthRootCause(
                cause_id="rj_market_contraction",
                dimension="customer_state",
                dimension_value="RJ",
                causal_category="segment_concentration",
                causal_mechanism=None,
                affected_dimension="customer_state",
                affected_value="RJ",
                expected_contribution_pct=None,
            )
        ],
        distractor_causes=[
            "average_order_value_contraction",
            "customer_state=SP",
            "carrier_sla_degradation",
        ],
        difficulty="medium",
        is_insufficient_evidence=False,
        target_metric="total_gmv",
        anomaly_date=date(2017, 4, 5),
        comparison_days=7,
        expected_direction="decrease",
        severity="warning",
        affected_dimensions=["order_volume", "customer_state"],
        expected_evidence_signals=[
            "volume_contribution_pct > 55.0",
            "observed_orders < baseline_orders",
        ],
        tags=["regional", "rj", "volume_contraction"],
    ),
    GroundTruthScenario(
        scenario_id="SCN-084",
        name="Northern Region Delivery Delay via Hub Disruption",
        description=(
            "A logistics hub disruption in Manaus causes delivery delays in AM and PA states "
            "that cascade into the national late delivery metric. The multi-state nature requires "
            "identifying the concentration dimension precisely."
        ),
        primary_cause=GroundTruthRootCause(
            cause_id="carrier_sla_degradation",
            dimension="delivery",
            dimension_value="carrier_transit_delay",
            causal_category="operational_mechanism",
            causal_mechanism="delivery",
            affected_dimension="customer_state",
            affected_value="AM",
            expected_contribution_pct=None,
        ),
        secondary_causes=[
            GroundTruthRootCause(
                cause_id="northern_region_delay_hub",
                dimension="customer_state",
                dimension_value="AM",
                causal_category="segment_concentration",
                causal_mechanism=None,
                affected_dimension="customer_state",
                affected_value="AM",
                expected_contribution_pct=None,
            )
        ],
        distractor_causes=[
            "customer_state=SP",
            "order_volume_surge",
            "product_category=ferramentas_jardim",
        ],
        difficulty="medium",
        is_insufficient_evidence=False,
        target_metric="late_delivery_rate_pct",
        anomaly_date=date(2018, 3, 20),
        comparison_days=7,
        expected_direction="increase",
        severity="warning",
        affected_dimensions=["delivery", "customer_state"],
        expected_evidence_signals=[
            "observed_late_delivery_rate > baseline_late_delivery_rate",
            "avg_delivery_days_change > 0",
        ],
        tags=["north_brazil", "logistics", "hub_disruption"],
    ),
    GroundTruthScenario(
        scenario_id="SCN-085",
        name="Sports Category Seasonal AOV Dip with Volume Stability",
        description=(
            "Post-summer clearance discounts in the esporte_lazer category compress average "
            "ticket sizes while maintaining order count. Requires distinguishing AOV compression "
            "from order volume changes to identify the correct mechanism."
        ),
        primary_cause=GroundTruthRootCause(
            cause_id="average_order_value_contraction",
            dimension="average_order_value",
            dimension_value=None,
            causal_category="macro_driver",
            causal_mechanism="average_order_value",
            affected_dimension="product_category",
            affected_value="esporte_lazer",
            expected_contribution_pct=63.0,
        ),
        secondary_causes=[
            GroundTruthRootCause(
                cause_id="sports_clearance_category_compression",
                dimension="product_category",
                dimension_value="esporte_lazer",
                causal_category="segment_concentration",
                causal_mechanism=None,
                affected_dimension="product_category",
                affected_value="esporte_lazer",
                expected_contribution_pct=None,
            )
        ],
        distractor_causes=[
            "order_volume_drop",
            "customer_state=SP",
            "product_category=cama_mesa_banho",
        ],
        difficulty="medium",
        is_insufficient_evidence=False,
        target_metric="average_order_value",
        anomaly_date=date(2018, 4, 10),
        comparison_days=7,
        expected_direction="decrease",
        severity="warning",
        affected_dimensions=["average_order_value", "product_category"],
        expected_evidence_signals=[
            "aov_contribution_pct > 50.0",
            "observed_aov < baseline_aov",
        ],
        tags=["sports", "clearance", "seasonal_aov"],
    ),
    GroundTruthScenario(
        scenario_id="SCN-086",
        name="Q2 2017 Volume Recovery with Regional Concentration",
        description=(
            "A broad market recovery in late May 2017 drives order count above baseline, but "
            "the uplift is concentrated in Sao Paulo and Rio de Janeiro."
        ),
        primary_cause=GroundTruthRootCause(
            cause_id="order_volume_surge",
            dimension="order_volume",
            dimension_value=None,
            causal_category="macro_driver",
            causal_mechanism="order_volume",
            affected_dimension="customer_state",
            affected_value="SP",
            expected_contribution_pct=60.0,
        ),
        secondary_causes=[
            GroundTruthRootCause(
                cause_id="sp_rj_acquisition_concentration",
                dimension="customer_state",
                dimension_value="SP",
                causal_category="segment_concentration",
                causal_mechanism=None,
                affected_dimension="customer_state",
                affected_value="SP",
                expected_contribution_pct=None,
            )
        ],
        distractor_causes=[
            "average_order_value_expansion",
            "customer_state=MG",
            "product_category=beleza_saude",
        ],
        difficulty="medium",
        is_insufficient_evidence=False,
        target_metric="orders_count",
        anomaly_date=date(2017, 5, 25),
        comparison_days=7,
        expected_direction="increase",
        severity="warning",
        affected_dimensions=["order_volume", "customer_state"],
        expected_evidence_signals=[
            "volume_contribution_pct > 55.0",
            "observed_orders > baseline_orders",
        ],
        tags=["q2", "recovery", "regional_concentration"],
    ),
    GroundTruthScenario(
        scenario_id="SCN-087",
        name="December Pre-Christmas Basket Mix Shift",
        description=(
            "Mid-December gift buying drives a shift toward higher-ticket items like electronics "
            "and luxury goods, expanding average basket size and lifting GMV through AOV expansion "
            "rather than through order volume, which is broadly flat versus prior week."
        ),
        primary_cause=GroundTruthRootCause(
            cause_id="average_order_value_expansion",
            dimension="average_order_value",
            dimension_value=None,
            causal_category="macro_driver",
            causal_mechanism="average_order_value",
            affected_dimension="product_category",
            affected_value="relogios_presentes",
            expected_contribution_pct=65.0,
        ),
        secondary_causes=[
            GroundTruthRootCause(
                cause_id="gifting_basket_uplift",
                dimension="product_category",
                dimension_value="relogios_presentes",
                causal_category="segment_concentration",
                causal_mechanism=None,
                affected_dimension="product_category",
                affected_value="relogios_presentes",
                expected_contribution_pct=None,
            )
        ],
        distractor_causes=[
            "order_volume_surge",
            "customer_state=SP",
            "product_category=brinquedos",
        ],
        difficulty="medium",
        is_insufficient_evidence=False,
        target_metric="average_order_value",
        anomaly_date=date(2017, 12, 15),
        comparison_days=7,
        expected_direction="increase",
        severity="warning",
        affected_dimensions=["average_order_value", "product_category"],
        expected_evidence_signals=[
            "aov_contribution_pct > 50.0",
            "observed_aov > baseline_aov",
        ],
        tags=["christmas", "gifting", "basket_shift"],
    ),
    GroundTruthScenario(
        scenario_id="SCN-088",
        name="Seller Performance Degradation Driving Review Decline",
        description=(
            "A cluster of high-volume sellers experiencing operational issues -- delayed dispatch, "
            "inadequate packaging, missing items -- drives a measurable decline in platform review "
            "scores. Distinguishing seller-driven from delivery-driven decline is non-trivial."
        ),
        primary_cause=GroundTruthRootCause(
            cause_id="customer_satisfaction_decline",
            dimension="avg_review_score",
            dimension_value=None,
            causal_category="operational_mechanism",
            causal_mechanism="avg_review_score",
            affected_dimension="seller",
            affected_value="seller_dispatch",
            expected_contribution_pct=None,
        ),
        secondary_causes=[
            GroundTruthRootCause(
                cause_id="seller_operational_failures",
                dimension="seller",
                dimension_value=None,
                causal_category="segment_concentration",
                causal_mechanism=None,
                affected_dimension="seller",
                affected_value=None,
                expected_contribution_pct=None,
            )
        ],
        distractor_causes=[
            "delivery",
            "customer_state=SP",
            "product_category=moveis_decoracao",
        ],
        difficulty="medium",
        is_insufficient_evidence=False,
        target_metric="avg_review_score",
        anomaly_date=date(2017, 9, 20),
        comparison_days=7,
        expected_direction="decrease",
        severity="warning",
        affected_dimensions=["avg_review_score", "seller"],
        expected_evidence_signals=[
            "observed_avg_review_score < baseline_avg_review_score"
        ],
        tags=["seller_quality", "operational", "reviews"],
    ),
    GroundTruthScenario(
        scenario_id="SCN-089",
        name="Tech Accessories Volume Surge with Basket Compression",
        description=(
            "A May 2018 tech accessories promotion drives volume up significantly, but the influx "
            "of low-ticket accessory orders simultaneously compresses average basket size. Total "
            "GMV rises via volume -- but the AOV signal runs counter, creating analytical noise."
        ),
        primary_cause=GroundTruthRootCause(
            cause_id="order_volume_surge",
            dimension="order_volume",
            dimension_value=None,
            causal_category="macro_driver",
            causal_mechanism="order_volume",
            affected_dimension="product_category",
            affected_value="informatica_acessorios",
            expected_contribution_pct=72.0,
        ),
        secondary_causes=[
            GroundTruthRootCause(
                cause_id="tech_accessories_concentration",
                dimension="product_category",
                dimension_value="informatica_acessorios",
                causal_category="segment_concentration",
                causal_mechanism=None,
                affected_dimension="product_category",
                affected_value="informatica_acessorios",
                expected_contribution_pct=None,
            )
        ],
        distractor_causes=[
            "average_order_value_expansion",
            "customer_state=SP",
            "product_category=eletrodomesticos",
        ],
        difficulty="medium",
        is_insufficient_evidence=False,
        target_metric="total_gmv",
        anomaly_date=date(2018, 5, 10),
        comparison_days=7,
        expected_direction="increase",
        severity="warning",
        affected_dimensions=["order_volume", "product_category"],
        expected_evidence_signals=[
            "volume_contribution_pct > 60.0",
            "observed_orders > baseline_orders",
        ],
        tags=["tech", "volume_surge", "counter_aov"],
    ),
    GroundTruthScenario(
        scenario_id="SCN-090",
        name="Black Friday Delivery Surge-Driven SLA Breach",
        description=(
            "The massive order volume surge during Black Friday week overwhelms logistics capacity, "
            "causing widespread delivery SLA breaches. The agent must distinguish between a "
            "carrier-quality issue and volume-driven capacity overload."
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
                cause_id="volume_overload_capacity_breach",
                dimension="order_volume",
                dimension_value=None,
                causal_category="macro_driver",
                causal_mechanism="order_volume",
                affected_dimension=None,
                affected_value=None,
                expected_contribution_pct=None,
            )
        ],
        distractor_causes=[
            "carrier_sla_degradation",
            "customer_state=MG",
            "product_category=cama_mesa_banho",
        ],
        difficulty="medium",
        is_insufficient_evidence=False,
        target_metric="late_delivery_rate_pct",
        anomaly_date=date(2017, 11, 28),
        comparison_days=7,
        expected_direction="increase",
        severity="critical",
        affected_dimensions=["delivery", "customer_state", "order_volume"],
        expected_evidence_signals=[
            "observed_late_delivery_rate > baseline_late_delivery_rate",
            "observed_orders > baseline_orders",
        ],
        tags=["black_friday", "logistics", "volume_overload"],
    ),
    GroundTruthScenario(
        scenario_id="SCN-091",
        name="Late October Orders Count Expansion Mixed Regional Signals",
        description=(
            "End-of-October order expansion shows broad market recovery but the signal is "
            "distributed across multiple states with none clearly dominating, making attribution "
            "to the order_volume mechanism require evidence across multiple dimensions."
        ),
        primary_cause=GroundTruthRootCause(
            cause_id="order_volume_surge",
            dimension="order_volume",
            dimension_value=None,
            causal_category="macro_driver",
            causal_mechanism="order_volume",
            affected_dimension="customer_state",
            affected_value="SP",
            expected_contribution_pct=60.0,
        ),
        secondary_causes=[
            GroundTruthRootCause(
                cause_id="broad_regional_expansion",
                dimension="customer_state",
                dimension_value="MG",
                causal_category="segment_concentration",
                causal_mechanism=None,
                affected_dimension="customer_state",
                affected_value="MG",
                expected_contribution_pct=None,
            )
        ],
        distractor_causes=[
            "average_order_value_expansion",
            "customer_state=RJ",
            "product_category=brinquedos",
        ],
        difficulty="medium",
        is_insufficient_evidence=False,
        target_metric="orders_count",
        anomaly_date=date(2017, 10, 28),
        comparison_days=7,
        expected_direction="increase",
        severity="warning",
        affected_dimensions=["order_volume", "customer_state"],
        expected_evidence_signals=[
            "volume_contribution_pct > 50.0",
            "observed_orders > baseline_orders",
        ],
        tags=["seasonal", "broad_expansion", "multi_regional"],
    ),
    GroundTruthScenario(
        scenario_id="SCN-092",
        name="Category Consolidation Revenue Contraction",
        description=(
            "A mid-year platform category consolidation removes low-performing SKUs, shifting "
            "the catalog toward fewer but higher-quality listings. AOV rises marginally but "
            "total GMV declines as volume falls due to reduced catalog breadth."
        ),
        primary_cause=GroundTruthRootCause(
            cause_id="order_volume_drop",
            dimension="order_volume",
            dimension_value=None,
            causal_category="macro_driver",
            causal_mechanism="order_volume",
            affected_dimension="product_category",
            affected_value="cama_mesa_banho",
            expected_contribution_pct=62.0,
        ),
        secondary_causes=[
            GroundTruthRootCause(
                cause_id="catalog_consolidation_volume_impact",
                dimension="product_category",
                dimension_value="cama_mesa_banho",
                causal_category="segment_concentration",
                causal_mechanism=None,
                affected_dimension="product_category",
                affected_value="cama_mesa_banho",
                expected_contribution_pct=None,
            )
        ],
        distractor_causes=[
            "average_order_value_contraction",
            "customer_state=SP",
            "carrier_sla_degradation",
        ],
        difficulty="medium",
        is_insufficient_evidence=False,
        target_metric="total_gmv",
        anomaly_date=date(2018, 6, 5),
        comparison_days=7,
        expected_direction="decrease",
        severity="warning",
        affected_dimensions=["order_volume", "product_category"],
        expected_evidence_signals=[
            "volume_contribution_pct > 50.0",
            "observed_orders < baseline_orders",
        ],
        tags=["catalog", "consolidation", "volume_impact"],
    ),
    GroundTruthScenario(
        scenario_id="SCN-093",
        name="Promotional Cadence Shift -- Structural Weekly Pattern Change",
        description=(
            "A change in promotional cadence shifts order concentration from weekends to weekdays, "
            "creating a measured weekly aggregate decline on the comparison window. The pattern "
            "requires careful baseline window interpretation."
        ),
        primary_cause=GroundTruthRootCause(
            cause_id="order_volume_drop",
            dimension="order_volume",
            dimension_value=None,
            causal_category="macro_driver",
            causal_mechanism="order_volume",
            affected_dimension="customer_state",
            affected_value="SP",
            expected_contribution_pct=63.0,
        ),
        secondary_causes=[
            GroundTruthRootCause(
                cause_id="sp_demand_pattern_shift",
                dimension="customer_state",
                dimension_value="SP",
                causal_category="segment_concentration",
                causal_mechanism=None,
                affected_dimension="customer_state",
                affected_value="SP",
                expected_contribution_pct=None,
            )
        ],
        distractor_causes=[
            "average_order_value_contraction",
            "carrier_sla_degradation",
            "product_category=esporte_lazer",
        ],
        difficulty="medium",
        is_insufficient_evidence=False,
        target_metric="orders_count",
        anomaly_date=date(2018, 7, 10),
        comparison_days=7,
        expected_direction="decrease",
        severity="warning",
        affected_dimensions=["order_volume", "customer_state"],
        expected_evidence_signals=[
            "volume_contribution_pct > 50.0",
            "observed_orders < baseline_orders",
        ],
        tags=["cadence_shift", "structural", "pattern"],
    ),
    GroundTruthScenario(
        scenario_id="SCN-094",
        name="Competitive Discount Pressure Basket Contraction",
        description=(
            "Intensifying marketplace competition in mid-2017 forces price reductions across "
            "the mid-tier product range, compressing average order value while maintaining "
            "broadly stable order volumes."
        ),
        primary_cause=GroundTruthRootCause(
            cause_id="average_order_value_contraction",
            dimension="average_order_value",
            dimension_value=None,
            causal_category="macro_driver",
            causal_mechanism="average_order_value",
            affected_dimension="product_category",
            affected_value="cama_mesa_banho",
            expected_contribution_pct=61.0,
        ),
        secondary_causes=[
            GroundTruthRootCause(
                cause_id="competitive_pricing_pressure",
                dimension="product_category",
                dimension_value="cama_mesa_banho",
                causal_category="segment_concentration",
                causal_mechanism=None,
                affected_dimension="product_category",
                affected_value="cama_mesa_banho",
                expected_contribution_pct=None,
            )
        ],
        distractor_causes=[
            "order_volume_drop",
            "customer_state=SP",
            "carrier_sla_degradation",
        ],
        difficulty="medium",
        is_insufficient_evidence=False,
        target_metric="average_order_value",
        anomaly_date=date(2017, 7, 20),
        comparison_days=7,
        expected_direction="decrease",
        severity="warning",
        affected_dimensions=["average_order_value", "product_category"],
        expected_evidence_signals=[
            "aov_contribution_pct > 50.0",
            "observed_aov < baseline_aov",
        ],
        tags=["competition", "pricing_pressure", "basket_contraction"],
    ),
    GroundTruthScenario(
        scenario_id="SCN-095",
        name="High-Frequency Delivery Issues Compounding Review Score Drop",
        description=(
            "A sustained period of elevated delivery delays produces a compounding review score "
            "decline, with multiple negative delivery review clusters appearing across categories. "
            "Distinguishing category quality issues from delivery SLA issues is required."
        ),
        primary_cause=GroundTruthRootCause(
            cause_id="customer_satisfaction_decline",
            dimension="avg_review_score",
            dimension_value=None,
            causal_category="operational_mechanism",
            causal_mechanism="avg_review_score",
            affected_dimension="delivery",
            affected_value="late_delivery",
            expected_contribution_pct=None,
        ),
        secondary_causes=[
            GroundTruthRootCause(
                cause_id="sustained_delivery_friction",
                dimension="delivery",
                dimension_value="late_delivery",
                causal_category="operational_mechanism",
                causal_mechanism="delivery",
                affected_dimension=None,
                affected_value=None,
                expected_contribution_pct=None,
            )
        ],
        distractor_causes=[
            "product_category=utilidades_domesticas",
            "seller",
            "order_volume_surge",
        ],
        difficulty="medium",
        is_insufficient_evidence=False,
        target_metric="avg_review_score",
        anomaly_date=date(2018, 4, 25),
        comparison_days=14,
        expected_direction="decrease",
        severity="warning",
        affected_dimensions=["avg_review_score", "delivery"],
        expected_evidence_signals=[
            "observed_avg_review_score < baseline_avg_review_score",
            "observed_late_delivery_rate > baseline_late_delivery_rate",
        ],
        tags=["delivery", "reviews", "sustained_degradation"],
    ),
    # --- HARD (SCN-096 to SCN-115) ---
    GroundTruthScenario(
        scenario_id="SCN-096",
        name="Near-Equal Volume vs AOV Split GMV Decline",
        description=(
            "A GMV decline shows a near-equal split between order volume contraction (51%) and "
            "average basket compression (49%). Neither driver clearly dominates; correct "
            "attribution requires precise decomposition and avoiding confirmation bias."
        ),
        primary_cause=GroundTruthRootCause(
            cause_id="order_volume_drop",
            dimension="order_volume",
            dimension_value=None,
            causal_category="macro_driver",
            causal_mechanism="order_volume",
            affected_dimension="customer_state",
            affected_value="SP",
            expected_contribution_pct=51.0,
        ),
        secondary_causes=[
            GroundTruthRootCause(
                cause_id="simultaneous_aov_compression",
                dimension="average_order_value",
                dimension_value=None,
                causal_category="macro_driver",
                causal_mechanism="average_order_value",
                affected_dimension=None,
                affected_value=None,
                expected_contribution_pct=49.0,
            )
        ],
        acceptable_alternative_causes=[
            GroundTruthRootCause(
                cause_id="average_order_value_contraction",
                dimension="average_order_value",
                dimension_value=None,
                causal_category="macro_driver",
                causal_mechanism="average_order_value",
                affected_dimension=None,
                affected_value=None,
                expected_contribution_pct=None,
            )
        ],
        distractor_causes=[
            "carrier_sla_degradation",
            "product_category=cama_mesa_banho",
            "customer_state=MG",
        ],
        difficulty="hard",
        is_insufficient_evidence=False,
        target_metric="total_gmv",
        anomaly_date=date(2017, 10, 5),
        comparison_days=7,
        expected_direction="decrease",
        severity="warning",
        affected_dimensions=["order_volume", "average_order_value", "customer_state"],
        expected_evidence_signals=[
            "volume_contribution_pct > 45.0",
            "aov_contribution_pct > 40.0",
            "observed_orders < baseline_orders",
            "observed_aov < baseline_aov",
        ],
        tags=["competing_drivers", "near_equal_split", "hard_attribution"],
    ),
    GroundTruthScenario(
        scenario_id="SCN-097",
        name="Review Score Decline: Delivery Delay or Product Quality",
        description=(
            "A review score decline in May 2018 co-occurs with both an uptick in late deliveries "
            "and a cluster of product mismatch complaints in the electronics category. "
            "Both mechanisms are plausible and the agent must weigh the evidence to identify "
            "the dominant causal pathway."
        ),
        primary_cause=GroundTruthRootCause(
            cause_id="customer_satisfaction_decline",
            dimension="avg_review_score",
            dimension_value=None,
            causal_category="operational_mechanism",
            causal_mechanism="avg_review_score",
            affected_dimension="delivery",
            affected_value="late_delivery",
            expected_contribution_pct=None,
        ),
        secondary_causes=[
            GroundTruthRootCause(
                cause_id="product_quality_mismatch_complaints",
                dimension="product_category",
                dimension_value="informatica_acessorios",
                causal_category="segment_concentration",
                causal_mechanism=None,
                affected_dimension="product_category",
                affected_value="informatica_acessorios",
                expected_contribution_pct=None,
            )
        ],
        distractor_causes=[
            "product_category=informatica_acessorios",
            "order_volume_surge",
            "customer_state=SP",
        ],
        difficulty="hard",
        is_insufficient_evidence=False,
        target_metric="avg_review_score",
        anomaly_date=date(2018, 5, 15),
        comparison_days=7,
        expected_direction="decrease",
        severity="warning",
        affected_dimensions=["avg_review_score", "delivery", "product_category"],
        expected_evidence_signals=[
            "observed_avg_review_score < baseline_avg_review_score",
            "observed_late_delivery_rate > baseline_late_delivery_rate",
        ],
        tags=["competing_review_drivers", "hard", "causal_ambiguity"],
    ),
    GroundTruthScenario(
        scenario_id="SCN-098",
        name="Seasonal Trend vs Structural Volume Decline Ambiguity",
        description=(
            "September 2017 shows a volume decline that could be attributed to seasonal "
            "back-to-school spending fatigue or to a structural acquisition channel disruption. "
            "Both hypotheses produce similar-looking data patterns, requiring multi-signal "
            "corroboration."
        ),
        primary_cause=GroundTruthRootCause(
            cause_id="order_volume_drop",
            dimension="order_volume",
            dimension_value=None,
            causal_category="macro_driver",
            causal_mechanism="order_volume",
            affected_dimension="customer_state",
            affected_value="SP",
            expected_contribution_pct=53.0,
        ),
        secondary_causes=[
            GroundTruthRootCause(
                cause_id="sp_seasonal_softening",
                dimension="customer_state",
                dimension_value="SP",
                causal_category="segment_concentration",
                causal_mechanism=None,
                affected_dimension="customer_state",
                affected_value="SP",
                expected_contribution_pct=None,
            )
        ],
        acceptable_alternative_causes=[
            GroundTruthRootCause(
                cause_id="acquisition_channel_disruption",
                dimension="order_volume",
                dimension_value=None,
                causal_category="macro_driver",
                causal_mechanism="order_volume",
                affected_dimension=None,
                affected_value=None,
                expected_contribution_pct=None,
            )
        ],
        distractor_causes=[
            "average_order_value_contraction",
            "carrier_sla_degradation",
            "product_category=esporte_lazer",
        ],
        difficulty="hard",
        is_insufficient_evidence=False,
        target_metric="orders_count",
        anomaly_date=date(2017, 9, 10),
        comparison_days=7,
        expected_direction="decrease",
        severity="warning",
        affected_dimensions=["order_volume", "customer_state"],
        expected_evidence_signals=[
            "volume_contribution_pct > 45.0",
            "observed_orders < baseline_orders",
        ],
        tags=["seasonal_vs_structural", "hard", "ambiguity"],
    ),
    GroundTruthScenario(
        scenario_id="SCN-099",
        name="Multi-Region Delivery Confusion Which State Drives the Rate",
        description=(
            "A late delivery rate spike in February 2018 is distributed across SP, MG, and RJ "
            "without a single state clearly dominating. The challenge is to determine whether "
            "this is a uniform national carrier issue or a combination of independent state events."
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
                cause_id="mg_rj_secondary_delay",
                dimension="customer_state",
                dimension_value="MG",
                causal_category="segment_concentration",
                causal_mechanism=None,
                affected_dimension="customer_state",
                affected_value="MG",
                expected_contribution_pct=None,
            )
        ],
        distractor_causes=[
            "customer_state=RJ",
            "order_volume_surge",
            "product_category=cama_mesa_banho",
        ],
        difficulty="hard",
        is_insufficient_evidence=False,
        target_metric="late_delivery_rate_pct",
        anomaly_date=date(2018, 2, 20),
        comparison_days=7,
        expected_direction="increase",
        severity="warning",
        affected_dimensions=["delivery", "customer_state"],
        expected_evidence_signals=[
            "observed_late_delivery_rate > baseline_late_delivery_rate",
            "avg_delivery_days_change > 0",
        ],
        tags=["multi_state", "carrier", "hard_attribution"],
    ),
    GroundTruthScenario(
        scenario_id="SCN-100",
        name="Early Holiday Volume Surge with Countervailing AOV Noise",
        description=(
            "Early December 2016 shows strong order growth but the simultaneous influx of small "
            "accessory orders from holiday promotions compresses average basket value, creating "
            "noise in the decomposition. Volume dominates but the negative AOV signal creates "
            "attribution ambiguity."
        ),
        primary_cause=GroundTruthRootCause(
            cause_id="order_volume_surge",
            dimension="order_volume",
            dimension_value=None,
            causal_category="macro_driver",
            causal_mechanism="order_volume",
            affected_dimension="customer_state",
            affected_value="SP",
            expected_contribution_pct=73.0,
        ),
        secondary_causes=[
            GroundTruthRootCause(
                cause_id="holiday_basket_compression_noise",
                dimension="average_order_value",
                dimension_value=None,
                causal_category="macro_driver",
                causal_mechanism="average_order_value",
                affected_dimension=None,
                affected_value=None,
                expected_contribution_pct=None,
            )
        ],
        distractor_causes=[
            "average_order_value_contraction",
            "product_category=brinquedos",
            "customer_state=RJ",
        ],
        difficulty="hard",
        is_insufficient_evidence=False,
        target_metric="total_gmv",
        anomaly_date=date(2017, 12, 10),
        comparison_days=7,
        expected_direction="increase",
        severity="warning",
        affected_dimensions=["order_volume", "average_order_value", "customer_state"],
        expected_evidence_signals=[
            "volume_contribution_pct > 60.0",
            "observed_orders > baseline_orders",
        ],
        tags=["holiday", "noisy_decomposition", "hard"],
    ),
    GroundTruthScenario(
        scenario_id="SCN-101",
        name="Category Shift or Order Volume Drop Ambiguous GMV Decline",
        description=(
            "A July 2017 GMV decline can be explained by either an AOV contraction caused by "
            "category mix shift toward cheaper items, or a genuine order volume drop. "
            "Both signals appear simultaneously at comparable magnitudes."
        ),
        primary_cause=GroundTruthRootCause(
            cause_id="average_order_value_contraction",
            dimension="average_order_value",
            dimension_value=None,
            causal_category="macro_driver",
            causal_mechanism="average_order_value",
            affected_dimension="product_category",
            affected_value="beleza_saude",
            expected_contribution_pct=53.0,
        ),
        secondary_causes=[
            GroundTruthRootCause(
                cause_id="order_volume_mild_softening",
                dimension="order_volume",
                dimension_value=None,
                causal_category="macro_driver",
                causal_mechanism="order_volume",
                affected_dimension=None,
                affected_value=None,
                expected_contribution_pct=47.0,
            )
        ],
        acceptable_alternative_causes=[
            GroundTruthRootCause(
                cause_id="order_volume_drop",
                dimension="order_volume",
                dimension_value=None,
                causal_category="macro_driver",
                causal_mechanism="order_volume",
                affected_dimension=None,
                affected_value=None,
                expected_contribution_pct=None,
            )
        ],
        distractor_causes=[
            "carrier_sla_degradation",
            "customer_state=RJ",
            "product_category=cama_mesa_banho",
        ],
        difficulty="hard",
        is_insufficient_evidence=False,
        target_metric="total_gmv",
        anomaly_date=date(2017, 7, 25),
        comparison_days=7,
        expected_direction="decrease",
        severity="warning",
        affected_dimensions=["average_order_value", "order_volume", "product_category"],
        expected_evidence_signals=[
            "aov_contribution_pct > 45.0",
            "volume_contribution_pct > 40.0",
            "observed_aov < baseline_aov",
        ],
        tags=["competing_drivers", "ambiguous", "hard"],
    ),
    GroundTruthScenario(
        scenario_id="SCN-102",
        name="Review Score Decline Delivery SLA or Furniture Product Quality",
        description=(
            "An August 2017 review score decline shows elevated late delivery rates in SP alongside "
            "a cluster of product quality complaints in furniture. Both mechanisms produce negative "
            "reviews; the delivery signal is slightly more prevalent but product signal is louder."
        ),
        primary_cause=GroundTruthRootCause(
            cause_id="customer_satisfaction_decline",
            dimension="avg_review_score",
            dimension_value=None,
            causal_category="operational_mechanism",
            causal_mechanism="avg_review_score",
            affected_dimension="delivery",
            affected_value="late_delivery",
            expected_contribution_pct=None,
        ),
        secondary_causes=[
            GroundTruthRootCause(
                cause_id="furniture_product_quality_complaints",
                dimension="product_category",
                dimension_value="moveis_decoracao",
                causal_category="segment_concentration",
                causal_mechanism=None,
                affected_dimension="product_category",
                affected_value="moveis_decoracao",
                expected_contribution_pct=None,
            )
        ],
        distractor_causes=[
            "product_category=moveis_decoracao",
            "order_volume_surge",
            "customer_state=SP",
        ],
        difficulty="hard",
        is_insufficient_evidence=False,
        target_metric="avg_review_score",
        anomaly_date=date(2017, 8, 25),
        comparison_days=7,
        expected_direction="decrease",
        severity="warning",
        affected_dimensions=["avg_review_score", "delivery", "product_category"],
        expected_evidence_signals=[
            "observed_avg_review_score < baseline_avg_review_score"
        ],
        tags=["review_ambiguity", "hard", "competing_quality_signals"],
    ),
    GroundTruthScenario(
        scenario_id="SCN-103",
        name="Multi-Carrier SLA vs Peak Volume Late Delivery Black Friday",
        description=(
            "Black Friday 2017 late delivery spike raises the question: is this a carrier SLA "
            "failure or pure volume overload? Both explanations are plausible given the concurrent "
            "order surge, requiring the agent to separate volume-driven delays from SLA degradation."
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
                cause_id="volume_surge_overload",
                dimension="order_volume",
                dimension_value=None,
                causal_category="macro_driver",
                causal_mechanism="order_volume",
                affected_dimension=None,
                affected_value=None,
                expected_contribution_pct=None,
            )
        ],
        distractor_causes=[
            "carrier_sla_degradation",
            "customer_state=MG",
            "product_category=eletrodomesticos",
        ],
        difficulty="hard",
        is_insufficient_evidence=False,
        target_metric="late_delivery_rate_pct",
        anomaly_date=date(2017, 11, 30),
        comparison_days=7,
        expected_direction="increase",
        severity="critical",
        affected_dimensions=["delivery", "customer_state", "order_volume"],
        expected_evidence_signals=[
            "observed_late_delivery_rate > baseline_late_delivery_rate",
            "observed_orders > baseline_orders",
        ],
        tags=["black_friday", "delivery", "competing_explanations"],
    ),
    GroundTruthScenario(
        scenario_id="SCN-104",
        name="Platform Revenue Softening Volume or Pricing Pressure",
        description=(
            "January 2018 shows a GMV decline that could be attributed to post-holiday volume "
            "exhaustion or to January clearance pricing compressing average order values. "
            "The competitive pricing signal is present but the volume signal is slightly stronger."
        ),
        primary_cause=GroundTruthRootCause(
            cause_id="order_volume_drop",
            dimension="order_volume",
            dimension_value=None,
            causal_category="macro_driver",
            causal_mechanism="order_volume",
            affected_dimension="customer_state",
            affected_value="SP",
            expected_contribution_pct=55.0,
        ),
        secondary_causes=[
            GroundTruthRootCause(
                cause_id="january_clearance_aov_compression",
                dimension="average_order_value",
                dimension_value=None,
                causal_category="macro_driver",
                causal_mechanism="average_order_value",
                affected_dimension=None,
                affected_value=None,
                expected_contribution_pct=45.0,
            )
        ],
        distractor_causes=[
            "carrier_sla_degradation",
            "customer_state=MG",
            "product_category=cama_mesa_banho",
        ],
        difficulty="hard",
        is_insufficient_evidence=False,
        target_metric="total_gmv",
        anomaly_date=date(2018, 1, 10),
        comparison_days=14,
        expected_direction="decrease",
        severity="warning",
        affected_dimensions=["order_volume", "average_order_value", "customer_state"],
        expected_evidence_signals=[
            "volume_contribution_pct > 45.0",
            "aov_contribution_pct > 35.0",
            "observed_orders < baseline_orders",
        ],
        tags=["january", "competing_drivers", "hard"],
    ),
    GroundTruthScenario(
        scenario_id="SCN-105",
        name="Ambiguous Weekly Fluctuation Insufficient Evidence",
        description=(
            "Early October 2016 shows a modest order count variation that falls within normal "
            "weekly statistical noise. Multiple mechanisms are weakly suggested but none produces "
            "a clear dominant signal, representing a genuinely insufficient evidence case."
        ),
        primary_cause=GroundTruthRootCause(
            cause_id="order_volume_drop",
            dimension="order_volume",
            dimension_value=None,
            causal_category="macro_driver",
            causal_mechanism="order_volume",
            affected_dimension="customer_state",
            affected_value="SP",
            expected_contribution_pct=None,
        ),
        secondary_causes=[],
        distractor_causes=[
            "average_order_value_contraction",
            "carrier_sla_degradation",
            "product_category=beleza_saude",
        ],
        difficulty="hard",
        is_insufficient_evidence=True,
        target_metric="orders_count",
        anomaly_date=date(2016, 10, 5),
        comparison_days=7,
        expected_direction="normal",
        severity="normal",
        affected_dimensions=["order_volume"],
        expected_evidence_signals=[
            "observed_value within_noise_threshold",
            "no_dominant_signal",
        ],
        tags=["insufficient_evidence", "noise", "ambiguous"],
    ),
    GroundTruthScenario(
        scenario_id="SCN-106",
        name="SP-Driven vs Category-Driven GMV Decline Correlated Dimensions",
        description=(
            "A March 2018 revenue drop is explained partly by SP order softening and partly by "
            "a volume decline in the cama_mesa_banho category. Both dimensions are correlated -- "
            "SP is the main buyer of that category -- making clean causal attribution difficult."
        ),
        primary_cause=GroundTruthRootCause(
            cause_id="order_volume_drop",
            dimension="order_volume",
            dimension_value=None,
            causal_category="macro_driver",
            causal_mechanism="order_volume",
            affected_dimension="customer_state",
            affected_value="SP",
            expected_contribution_pct=57.0,
        ),
        secondary_causes=[
            GroundTruthRootCause(
                cause_id="bed_bath_category_volume_drop",
                dimension="product_category",
                dimension_value="cama_mesa_banho",
                causal_category="segment_concentration",
                causal_mechanism=None,
                affected_dimension="product_category",
                affected_value="cama_mesa_banho",
                expected_contribution_pct=None,
            )
        ],
        distractor_causes=[
            "average_order_value_contraction",
            "customer_state=RJ",
            "carrier_sla_degradation",
        ],
        difficulty="hard",
        is_insufficient_evidence=False,
        target_metric="total_gmv",
        anomaly_date=date(2018, 3, 10),
        comparison_days=7,
        expected_direction="decrease",
        severity="warning",
        affected_dimensions=["order_volume", "customer_state", "product_category"],
        expected_evidence_signals=[
            "volume_contribution_pct > 45.0",
            "observed_orders < baseline_orders",
        ],
        tags=["correlated_dimensions", "sp_category_overlap", "hard"],
    ),
    GroundTruthScenario(
        scenario_id="SCN-107",
        name="AOV Contraction vs Volume Surge Net Positive GMV",
        description=(
            "June 2017 shows a net GMV increase driven by order volume surge, but a concurrent "
            "AOV contraction partially offsets it. The agent must correctly decompose the competing "
            "effects and identify volume as the net positive driver despite AOV headwinds."
        ),
        primary_cause=GroundTruthRootCause(
            cause_id="order_volume_surge",
            dimension="order_volume",
            dimension_value=None,
            causal_category="macro_driver",
            causal_mechanism="order_volume",
            affected_dimension="customer_state",
            affected_value="SP",
            expected_contribution_pct=68.0,
        ),
        secondary_causes=[
            GroundTruthRootCause(
                cause_id="aov_headwind_offset",
                dimension="average_order_value",
                dimension_value=None,
                causal_category="macro_driver",
                causal_mechanism="average_order_value",
                affected_dimension=None,
                affected_value=None,
                expected_contribution_pct=None,
            )
        ],
        distractor_causes=[
            "average_order_value_expansion",
            "customer_state=MG",
            "product_category=cama_mesa_banho",
        ],
        difficulty="hard",
        is_insufficient_evidence=False,
        target_metric="total_gmv",
        anomaly_date=date(2017, 6, 5),
        comparison_days=7,
        expected_direction="increase",
        severity="warning",
        affected_dimensions=["order_volume", "average_order_value", "customer_state"],
        expected_evidence_signals=[
            "volume_contribution_pct > 55.0",
            "observed_orders > baseline_orders",
            "observed_aov < baseline_aov",
        ],
        tags=["counter_aov", "hard_decomposition", "competing_effects"],
    ),
    GroundTruthScenario(
        scenario_id="SCN-108",
        name="Delivery Delay Plus Seller Quality Dual Mechanism Late Delivery",
        description=(
            "A June 2018 late delivery spike is caused jointly by carrier SLA failures in SP "
            "and by a cluster of large sellers failing to dispatch orders on time. Attributing "
            "to carrier vs seller is non-trivial without examining dispatch timing data."
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
                cause_id="seller_dispatch_delay_contribution",
                dimension="seller",
                dimension_value=None,
                causal_category="segment_concentration",
                causal_mechanism=None,
                affected_dimension="seller",
                affected_value=None,
                expected_contribution_pct=None,
            )
        ],
        distractor_causes=[
            "order_volume_surge",
            "product_category=moveis_decoracao",
            "customer_state=MG",
        ],
        difficulty="hard",
        is_insufficient_evidence=False,
        target_metric="late_delivery_rate_pct",
        anomaly_date=date(2018, 6, 15),
        comparison_days=7,
        expected_direction="increase",
        severity="warning",
        affected_dimensions=["delivery", "customer_state", "seller"],
        expected_evidence_signals=[
            "observed_late_delivery_rate > baseline_late_delivery_rate",
            "avg_delivery_days_change > 0",
        ],
        tags=["dual_mechanism", "seller_vs_carrier", "hard"],
    ),
    GroundTruthScenario(
        scenario_id="SCN-109",
        name="Review Score Decline Small Sample Size Early Dataset",
        description=(
            "Early Olist data in October 2016 shows a modest review score decline, but the "
            "sample size of reviews in this early period is small, making the signal noisy. "
            "The agent must weigh whether the decline is statistically meaningful."
        ),
        primary_cause=GroundTruthRootCause(
            cause_id="customer_satisfaction_decline",
            dimension="avg_review_score",
            dimension_value=None,
            causal_category="operational_mechanism",
            causal_mechanism="avg_review_score",
            affected_dimension="delivery",
            affected_value="late_delivery",
            expected_contribution_pct=None,
        ),
        secondary_causes=[],
        distractor_causes=[
            "product_category=utilidades_domesticas",
            "order_volume_drop",
            "seller",
        ],
        difficulty="hard",
        is_insufficient_evidence=True,
        target_metric="avg_review_score",
        anomaly_date=date(2017, 1, 25),
        comparison_days=7,
        expected_direction="decrease",
        severity="normal",
        affected_dimensions=["avg_review_score"],
        expected_evidence_signals=[
            "observed_avg_review_score < baseline_avg_review_score"
        ],
        tags=["small_sample", "noise", "early_data", "hard"],
    ),
    GroundTruthScenario(
        scenario_id="SCN-110",
        name="Volume to Delivery to Review Causal Chain Investigation",
        description=(
            "A prior-week volume surge overwhelmed logistics, elevated late delivery rates, and "
            "then cascaded into a review score decline. This scenario tests whether the agent can "
            "trace back through a multi-step causal chain to identify the originating volume "
            "contraction as the current-week root cause."
        ),
        primary_cause=GroundTruthRootCause(
            cause_id="order_volume_drop",
            dimension="order_volume",
            dimension_value=None,
            causal_category="macro_driver",
            causal_mechanism="order_volume",
            affected_dimension="customer_state",
            affected_value="SP",
            expected_contribution_pct=62.0,
        ),
        secondary_causes=[
            GroundTruthRootCause(
                cause_id="sp_volume_softening_march",
                dimension="customer_state",
                dimension_value="SP",
                causal_category="segment_concentration",
                causal_mechanism=None,
                affected_dimension="customer_state",
                affected_value="SP",
                expected_contribution_pct=None,
            )
        ],
        distractor_causes=[
            "average_order_value_contraction",
            "carrier_sla_degradation",
            "product_category=beleza_saude",
        ],
        difficulty="hard",
        is_insufficient_evidence=False,
        target_metric="orders_count",
        anomaly_date=date(2017, 3, 1),
        comparison_days=7,
        expected_direction="decrease",
        severity="warning",
        affected_dimensions=["order_volume", "customer_state"],
        expected_evidence_signals=[
            "volume_contribution_pct > 50.0",
            "observed_orders < baseline_orders",
        ],
        tags=["causal_chain", "multi_metric", "hard"],
    ),
    GroundTruthScenario(
        scenario_id="SCN-111",
        name="Competing Category Mix Shifts in AOV Hard Attribution",
        description=(
            "September 2017 GMV growth is partially explained by rising AOV driven by electronics, "
            "but simultaneously offset by a category shift toward low-ticket fashion goods. "
            "The net AOV effect is positive but requires disentangling two opposing category "
            "movements."
        ),
        primary_cause=GroundTruthRootCause(
            cause_id="average_order_value_expansion",
            dimension="average_order_value",
            dimension_value=None,
            causal_category="macro_driver",
            causal_mechanism="average_order_value",
            affected_dimension="product_category",
            affected_value="eletrodomesticos",
            expected_contribution_pct=56.0,
        ),
        secondary_causes=[
            GroundTruthRootCause(
                cause_id="order_volume_moderate_uplift",
                dimension="order_volume",
                dimension_value=None,
                causal_category="macro_driver",
                causal_mechanism="order_volume",
                affected_dimension=None,
                affected_value=None,
                expected_contribution_pct=44.0,
            )
        ],
        distractor_causes=[
            "product_category=beleza_saude",
            "customer_state=SP",
            "carrier_sla_degradation",
        ],
        difficulty="hard",
        is_insufficient_evidence=False,
        target_metric="total_gmv",
        anomaly_date=date(2017, 9, 25),
        comparison_days=7,
        expected_direction="increase",
        severity="warning",
        affected_dimensions=["average_order_value", "order_volume", "product_category"],
        expected_evidence_signals=[
            "aov_contribution_pct > 45.0",
            "observed_aov > baseline_aov",
        ],
        tags=["competing_category_shifts", "aov_attribution", "hard"],
    ),
    GroundTruthScenario(
        scenario_id="SCN-112",
        name="Volume-Led Revenue Recovery Ambiguous Segment Attribution",
        description=(
            "A July 2018 GMV recovery shows volume growth but the state-level attribution is "
            "ambiguous: SP leads, but MG and PR show disproportionate growth relative to their "
            "baseline. Correct attribution to the macro order_volume mechanism requires "
            "distinguishing which segment is primary."
        ),
        primary_cause=GroundTruthRootCause(
            cause_id="order_volume_surge",
            dimension="order_volume",
            dimension_value=None,
            causal_category="macro_driver",
            causal_mechanism="order_volume",
            affected_dimension="customer_state",
            affected_value="SP",
            expected_contribution_pct=59.0,
        ),
        secondary_causes=[
            GroundTruthRootCause(
                cause_id="mg_pr_secondary_volume_contribution",
                dimension="customer_state",
                dimension_value="MG",
                causal_category="segment_concentration",
                causal_mechanism=None,
                affected_dimension="customer_state",
                affected_value="MG",
                expected_contribution_pct=None,
            )
        ],
        distractor_causes=[
            "average_order_value_expansion",
            "customer_state=MG",
            "product_category=ferramentas_jardim",
        ],
        difficulty="hard",
        is_insufficient_evidence=False,
        target_metric="total_gmv",
        anomaly_date=date(2018, 7, 15),
        comparison_days=7,
        expected_direction="increase",
        severity="warning",
        affected_dimensions=["order_volume", "customer_state"],
        expected_evidence_signals=[
            "volume_contribution_pct > 50.0",
            "observed_orders > baseline_orders",
        ],
        tags=["segment_ambiguity", "recovery", "hard"],
    ),
    GroundTruthScenario(
        scenario_id="SCN-113",
        name="Multi-Cause Late Delivery Insufficient Analytical Evidence",
        description=(
            "May 2017 shows elevated late delivery rates coinciding with multiple potential "
            "causes: a partial freight work-to-rule action, regional flooding in Bahia, and a "
            "concurrent peak in furniture deliveries. The evidence is too diffuse to isolate a "
            "single root cause with confidence."
        ),
        primary_cause=GroundTruthRootCause(
            cause_id="carrier_sla_degradation",
            dimension="delivery",
            dimension_value="carrier_transit_delay",
            causal_category="operational_mechanism",
            causal_mechanism="delivery",
            affected_dimension="customer_state",
            affected_value="BA",
            expected_contribution_pct=None,
        ),
        secondary_causes=[],
        distractor_causes=[
            "order_volume_surge",
            "customer_state=SP",
            "product_category=moveis_decoracao",
        ],
        difficulty="hard",
        is_insufficient_evidence=True,
        target_metric="late_delivery_rate_pct",
        anomaly_date=date(2017, 5, 10),
        comparison_days=7,
        expected_direction="increase",
        severity="warning",
        affected_dimensions=["delivery", "customer_state"],
        expected_evidence_signals=[
            "observed_late_delivery_rate > baseline_late_delivery_rate"
        ],
        tags=["insufficient_evidence", "multi_cause", "ambiguous_delivery"],
    ),
    GroundTruthScenario(
        scenario_id="SCN-114",
        name="Seasonal vs Operational Delivery Delay July 2017",
        description=(
            "A late delivery rate increase in July 2017 coincides with the Brazilian winter "
            "holiday school break, which drives volume in toy and book categories, but also "
            "with a reported carrier network reconfiguration. Seasonal volume effects and "
            "operational carrier changes are competing explanations."
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
                cause_id="winter_holiday_volume_overload",
                dimension="order_volume",
                dimension_value=None,
                causal_category="macro_driver",
                causal_mechanism="order_volume",
                affected_dimension=None,
                affected_value=None,
                expected_contribution_pct=None,
            )
        ],
        acceptable_alternative_causes=[
            GroundTruthRootCause(
                cause_id="logistics_fulfillment_bottleneck",
                dimension="delivery",
                dimension_value="late_delivery",
                causal_category="operational_mechanism",
                causal_mechanism="delivery",
                affected_dimension="customer_state",
                affected_value="SP",
                expected_contribution_pct=None,
            )
        ],
        distractor_causes=[
            "product_category=brinquedos",
            "customer_state=RJ",
            "average_order_value_expansion",
        ],
        difficulty="hard",
        is_insufficient_evidence=False,
        target_metric="late_delivery_rate_pct",
        anomaly_date=date(2017, 7, 20),
        comparison_days=7,
        expected_direction="increase",
        severity="warning",
        affected_dimensions=["delivery", "customer_state", "order_volume"],
        expected_evidence_signals=[
            "observed_late_delivery_rate > baseline_late_delivery_rate",
            "avg_delivery_days_change > 0",
        ],
        tags=["seasonal_vs_operational", "delivery", "competing_explanations"],
    ),
    GroundTruthScenario(
        scenario_id="SCN-115",
        name="End-of-Dataset August 2018 Volume Trend Ambiguity",
        description=(
            "The final weeks of the Olist dataset (August 2018) show a volume decline that could "
            "reflect genuine market softening, truncated data coverage, or the tail of the "
            "Brazilian truckers strike aftermath. Minimal historical comparison context makes "
            "confident attribution challenging."
        ),
        primary_cause=GroundTruthRootCause(
            cause_id="order_volume_drop",
            dimension="order_volume",
            dimension_value=None,
            causal_category="macro_driver",
            causal_mechanism="order_volume",
            affected_dimension="customer_state",
            affected_value="SP",
            expected_contribution_pct=60.0,
        ),
        secondary_causes=[
            GroundTruthRootCause(
                cause_id="sp_end_of_dataset_softening",
                dimension="customer_state",
                dimension_value="SP",
                causal_category="segment_concentration",
                causal_mechanism=None,
                affected_dimension="customer_state",
                affected_value="SP",
                expected_contribution_pct=None,
            )
        ],
        acceptable_alternative_causes=[
            GroundTruthRootCause(
                cause_id="truckers_strike_aftermath",
                dimension="order_volume",
                dimension_value=None,
                causal_category="macro_driver",
                causal_mechanism="order_volume",
                affected_dimension=None,
                affected_value=None,
                expected_contribution_pct=None,
            )
        ],
        distractor_causes=[
            "average_order_value_contraction",
            "carrier_sla_degradation",
            "product_category=ferramentas_jardim",
        ],
        difficulty="hard",
        is_insufficient_evidence=False,
        target_metric="total_gmv",
        anomaly_date=date(2018, 8, 10),
        comparison_days=7,
        expected_direction="decrease",
        severity="warning",
        affected_dimensions=["order_volume", "customer_state"],
        expected_evidence_signals=[
            "volume_contribution_pct > 50.0",
            "observed_orders < baseline_orders",
        ],
        tags=["dataset_end", "truckers_strike", "hard_attribution"],
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
