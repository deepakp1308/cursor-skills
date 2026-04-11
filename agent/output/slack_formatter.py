"""Format the weekly Slack message from analysis results."""

from datetime import date
from agent.config import REPORT_URL


def format_slack_message(
    headline: str,
    channel_health: dict,
    analyzer_impact: dict,
    key_segment_insight: str,
    funnel_alert: str,
    retention_signal: str,
    dq_summary: str,
) -> str:
    today = date.today().strftime("%b %d, %Y")

    chatgpt = channel_health.get("chatgpt", {})
    claude = channel_health.get("claude", {})

    return f"""*MC Everywhere Analyzer — Weekly Report — {today}*

{headline}

*Channel Health:*
>  ChatGPT: {chatgpt.get('connections', '?')} connections ({chatgpt.get('daily_adds', '?')}/day) | {chatgpt.get('wau_pct', '?')}% WAU
>  Claude:  {claude.get('connections', '?')} connections ({claude.get('daily_adds', '?')}/day) | {claude.get('wau_pct', '?')}% WAU

*Marketing Analyzer Impact:*
>  Segment lift: {analyzer_impact.get('segment_lift', '?')}x | Email lift: {analyzer_impact.get('email_lift', '?')}x
>  Upgrade multiplier: {analyzer_impact.get('upgrade_mult', '?')}x | Free→Paid: {analyzer_impact.get('f2p_with', '?')}% vs {analyzer_impact.get('f2p_without', '?')}%

*Key Segment Insight:* {key_segment_insight}
*Funnel Alert:* {funnel_alert}
*Retention Signal:* {retention_signal}

*Data Quality:* {dq_summary}

<{REPORT_URL}|View Full Report>"""
