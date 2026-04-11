"""Cohort retention curve calculations and churn window analysis."""

from agent.analysis.metrics import rate


def retention_rates(cohort_rows: list[dict]) -> list[dict]:
    results = []
    for row in cohort_rows:
        size = row["cohort_size"]
        if not size:
            continue
        results.append({
            "channel": row["channel"],
            "cohort_week": str(row["cohort_week"]),
            "cohort_size": size,
            "week_0_pct": rate(row.get("week_0", 0), size),
            "week_1_pct": rate(row.get("week_1", 0), size),
            "week_2_pct": rate(row.get("week_2", 0), size),
            "week_4_pct": rate(row.get("week_4", 0), size),
            "week_8_pct": rate(row.get("week_8", 0), size),
            "week_12_pct": rate(row.get("week_12", 0), size),
        })
    return results


def churn_windows(churn_rows: list[dict]) -> list[dict]:
    results = []
    for row in churn_rows:
        total = row["total_churned"]
        if not total:
            continue
        results.append({
            "channel": row["channel"],
            "total_churned": total,
            "week1_pct": rate(row.get("churned_week1", 0), total),
            "month1_pct": rate(row.get("churned_month1", 0), total),
            "month2_pct": rate(row.get("churned_month2", 0), total),
            "after_60d_pct": rate(row.get("churned_after_60d", 0), total),
            "avg_days": row.get("avg_days_to_churn", 0),
        })
    return results
