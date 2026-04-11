"""Post-analysis sanity checks on computed metrics."""

from agent.config import VALIDATION_THRESHOLDS as T


def check_rate_bounds(value: float, name: str) -> tuple[str, str]:
    if T["rate_min"] <= value <= T["rate_max"]:
        return "pass", f"{name}: {value}% within [0, 100]"
    return "fail", f"{name}: {value}% outside valid range [0, 100]"


def check_positive_lift(value: float, name: str) -> tuple[str, str]:
    if value > 0:
        return "pass", f"{name}: {value}x is positive"
    return "warn", f"{name}: {value}x is non-positive"


def check_user_count_consistency(count_a: int, count_b: int, label: str) -> tuple[str, str]:
    if count_a == count_b:
        return "pass", f"{label}: counts match ({count_a})"
    return "warn", f"{label}: counts differ ({count_a} vs {count_b})"


def check_week_over_week(current: float, previous: float, name: str, max_change: float = T["max_wow_change"]) -> tuple[str, str]:
    if previous == 0:
        return "pass", f"{name}: no previous data to compare"
    change = abs(current - previous) / previous
    if change <= max_change:
        return "pass", f"{name}: WoW change {change:.0%} within {max_change:.0%}"
    return "warn", f"{name}: WoW change {change:.0%} exceeds {max_change:.0%} threshold"
