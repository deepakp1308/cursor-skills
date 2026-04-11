"""Module 1a: Core channel performance queries — scale, composition, engagement, attachment, acquisition."""

from agent.config import TABLES, ANALYSIS_START_DATE


def daily_connections_sql() -> str:
    return f"""
    SELECT
        name AS channel,
        DATE(created_at) AS day,
        COUNT(*) AS connections,
        COUNT(CASE WHEN user_created_at IS NOT NULL THEN 1 END) AS new_signups
    FROM `{TABLES['integrations']}`
    WHERE type = 'oauth2' AND LOWER(name) IN ('chatgpt', 'claude')
    GROUP BY channel, day
    ORDER BY channel, day
    """


def channel_summary_sql() -> str:
    return f"""
    SELECT
        name,
        type,
        COUNT(DISTINCT user_id) AS unique_users,
        COUNT(*) AS total_connections,
        COUNT(CASE WHEN user_created_at IS NOT NULL THEN 1 END) AS new_mc_signups,
        ROUND(SAFE_DIVIDE(
            COUNT(CASE WHEN user_created_at IS NOT NULL THEN 1 END),
            COUNT(*)
        ) * 100, 2) AS signup_rate_pct,
        COUNT(CASE WHEN is_deleted = FALSE THEN 1 END) AS active,
        COUNT(CASE WHEN is_deleted = TRUE THEN 1 END) AS churned,
        MIN(created_at) AS first_connection,
        MAX(created_at) AS last_connection,
        DATE_DIFF(CURRENT_DATE(), DATE(MIN(created_at)), DAY) AS days_since_launch
    FROM `{TABLES['integrations']}`
    WHERE type = 'oauth2' AND LOWER(name) IN ('chatgpt', 'claude')
    GROUP BY name, type
    ORDER BY name
    """


def plan_distribution_sql() -> str:
    return f"""
    WITH channel_users AS (
        SELECT DISTINCT i.user_id,
            CASE WHEN LOWER(i.name) = 'chatgpt' THEN 'chatgpt'
                 WHEN LOWER(i.name) = 'claude' THEN 'claude' END AS channel
        FROM `{TABLES['integrations']}` i
        WHERE i.type = 'oauth2' AND LOWER(i.name) IN ('chatgpt', 'claude')
    )
    SELECT cu.channel, u.primary_plan_type,
        COUNT(DISTINCT cu.user_id) AS users,
        ROUND(SAFE_DIVIDE(
            COUNT(DISTINCT cu.user_id),
            SUM(COUNT(DISTINCT cu.user_id)) OVER (PARTITION BY cu.channel)
        ) * 100, 1) AS pct
    FROM channel_users cu
    JOIN `{TABLES['users']}` u ON cu.user_id = u.user_id
    GROUP BY cu.channel, u.primary_plan_type
    ORDER BY cu.channel, users DESC
    """


def engagement_by_tier_sql() -> str:
    return f"""
    WITH ai_users AS (
        SELECT DISTINCT i.user_id,
            CASE WHEN LOWER(i.name) = 'chatgpt' THEN 'chatgpt'
                 WHEN LOWER(i.name) = 'claude' THEN 'claude' END AS channel
        FROM `{TABLES['integrations']}` i
        WHERE i.type = 'oauth2' AND LOWER(i.name) IN ('chatgpt', 'claude')
    )
    SELECT a.channel, e.monthly_plan,
        COUNT(DISTINCT a.user_id) AS total_users,
        COUNT(DISTINCT CASE WHEN w.wau = TRUE THEN a.user_id END) AS wau_users,
        ROUND(SAFE_DIVIDE(
            COUNT(DISTINCT CASE WHEN w.wau = TRUE THEN a.user_id END),
            COUNT(DISTINCT a.user_id)
        ) * 100, 1) AS wau_pct
    FROM ai_users a
    LEFT JOIN `{TABLES['genai_eligibility']}` e
        ON a.user_id = e.user_id AND e.month = DATE_TRUNC(CURRENT_DATE(), MONTH)
    LEFT JOIN `{TABLES['users_weekly_rollup']}` w
        ON a.user_id = w.user_id AND w.week = DATE_TRUNC(CURRENT_DATE(), WEEK(SUNDAY))
    GROUP BY a.channel, e.monthly_plan
    ORDER BY a.channel, total_users DESC
    """


def genai_engagement_sql() -> str:
    return f"""
    SELECT channel, total_users, genai_eligible, genai_eligible_and_active,
        ROUND(SAFE_DIVIDE(genai_eligible_and_active, genai_eligible) * 100, 1) AS genai_engagement_rate
    FROM (
        SELECT a.channel,
            COUNT(DISTINCT a.user_id) AS total_users,
            COUNT(DISTINCT CASE WHEN e.email_inline = TRUE THEN a.user_id END) AS genai_eligible,
            COUNT(DISTINCT CASE WHEN e.email_inline = TRUE AND w.wau = TRUE THEN a.user_id END) AS genai_eligible_and_active
        FROM (
            SELECT DISTINCT i.user_id,
                CASE WHEN LOWER(i.name) = 'chatgpt' THEN 'chatgpt'
                     WHEN LOWER(i.name) = 'claude' THEN 'claude' END AS channel
            FROM `{TABLES['integrations']}` i
            WHERE i.type = 'oauth2' AND LOWER(i.name) IN ('chatgpt', 'claude')
        ) a
        LEFT JOIN `{TABLES['genai_eligibility']}` e
            ON a.user_id = e.user_id AND e.month = DATE_TRUNC(CURRENT_DATE(), MONTH)
        LEFT JOIN `{TABLES['users_weekly_rollup']}` w
            ON a.user_id = w.user_id AND w.week = DATE_TRUNC(CURRENT_DATE(), WEEK(SUNDAY))
        GROUP BY a.channel
    )
    """


def product_attachment_sql() -> str:
    return f"""
    WITH ai_users AS (
        SELECT DISTINCT i.user_id,
            CASE WHEN LOWER(i.name) = 'chatgpt' THEN 'chatgpt'
                 WHEN LOWER(i.name) = 'claude' THEN 'claude' END AS channel
        FROM `{TABLES['integrations']}` i
        WHERE i.type = 'oauth2' AND LOWER(i.name) IN ('chatgpt', 'claude')
    ),
    bulk_email AS (SELECT DISTINCT user_id FROM `{TABLES['integrations']}` WHERE FALSE),
    automations AS (SELECT DISTINCT user_id FROM `{TABLES['customer_journey']}`),
    sms AS (
        SELECT DISTINCT user_id FROM `{TABLES['sms']}`
        WHERE metrics.message.outbound.delivered_message_count > 0
    ),
    tx AS (SELECT DISTINCT user_id FROM `{TABLES['transactional']}` WHERE sent > 0),
    wa AS (
        SELECT DISTINCT user_id FROM `{TABLES['messaging_outreach']}`
        WHERE is_whatsapp_outreach = TRUE AND delivery_metrics.total_messages_delivered > 0
    )
    SELECT a.channel,
        COUNT(DISTINCT a.user_id) AS total,
        ROUND(SAFE_DIVIDE(COUNT(DISTINCT CASE WHEN aut.user_id IS NOT NULL THEN a.user_id END), COUNT(DISTINCT a.user_id)) * 100, 1) AS automation_pct,
        ROUND(SAFE_DIVIDE(COUNT(DISTINCT CASE WHEN s.user_id IS NOT NULL THEN a.user_id END), COUNT(DISTINCT a.user_id)) * 100, 1) AS sms_pct,
        ROUND(SAFE_DIVIDE(COUNT(DISTINCT CASE WHEN t.user_id IS NOT NULL THEN a.user_id END), COUNT(DISTINCT a.user_id)) * 100, 1) AS tx_email_pct,
        ROUND(SAFE_DIVIDE(COUNT(DISTINCT CASE WHEN w.user_id IS NOT NULL THEN a.user_id END), COUNT(DISTINCT a.user_id)) * 100, 1) AS whatsapp_pct
    FROM ai_users a
    LEFT JOIN automations aut ON a.user_id = aut.user_id
    LEFT JOIN sms s ON a.user_id = s.user_id
    LEFT JOIN tx t ON a.user_id = t.user_id
    LEFT JOIN wa w ON a.user_id = w.user_id
    GROUP BY a.channel
    """


def acquisition_conversion_sql() -> str:
    return f"""
    WITH channel_signups AS (
        SELECT i.name AS channel, i.user_id, i.user_created_at
        FROM `{TABLES['integrations']}` i
        WHERE i.type = 'oauth2' AND i.user_created_at IS NOT NULL
            AND i.user_created_at >= '{ANALYSIS_START_DATE}'
            AND LOWER(i.name) IN (
                'chatgpt', 'claude', 'mailchimp for shopify',
                'mailchimp for woocommerce', 'squarespace commerce',
                'square', 'beatstars'
            )
    )
    SELECT s.channel,
        COUNT(DISTINCT s.user_id) AS total_signups,
        COUNT(DISTINCT CASE WHEN o.new_conversion = TRUE THEN s.user_id END) AS paid_conversions,
        ROUND(SAFE_DIVIDE(
            COUNT(DISTINCT CASE WHEN o.new_conversion = TRUE THEN s.user_id END),
            COUNT(DISTINCT s.user_id)
        ) * 100, 2) AS conversion_rate,
        ROUND(AVG(CASE WHEN o.new_conversion = TRUE THEN o.days_from_signup_to_order END), 1) AS avg_days_to_convert
    FROM channel_signups s
    LEFT JOIN `{TABLES['orders']}` o ON s.user_id = o.user_id
    GROUP BY s.channel
    ORDER BY conversion_rate DESC
    """
