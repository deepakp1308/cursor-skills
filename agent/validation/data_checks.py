"""Pre-analysis data quality checks on raw BigQuery results."""

from datetime import datetime, timezone
from agent.config import VALIDATION_THRESHOLDS as T


class DataQualityResult:
    def __init__(self):
        self.checks: list[dict] = []
        self.passed = True

    def add(self, name: str, status: str, detail: str = ""):
        self.checks.append({"name": name, "status": status, "detail": detail})
        if status == "fail":
            self.passed = False

    @property
    def summary(self) -> str:
        fails = [c for c in self.checks if c["status"] == "fail"]
        warns = [c for c in self.checks if c["status"] == "warn"]
        if not fails and not warns:
            return "All checks passed"
        parts = []
        if fails:
            parts.append(f"{len(fails)} failed")
        if warns:
            parts.append(f"{len(warns)} warnings")
        return ", ".join(parts)


def check_row_count(rows: list[dict], label: str, minimum: int = T["min_connector_users"]) -> tuple[str, str]:
    count = len(rows) if isinstance(rows, list) else rows
    if count >= minimum:
        return "pass", f"{label}: {count} rows (min {minimum})"
    return "warn", f"{label}: {count} rows below minimum {minimum}"


def check_null_rate(rows: list[dict], field: str, max_rate: float = T["max_null_rate"]) -> tuple[str, str]:
    if not rows:
        return "warn", f"No rows to check nulls on {field}"
    nulls = sum(1 for r in rows if r.get(field) is None)
    null_rate = nulls / len(rows)
    if null_rate <= max_rate:
        return "pass", f"{field} null rate: {null_rate:.1%} (max {max_rate:.0%})"
    return "warn", f"{field} null rate: {null_rate:.1%} exceeds {max_rate:.0%}"


def check_freshness(rows: list[dict], date_field: str, max_hours: int = T["max_freshness_hours"]) -> tuple[str, str]:
    if not rows:
        return "warn", f"No rows to check freshness on {date_field}"
    dates = [r[date_field] for r in rows if r.get(date_field)]
    if not dates:
        return "warn", f"No non-null {date_field} values"
    most_recent = max(dates)
    if hasattr(most_recent, "timestamp"):
        age_hours = (datetime.now(timezone.utc) - most_recent).total_seconds() / 3600
    else:
        return "pass", f"Date field {date_field}: type check skipped"
    if age_hours <= max_hours:
        return "pass", f"{date_field}: {age_hours:.0f}h old (max {max_hours}h)"
    return "warn", f"{date_field}: {age_hours:.0f}h old exceeds {max_hours}h"


def run_all_checks(query_results: dict) -> DataQualityResult:
    dq = DataQualityResult()

    if "channel_summary" in query_results:
        status, detail = check_row_count(query_results["channel_summary"], "channel_summary", minimum=2)
        dq.add("channel_summary_rows", status, detail)

    if "daily_connections" in query_results:
        status, detail = check_null_rate(query_results["daily_connections"], "channel")
        dq.add("daily_connections_nulls", status, detail)

    return dq
