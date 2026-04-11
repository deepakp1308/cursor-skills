"""Unit tests for funnel metric calculations."""

from agent.analysis.funnel_metrics import funnel_conversion_rates


def test_funnel_rates():
    data = [{
        "channel": "chatgpt",
        "connected": 2899,
        "wau_rate": 55.0,
        "email_30d_rate": 40.0,
        "segment_30d_rate": 30.0,
        "automation_rate": 25.0,
    }]
    result = funnel_conversion_rates(data)
    assert len(result) == 1
    assert result[0]["channel"] == "chatgpt"
    assert result[0]["became_wau_rate"] == 55.0
    assert result[0]["biggest_dropoff"] == "connection_to_wau"


def test_biggest_dropoff_email_to_segment():
    data = [{
        "channel": "claude",
        "connected": 100,
        "wau_rate": 90.0,
        "email_30d_rate": 85.0,
        "segment_30d_rate": 20.0,
        "automation_rate": 10.0,
    }]
    result = funnel_conversion_rates(data)
    assert result[0]["biggest_dropoff"] == "email_to_segment"
