"""Functional test: verify the analysis pipeline with mock data."""

from agent.analysis.metrics import lift, disconnect_rate_reduction, upgrade_multiplier
from agent.analysis.recommendations import generate_recommendations


def test_recommendations_from_known_data():
    data = {
        "analyzer_segment_lift": 2.6,
        "analyzer_email_lift": 2.0,
        "disconnect_rate_reduction": 40.0,
        "upgrade_multiplier": 3.7,
        "chatgpt_daily_adds": 15,
        "connector_paid_conversion": 6.2,
    }
    recs = generate_recommendations(data)
    assert len(recs) >= 3
    categories = {r["category"] for r in recs}
    assert "marketing_analyzer" in categories
    assert "growth" in categories


def test_lift_calculations_consistent():
    seg_lift = lift(68.3, 26.7)
    email_lift = lift(88.7, 44.8)
    assert seg_lift == 2.6
    assert email_lift == 2.0


def test_disconnect_reduction():
    result = disconnect_rate_reduction(1.5, 0.9)
    assert result == 40.0


def test_upgrade_multiplier():
    result = upgrade_multiplier(0.223, 0.061)
    assert result == 3.7
