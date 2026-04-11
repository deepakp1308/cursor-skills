"""Unit tests for correlation lift calculations."""

from agent.analysis.correlation_metrics import feature_conversion_lifts, stacking_effect


def test_feature_lifts_sorted_by_lift():
    rows = [
        {"feature": "sms", "conversion_rate_with": 20.0, "conversion_rate_without": 5.0},
        {"feature": "email", "conversion_rate_with": 15.0, "conversion_rate_without": 10.0},
    ]
    result = feature_conversion_lifts(rows)
    assert result[0]["feature"] == "sms"
    assert result[0]["lift"] == 4.0
    assert result[1]["lift"] == 1.5


def test_stacking_incremental():
    rows = [
        {"product_count": 0, "users": 1000, "wau_pct": 20.0},
        {"product_count": 1, "users": 800, "wau_pct": 40.0},
        {"product_count": 2, "users": 500, "wau_pct": 65.0},
    ]
    result = stacking_effect(rows)
    assert result[0]["incremental_wau"] == 0.0
    assert result[1]["incremental_wau"] == 20.0
    assert result[2]["incremental_wau"] == 45.0
