"""Unit tests for Slack message formatting."""

from agent.output.slack_formatter import format_slack_message


def test_format_produces_valid_message():
    msg = format_slack_message(
        headline="Test headline",
        channel_health={
            "chatgpt": {"connections": 2899, "daily_adds": "~15", "wau_pct": "63"},
            "claude": {"connections": 2693, "daily_adds": "~269", "wau_pct": "82"},
        },
        analyzer_impact={
            "segment_lift": 2.6, "email_lift": 2.0,
            "upgrade_mult": 3.7, "f2p_with": 99.4, "f2p_without": 6.2,
        },
        key_segment_insight="E-commerce users over-index",
        funnel_alert="connection_to_wau",
        retention_signal="12 cohorts tracked",
        dq_summary="All checks passed",
    )
    assert "MC Everywhere Analyzer" in msg
    assert "Test headline" in msg
    assert "2899" in msg
    assert "2693" in msg
    assert "2.6x" in msg
    assert "All checks passed" in msg


def test_format_handles_missing_data():
    msg = format_slack_message(
        headline="Fallback", channel_health={}, analyzer_impact={},
        key_segment_insight="N/A", funnel_alert="N/A",
        retention_signal="N/A", dq_summary="1 warning",
    )
    assert "Fallback" in msg
