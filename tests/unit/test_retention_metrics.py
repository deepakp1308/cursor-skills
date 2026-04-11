"""Unit tests for retention curve calculations."""

from agent.analysis.retention_metrics import retention_rates, churn_windows


def test_retention_rates():
    rows = [{"channel": "chatgpt", "cohort_week": "2025-12-14", "cohort_size": 257,
             "week_0": 200, "week_1": 150, "week_2": 120, "week_4": 90, "week_8": 60, "week_12": 40}]
    result = retention_rates(rows)
    assert len(result) == 1
    assert result[0]["week_0_pct"] == 77.8
    assert result[0]["week_12_pct"] == 15.6


def test_churn_windows():
    rows = [{"channel": "chatgpt", "total_churned": 28, "churned_week1": 5,
             "churned_month1": 10, "churned_month2": 8, "churned_after_60d": 5, "avg_days_to_churn": 35}]
    result = churn_windows(rows)
    assert len(result) == 1
    assert result[0]["week1_pct"] == 17.9
    assert result[0]["avg_days"] == 35


def test_empty_cohort_skipped():
    rows = [{"channel": "x", "cohort_week": "2026-01-01", "cohort_size": 0,
             "week_0": 0, "week_1": 0, "week_2": 0, "week_4": 0, "week_8": 0, "week_12": 0}]
    result = retention_rates(rows)
    assert len(result) == 0
