"""Module 2: Every metric sliced by plan tier for ChatGPT and Claude."""

from agent.config import TABLES, ANALYSIS_START_DATE


def metrics_by_plan_tier_sql() -> str:
    return f"""
    WITH ai_users AS (
        SELECT DISTINCT i.user_id,
            CASE WHEN LOWER(i.name) = 'chatgpt' THEN 'chatgpt' ELSE 'claude' END AS channel,
            COALESCE(e.monthly_plan, 'free') AS plan
        FROM `{TABLES['integrations']}` i
        LEFT JOIN `{TABLES['genai_eligibility']}` e
            ON i.user_id = e.user_id AND e.month = DATE_TRUNC(CURRENT_DATE(), MONTH)
        WHERE i.type = 'oauth2' AND LOWER(i.name) IN ('chatgpt', 'claude')
    ),
    wau AS (
        SELECT DISTINCT user_id FROM `{TABLES['users_weekly_rollup']}`
        WHERE week = DATE_TRUNC(CURRENT_DATE(), WEEK(SUNDAY)) AND wau = TRUE
    ),
    segments AS (
        SELECT DISTINCT user_id FROM `{TABLES['tags_segments']}`
        WHERE action_date >= '{ANALYSIS_START_DATE}' AND action_type LIKE '%segment%'
    ),
    automations AS (SELECT DISTINCT user_id FROM `{TABLES['customer_journey']}`),
    sms AS (
        SELECT DISTINCT user_id FROM `{TABLES['sms']}`
        WHERE metrics.message.outbound.delivered_message_count > 0
    ),
    emails AS (
        SELECT DISTINCT user_id FROM `{TABLES['email_sends']}`
        WHERE send_date >= '{ANALYSIS_START_DATE}' AND sends.delivered > 0
    )
    SELECT a.channel, a.plan,
        COUNT(DISTINCT a.user_id) AS users,
        ROUND(SAFE_DIVIDE(COUNT(DISTINCT CASE WHEN w.user_id IS NOT NULL THEN a.user_id END), COUNT(DISTINCT a.user_id)) * 100, 1) AS wau_pct,
        ROUND(SAFE_DIVIDE(COUNT(DISTINCT CASE WHEN seg.user_id IS NOT NULL THEN a.user_id END), COUNT(DISTINCT a.user_id)) * 100, 1) AS segment_pct,
        ROUND(SAFE_DIVIDE(COUNT(DISTINCT CASE WHEN aut.user_id IS NOT NULL THEN a.user_id END), COUNT(DISTINCT a.user_id)) * 100, 1) AS automation_pct,
        ROUND(SAFE_DIVIDE(COUNT(DISTINCT CASE WHEN s.user_id IS NOT NULL THEN a.user_id END), COUNT(DISTINCT a.user_id)) * 100, 1) AS sms_pct,
        ROUND(SAFE_DIVIDE(COUNT(DISTINCT CASE WHEN em.user_id IS NOT NULL THEN a.user_id END), COUNT(DISTINCT a.user_id)) * 100, 1) AS email_pct
    FROM ai_users a
    LEFT JOIN wau w ON a.user_id = w.user_id
    LEFT JOIN segments seg ON a.user_id = seg.user_id
    LEFT JOIN automations aut ON a.user_id = aut.user_id
    LEFT JOIN sms s ON a.user_id = s.user_id
    LEFT JOIN emails em ON a.user_id = em.user_id
    GROUP BY a.channel, a.plan
    ORDER BY a.channel, users DESC
    """
