"""Module 4: Funnel analytics — connection-to-action funnel, time-to-value, drop-off."""

from agent.config import TABLES, ANALYSIS_START_DATE


def connection_to_action_funnel_sql() -> str:
    return f"""
    WITH connector_users AS (
        SELECT DISTINCT i.user_id,
            CASE WHEN LOWER(i.name) = 'chatgpt' THEN 'chatgpt' ELSE 'claude' END AS channel,
            DATE(i.created_at) AS connected_date
        FROM `{TABLES['integrations']}` i
        WHERE i.type = 'oauth2' AND LOWER(i.name) IN ('chatgpt', 'claude')
    ),
    first_wau AS (
        SELECT w.user_id, MIN(w.week) AS first_active_week
        FROM `{TABLES['users_weekly_rollup']}` w
        WHERE w.wau = TRUE AND w.week >= '{ANALYSIS_START_DATE}'
        GROUP BY w.user_id
    ),
    first_segment AS (
        SELECT user_id, MIN(action_date) AS first_segment_date
        FROM `{TABLES['tags_segments']}`
        WHERE action_type LIKE '%segment%' AND action_date >= '{ANALYSIS_START_DATE}'
        GROUP BY user_id
    ),
    first_email AS (
        SELECT user_id, MIN(send_date) AS first_email_date
        FROM `{TABLES['email_sends']}`
        WHERE send_date >= '{ANALYSIS_START_DATE}' AND sends.delivered > 0
        GROUP BY user_id
    ),
    first_automation AS (
        SELECT DISTINCT user_id FROM `{TABLES['customer_journey']}`
    )
    SELECT c.channel,
        COUNT(DISTINCT c.user_id) AS connected,
        COUNT(DISTINCT CASE WHEN fw.user_id IS NOT NULL THEN c.user_id END) AS became_wau,
        ROUND(SAFE_DIVIDE(COUNT(DISTINCT CASE WHEN fw.user_id IS NOT NULL THEN c.user_id END), COUNT(DISTINCT c.user_id)) * 100, 1) AS wau_rate,
        COUNT(DISTINCT CASE WHEN fe.user_id IS NOT NULL AND fe.first_email_date <= DATE_ADD(c.connected_date, INTERVAL 30 DAY) THEN c.user_id END) AS sent_email_30d,
        ROUND(SAFE_DIVIDE(COUNT(DISTINCT CASE WHEN fe.user_id IS NOT NULL AND fe.first_email_date <= DATE_ADD(c.connected_date, INTERVAL 30 DAY) THEN c.user_id END), COUNT(DISTINCT c.user_id)) * 100, 1) AS email_30d_rate,
        COUNT(DISTINCT CASE WHEN fs.user_id IS NOT NULL AND fs.first_segment_date <= DATE_ADD(c.connected_date, INTERVAL 30 DAY) THEN c.user_id END) AS created_segment_30d,
        ROUND(SAFE_DIVIDE(COUNT(DISTINCT CASE WHEN fs.user_id IS NOT NULL AND fs.first_segment_date <= DATE_ADD(c.connected_date, INTERVAL 30 DAY) THEN c.user_id END), COUNT(DISTINCT c.user_id)) * 100, 1) AS segment_30d_rate,
        COUNT(DISTINCT CASE WHEN fa.user_id IS NOT NULL THEN c.user_id END) AS has_automation,
        ROUND(SAFE_DIVIDE(COUNT(DISTINCT CASE WHEN fa.user_id IS NOT NULL THEN c.user_id END), COUNT(DISTINCT c.user_id)) * 100, 1) AS automation_rate
    FROM connector_users c
    LEFT JOIN first_wau fw ON c.user_id = fw.user_id
    LEFT JOIN first_email fe ON c.user_id = fe.user_id
    LEFT JOIN first_segment fs ON c.user_id = fs.user_id
    LEFT JOIN first_automation fa ON c.user_id = fa.user_id
    GROUP BY c.channel
    """


def time_to_value_sql() -> str:
    return f"""
    WITH connector_users AS (
        SELECT DISTINCT i.user_id,
            CASE WHEN LOWER(i.name) = 'chatgpt' THEN 'chatgpt' ELSE 'claude' END AS channel,
            DATE(i.created_at) AS connected_date
        FROM `{TABLES['integrations']}` i
        WHERE i.type = 'oauth2' AND LOWER(i.name) IN ('chatgpt', 'claude')
    ),
    first_email AS (
        SELECT user_id, MIN(send_date) AS first_email_date
        FROM `{TABLES['email_sends']}`
        WHERE send_date >= '{ANALYSIS_START_DATE}' AND sends.delivered > 0
        GROUP BY user_id
    ),
    first_segment AS (
        SELECT user_id, MIN(action_date) AS first_segment_date
        FROM `{TABLES['tags_segments']}`
        WHERE action_type LIKE '%segment%' AND action_date >= '{ANALYSIS_START_DATE}'
        GROUP BY user_id
    )
    SELECT c.channel,
        APPROX_QUANTILES(DATE_DIFF(fe.first_email_date, c.connected_date, DAY), 2)[OFFSET(1)] AS median_days_to_first_email,
        APPROX_QUANTILES(DATE_DIFF(fs.first_segment_date, c.connected_date, DAY), 2)[OFFSET(1)] AS median_days_to_first_segment
    FROM connector_users c
    LEFT JOIN first_email fe ON c.user_id = fe.user_id AND fe.first_email_date >= c.connected_date
    LEFT JOIN first_segment fs ON c.user_id = fs.user_id AND fs.first_segment_date >= c.connected_date
    WHERE fe.user_id IS NOT NULL OR fs.user_id IS NOT NULL
    GROUP BY c.channel
    """
