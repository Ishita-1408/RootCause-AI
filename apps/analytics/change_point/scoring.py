"""Persistence Scoring & Method Selection Engine for Change-Point Analysis (Phase L)."""

from collections.abc import Sequence

from apps.analytics.change_point.models import (
    DetectionMethod,
    PersistenceClassification,
    RegimeType,
)


def select_detection_method(
    n_observations: int,
    requested_method: str = "auto",
) -> DetectionMethod:
    """Deterministically select optimal change-point detector based on sample size."""
    if n_observations < 3:
        return "insufficient_data"

    if requested_method != "auto":
        valid_methods = (
            "pelt",
            "cusum",
            "rolling_baseline",
            "welch_binary_segmentation",
        )
        if requested_method in valid_methods:
            return requested_method  # type: ignore[return-value]

    # Smart Auto-Selection Policy
    if n_observations >= 14:
        return "pelt"
    elif n_observations >= 7:
        return "cusum"
    else:
        return "rolling_baseline"


def evaluate_persistence(
    values: Sequence[float],
    change_idx: int | None,
    pre_mean: float | None,
    post_mean: float | None,
    is_significant: bool = True,
) -> tuple[PersistenceClassification, float, int, RegimeType]:
    """Evaluate whether an observed deviation is a spike or persistent shift."""
    if change_idx is None or pre_mean is None or post_mean is None:
        return "INSUFFICIENT_EVIDENCE", 0.0, 0, "insufficient_data"

    post_values = values[change_idx:]
    n_post = len(post_values)

    if n_post == 0:
        return "INSUFFICIENT_EVIDENCE", 0.0, 0, "insufficient_data"

    diff = post_mean - pre_mean
    if abs(diff) < 1e-9 or not is_significant:
        return "INSUFFICIENT_EVIDENCE", 0.0, 0, "normal"

    direction = 1 if diff > 0 else -1
    threshold = pre_mean + 0.5 * diff

    sustained_count = 0
    consecutive_sustained = 0
    max_consecutive = 0

    for v in post_values:
        if (direction == 1 and v >= threshold) or (direction == -1 and v <= threshold):
            sustained_count += 1
            consecutive_sustained += 1
            if consecutive_sustained > max_consecutive:
                max_consecutive = consecutive_sustained
        else:
            consecutive_sustained = 0

    persistence_score = round(sustained_count / n_post, 4)
    persistence_days = max_consecutive

    # 1. Single-day or 2-day spike reverting back
    if n_post >= 2 and max_consecutive <= 2 and persistence_score < 0.5:
        return "SPIKE", persistence_score, persistence_days, "isolated_anomaly"

    # 2. Short series: 1 single post-observation
    if n_post == 1:
        return "SPIKE", 1.0, 1, "isolated_anomaly"

    # 3. Temporary Shift (3 to 6 days or medium score)
    if (3 <= max_consecutive <= 6 and n_post >= 7 and persistence_score < 0.7) or (
        max_consecutive <= 3 and persistence_score < 0.6
    ):
        return (
            "TEMPORARY_SHIFT",
            persistence_score,
            persistence_days,
            "isolated_anomaly",
        )

    # 4. Persistent Regime Shift (7+ consecutive days or high sustained ratio)
    if (max_consecutive >= 7) or (persistence_score >= 0.70 and n_post >= 3):
        return (
            "PERSISTENT_SHIFT",
            persistence_score,
            persistence_days,
            "sustained_level_shift",
        )

    if persistence_score >= 0.5:
        return (
            "TEMPORARY_SHIFT",
            persistence_score,
            persistence_days,
            "sustained_level_shift",
        )

    return "SPIKE", persistence_score, persistence_days, "isolated_anomaly"
