"""Synthetic and Canonical Scenarios for Change-Point Evaluation (Phase L)."""

from datetime import date, timedelta

from pydantic import BaseModel, Field

from apps.analytics.anomaly.models import DailyKPIObservation
from apps.analytics.change_point.models import RegimeType


class ChangePointScenario(BaseModel):
    """Benchmark test scenario for change-point and regime-shift detectors."""

    scenario_id: str
    name: str
    description: str
    metric: str
    expected_change_point: bool
    expected_regime: RegimeType
    expected_change_date: date | None = None
    expected_mean_shift_pct: float | None = None
    expected_variance_shift: bool = False
    observations: list[DailyKPIObservation] = Field(default_factory=list)


def build_change_point_scenarios() -> list[ChangePointScenario]:
    """Generate 10 deterministic benchmark scenarios for change-point evaluation."""
    base_date = date(2017, 1, 1)
    scenarios: list[ChangePointScenario] = []

    # 1. Scenario 01: Clear Upward Regime Shift (+60% on day 10)
    obs_01: list[DailyKPIObservation] = []
    for i in range(20):
        d = base_date + timedelta(days=i)
        base_val = 100.0 if i < 10 else 160.0
        val = base_val + (i % 3 - 1) * 2.5
        obs_01.append(DailyKPIObservation(date=d, metric="total_gmv", value=val))

    scenarios.append(
        ChangePointScenario(
            scenario_id="CP-SCN-01",
            name="Clear Upward Regime Shift",
            description="Permanent structural shift from R$ 100 to R$ 160.",
            metric="total_gmv",
            expected_change_point=True,
            expected_regime="sustained_level_shift",
            expected_change_date=base_date + timedelta(days=10),
            expected_mean_shift_pct=60.0,
            expected_variance_shift=False,
            observations=obs_01,
        )
    )

    # 2. Scenario 02: Clear Downward Regime Shift (-40% on day 10)
    obs_02: list[DailyKPIObservation] = []
    for i in range(20):
        d = base_date + timedelta(days=i)
        base_val = 150.0 if i < 10 else 90.0
        val = base_val + (i % 3 - 1) * 2.0
        obs_02.append(DailyKPIObservation(date=d, metric="total_gmv", value=val))

    scenarios.append(
        ChangePointScenario(
            scenario_id="CP-SCN-02",
            name="Clear Downward Regime Shift",
            description="Structural demand contraction from R$ 150 to R$ 90.",
            metric="total_gmv",
            expected_change_point=True,
            expected_regime="sustained_level_shift",
            expected_change_date=base_date + timedelta(days=10),
            expected_mean_shift_pct=-40.0,
            expected_variance_shift=False,
            observations=obs_02,
        )
    )

    # 3. Scenario 03: Temporary Spike (Day 10 spike reverting to baseline)
    obs_03: list[DailyKPIObservation] = []
    for i in range(20):
        d = base_date + timedelta(days=i)
        val = 250.0 if i == 10 else (100.0 + (i % 3 - 1) * 2.0)
        obs_03.append(DailyKPIObservation(date=d, metric="total_gmv", value=val))

    scenarios.append(
        ChangePointScenario(
            scenario_id="CP-SCN-03",
            name="Temporary Spike with Baseline Reversion",
            description="Single-day extreme demand spike returning to baseline.",
            metric="total_gmv",
            expected_change_point=False,
            expected_regime="isolated_anomaly",
            expected_change_date=None,
            expected_mean_shift_pct=None,
            expected_variance_shift=False,
            observations=obs_03,
        )
    )

    # 4. Scenario 04: Gradual Linear Trend without Break
    obs_04: list[DailyKPIObservation] = []
    for i in range(20):
        d = base_date + timedelta(days=i)
        val = 100.0 + 3.0 * float(i) + (i % 2 - 0.5) * 1.0
        obs_04.append(DailyKPIObservation(date=d, metric="total_gmv", value=val))

    scenarios.append(
        ChangePointScenario(
            scenario_id="CP-SCN-04",
            name="Gradual Linear Trend without Break",
            description="Steady monotonic growth across window without break.",
            metric="total_gmv",
            expected_change_point=False,
            expected_regime="gradual_trend",
            expected_change_date=None,
            expected_mean_shift_pct=None,
            expected_variance_shift=False,
            observations=obs_04,
        )
    )

    # 5. Scenario 05: Variance Regime Change (Equal means, 10x volatility expansion)
    obs_05: list[DailyKPIObservation] = []
    for i in range(24):
        d = base_date + timedelta(days=i)
        val = 100.0 + (2.0 if i < 12 else 20.0) * (1.0 if i % 2 == 0 else -1.0)
        obs_05.append(DailyKPIObservation(date=d, metric="total_gmv", value=val))

    scenarios.append(
        ChangePointScenario(
            scenario_id="CP-SCN-05",
            name="Variance Regime Change (Volatility Expansion)",
            description="Stable mean around R$ 100 with volatility expansion.",
            metric="total_gmv",
            expected_change_point=True,
            expected_regime="variance_regime_shift",
            expected_change_date=base_date + timedelta(days=12),
            expected_mean_shift_pct=0.0,
            expected_variance_shift=True,
            observations=obs_05,
        )
    )

    # 6. Scenario 06: Very Noisy Series without Structural Break
    obs_06: list[DailyKPIObservation] = []
    for i in range(20):
        d = base_date + timedelta(days=i)
        val = 100.0 + (i % 5 - 2) * 8.0
        obs_06.append(DailyKPIObservation(date=d, metric="total_gmv", value=val))

    scenarios.append(
        ChangePointScenario(
            scenario_id="CP-SCN-06",
            name="Very Noisy Series without Structural Break",
            description="High background variance with stationary noise.",
            metric="total_gmv",
            expected_change_point=False,
            expected_regime="normal",
            expected_change_date=None,
            expected_mean_shift_pct=None,
            expected_variance_shift=False,
            observations=obs_06,
        )
    )

    # 7. Scenario 07: Insufficient History (n < 4)
    obs_07: list[DailyKPIObservation] = []
    for i in range(3):
        d = base_date + timedelta(days=i)
        obs_07.append(DailyKPIObservation(date=d, metric="total_gmv", value=100.0 + i))

    scenarios.append(
        ChangePointScenario(
            scenario_id="CP-SCN-07",
            name="Insufficient History",
            description="Short time series (3 days) below minimum segment threshold.",
            metric="total_gmv",
            expected_change_point=False,
            expected_regime="insufficient_data",
            expected_change_date=None,
            expected_mean_shift_pct=None,
            expected_variance_shift=False,
            observations=obs_07,
        )
    )

    # 8. Scenario 08: Constant Series (Zero Variance)
    obs_08: list[DailyKPIObservation] = []
    for i in range(15):
        d = base_date + timedelta(days=i)
        obs_08.append(DailyKPIObservation(date=d, metric="total_gmv", value=100.0))

    scenarios.append(
        ChangePointScenario(
            scenario_id="CP-SCN-08",
            name="Constant Series with Zero Variance",
            description="Completely flat time series with zero variance.",
            metric="total_gmv",
            expected_change_point=False,
            expected_regime="normal",
            expected_change_date=None,
            expected_mean_shift_pct=0.0,
            expected_variance_shift=False,
            observations=obs_08,
        )
    )

    # 9. Scenario 09: Single Outlier Without Regime Change
    obs_09: list[DailyKPIObservation] = []
    for i in range(18):
        d = base_date + timedelta(days=i)
        val = 180.0 if i == 5 else (100.0 + (i % 2 - 0.5) * 2.0)
        obs_09.append(DailyKPIObservation(date=d, metric="total_gmv", value=val))

    scenarios.append(
        ChangePointScenario(
            scenario_id="CP-SCN-09",
            name="Outlier Without Regime Change",
            description="Early single-day outlier returning immediately to baseline.",
            metric="total_gmv",
            expected_change_point=False,
            expected_regime="isolated_anomaly",
            expected_change_date=None,
            expected_mean_shift_pct=None,
            expected_variance_shift=False,
            observations=obs_09,
        )
    )

    # 10. Scenario 10: Change Point Preceding Anomaly with Missing Dates
    obs_10: list[DailyKPIObservation] = []
    for i in range(20):
        d = base_date + timedelta(days=i)
        obs_val: float | None = (
            None if i in (3, 7, 15) else (100.0 if i < 10 else 170.0)
        )
        obs_10.append(DailyKPIObservation(date=d, metric="total_gmv", value=obs_val))

    scenarios.append(
        ChangePointScenario(
            scenario_id="CP-SCN-10",
            name="Change Point Preceding Anomaly with Missing Dates",
            description="Time series with intermittent nulls and structural shift.",
            metric="total_gmv",
            expected_change_point=True,
            expected_regime="sustained_level_shift",
            expected_change_date=base_date + timedelta(days=10),
            expected_mean_shift_pct=70.0,
            expected_variance_shift=False,
            observations=obs_10,
        )
    )

    return scenarios
