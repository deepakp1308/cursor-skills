"""Funnel conversion rates, drop-off analysis, time-to-value computations."""

from agent.analysis.metrics import rate


def funnel_conversion_rates(funnel_data: list[dict]) -> list[dict]:
    results = []
    for row in funnel_data:
        channel = row["channel"]
        connected = row["connected"]
        results.append({
            "channel": channel,
            "connected": connected,
            "became_wau_rate": row.get("wau_rate", 0),
            "email_30d_rate": row.get("email_30d_rate", 0),
            "segment_30d_rate": row.get("segment_30d_rate", 0),
            "automation_rate": row.get("automation_rate", 0),
            "biggest_dropoff": _find_biggest_dropoff(row),
        })
    return results


def _find_biggest_dropoff(row: dict) -> str:
    stages = [
        ("connection_to_wau", 100, row.get("wau_rate", 0)),
        ("wau_to_email", row.get("wau_rate", 0), row.get("email_30d_rate", 0)),
        ("email_to_segment", row.get("email_30d_rate", 0), row.get("segment_30d_rate", 0)),
    ]
    max_drop = 0
    max_stage = "none"
    for name, from_rate, to_rate in stages:
        drop = from_rate - to_rate
        if drop > max_drop:
            max_drop = drop
            max_stage = name
    return max_stage
