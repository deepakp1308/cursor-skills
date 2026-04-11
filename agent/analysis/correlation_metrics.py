"""Lift calculations for feature-to-conversion and multi-product stacking."""

from agent.analysis.metrics import lift


def feature_conversion_lifts(rows: list[dict]) -> list[dict]:
    results = []
    for row in rows:
        with_rate = row.get("conversion_rate_with", 0) or 0
        without_rate = row.get("conversion_rate_without", 0) or 0
        results.append({
            "feature": row["feature"],
            "conversion_with": with_rate,
            "conversion_without": without_rate,
            "lift": lift(with_rate, without_rate) if without_rate else float("inf"),
        })
    return sorted(results, key=lambda x: x["lift"], reverse=True)


def stacking_effect(rows: list[dict]) -> list[dict]:
    results = []
    base_wau = None
    for row in sorted(rows, key=lambda x: x["product_count"]):
        wau = row.get("wau_pct", 0)
        if base_wau is None:
            base_wau = wau
        results.append({
            "product_count": row["product_count"],
            "users": row["users"],
            "wau_pct": wau,
            "incremental_wau": round(wau - base_wau, 1),
        })
    return results
