"""Threshold-based recommendation engine."""


def generate_recommendations(data: dict) -> list[dict]:
    recs = []

    analyzer_lift = data.get("analyzer_segment_lift", 0)
    if analyzer_lift >= 2.0:
        recs.append({
            "category": "marketing_analyzer",
            "priority": "high",
            "finding": f"Marketing Analyzer lifts segment creation by {analyzer_lift}x",
            "recommendation": "Embed Marketing Analyzer in ChatGPT/Claude connector experience",
        })

    chatgpt_daily = data.get("chatgpt_daily_adds", 0)
    if chatgpt_daily < 30:
        recs.append({
            "category": "growth",
            "priority": "high",
            "finding": f"ChatGPT daily adds declined to {chatgpt_daily}/day",
            "recommendation": "Investigate ChatGPT connector discovery and activation flow",
        })

    paid_conversion = data.get("connector_paid_conversion", 0)
    if paid_conversion < 5:
        recs.append({
            "category": "conversion",
            "priority": "critical",
            "finding": f"Free-to-paid conversion for connector signups is {paid_conversion}%",
            "recommendation": "Create upgrade trigger for free connector users via Marketing Analyzer trial",
        })

    upgrade_mult = data.get("upgrade_multiplier", 0)
    if upgrade_mult >= 2.0:
        recs.append({
            "category": "upsell",
            "priority": "medium",
            "finding": f"Active segmenters upgrade Standard→Premium at {upgrade_mult}x",
            "recommendation": "Surface segmentation prompts to Standard connector users to drive Premium upgrades",
        })

    disconnect_reduction = data.get("disconnect_rate_reduction", 0)
    if disconnect_reduction >= 20:
        recs.append({
            "category": "retention",
            "priority": "medium",
            "finding": f"Segment creators disconnect {disconnect_reduction}% less",
            "recommendation": "Drive segment creation behavior to compound retention advantage",
        })

    return sorted(recs, key=lambda r: {"critical": 0, "high": 1, "medium": 2}.get(r["priority"], 3))
