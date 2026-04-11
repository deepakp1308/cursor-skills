"""Structure QBO vs MC and ChatGPT vs Claude comparisons."""

from agent.analysis.metrics import delta, lift


QBO_BENCHMARKS = {
    "chatgpt_connections": 4792,
    "claude_connections": 4830,
    "chatgpt_daily_adds": 60,
    "claude_daily_adds_low": 280,
    "claude_daily_adds_high": 440,
    "chatgpt_engagement": 53,
    "claude_engagement": 49,
    "premium_chatgpt_engagement": 73,
    "premium_claude_engagement": 68,
    "payments_chatgpt": 29,
    "payments_claude": 27,
    "payroll_chatgpt": 19,
    "payroll_claude": 17,
    "billpay_chatgpt": 18,
    "billpay_claude": 16,
}


def build_scorecard(mc_data: dict) -> list[dict]:
    rows = []
    for dimension, qbo_val, mc_val, mc_internal in _scorecard_rows(mc_data):
        rows.append({
            "dimension": dimension,
            "qbo_vs_mc": "MC leads" if mc_val > qbo_val else "QBO leads",
            "qbo_value": qbo_val,
            "mc_value": mc_val,
            "delta": delta(mc_val, qbo_val),
            "mc_internal": mc_internal,
        })
    return rows


def _scorecard_rows(d: dict):
    yield ("Scale", QBO_BENCHMARKS["chatgpt_connections"], d.get("chatgpt_connections", 0), f"ChatGPT {d.get('chatgpt_connections', 0)} vs Claude {d.get('claude_connections', 0)}")
    yield ("Engagement", QBO_BENCHMARKS["chatgpt_engagement"], d.get("chatgpt_engagement", 0), f"Claude {d.get('claude_engagement', 0)}% vs ChatGPT {d.get('chatgpt_engagement', 0)}%")
    yield ("Top attachment", QBO_BENCHMARKS["payments_chatgpt"], d.get("chatgpt_automation_pct", 0), f"Automations: Claude {d.get('claude_automation_pct', 0)}% vs ChatGPT {d.get('chatgpt_automation_pct', 0)}%")
