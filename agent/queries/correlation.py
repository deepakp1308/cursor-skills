"""Module 5: Correlation analysis — feature-to-conversion, feature-to-retention, stacking."""

from agent.config import TABLES, ANALYSIS_START_DATE


def feature_to_conversion_sql() -> str:
    """Among free connector users, which actions correlate with paid conversion?"""
    return f"""
    WITH free_connector AS (
        SELECT DISTINCT i.user_id
        FROM `{TABLES['integrations']}` i
        JOIN `{TABLES['users']}` u ON i.user_id = u.user_id
        WHERE i.type = 'oauth2' AND LOWER(i.name) IN ('chatgpt', 'claude')
            AND u.primary_plan_type = 'free'
    ),
    converted AS (
        SELECT DISTINCT user_id FROM `{TABLES['orders']}`
        WHERE new_conversion = TRUE AND ordered_at >= '{ANALYSIS_START_DATE}'
    ),
    has_segment AS (SELECT DISTINCT user_id FROM `{TABLES['tags_segments']}` WHERE action_type LIKE '%segment%' AND action_date >= '{ANALYSIS_START_DATE}'),
    has_email AS (SELECT DISTINCT user_id FROM `{TABLES['email_sends']}` WHERE send_date >= '{ANALYSIS_START_DATE}' AND sends.delivered > 0),
    has_automation AS (SELECT DISTINCT user_id FROM `{TABLES['customer_journey']}` WHERE user_id IS NOT NULL),
    has_sms AS (SELECT DISTINCT user_id FROM `{TABLES['sms']}` WHERE metrics.message.outbound.delivered_message_count > 0)
    SELECT
        'segment_creation' AS feature,
        COUNT(DISTINCT CASE WHEN hs.user_id IS NOT NULL THEN f.user_id END) AS users_with_feature,
        COUNT(DISTINCT CASE WHEN hs.user_id IS NOT NULL AND c.user_id IS NOT NULL THEN f.user_id END) AS converted_with_feature,
        ROUND(SAFE_DIVIDE(COUNT(DISTINCT CASE WHEN hs.user_id IS NOT NULL AND c.user_id IS NOT NULL THEN f.user_id END), NULLIF(COUNT(DISTINCT CASE WHEN hs.user_id IS NOT NULL THEN f.user_id END), 0)) * 100, 1) AS conversion_rate_with,
        ROUND(SAFE_DIVIDE(COUNT(DISTINCT CASE WHEN hs.user_id IS NULL AND c.user_id IS NOT NULL THEN f.user_id END), NULLIF(COUNT(DISTINCT CASE WHEN hs.user_id IS NULL THEN f.user_id END), 0)) * 100, 1) AS conversion_rate_without
    FROM free_connector f
    LEFT JOIN converted c ON f.user_id = c.user_id
    LEFT JOIN has_segment hs ON f.user_id = hs.user_id
    UNION ALL
    SELECT 'email_send' AS feature,
        COUNT(DISTINCT CASE WHEN he.user_id IS NOT NULL THEN f.user_id END),
        COUNT(DISTINCT CASE WHEN he.user_id IS NOT NULL AND c.user_id IS NOT NULL THEN f.user_id END),
        ROUND(SAFE_DIVIDE(COUNT(DISTINCT CASE WHEN he.user_id IS NOT NULL AND c.user_id IS NOT NULL THEN f.user_id END), NULLIF(COUNT(DISTINCT CASE WHEN he.user_id IS NOT NULL THEN f.user_id END), 0)) * 100, 1),
        ROUND(SAFE_DIVIDE(COUNT(DISTINCT CASE WHEN he.user_id IS NULL AND c.user_id IS NOT NULL THEN f.user_id END), NULLIF(COUNT(DISTINCT CASE WHEN he.user_id IS NULL THEN f.user_id END), 0)) * 100, 1)
    FROM free_connector f LEFT JOIN converted c ON f.user_id = c.user_id LEFT JOIN has_email he ON f.user_id = he.user_id
    UNION ALL
    SELECT 'automation' AS feature,
        COUNT(DISTINCT CASE WHEN ha.user_id IS NOT NULL THEN f.user_id END),
        COUNT(DISTINCT CASE WHEN ha.user_id IS NOT NULL AND c.user_id IS NOT NULL THEN f.user_id END),
        ROUND(SAFE_DIVIDE(COUNT(DISTINCT CASE WHEN ha.user_id IS NOT NULL AND c.user_id IS NOT NULL THEN f.user_id END), NULLIF(COUNT(DISTINCT CASE WHEN ha.user_id IS NOT NULL THEN f.user_id END), 0)) * 100, 1),
        ROUND(SAFE_DIVIDE(COUNT(DISTINCT CASE WHEN ha.user_id IS NULL AND c.user_id IS NOT NULL THEN f.user_id END), NULLIF(COUNT(DISTINCT CASE WHEN ha.user_id IS NULL THEN f.user_id END), 0)) * 100, 1)
    FROM free_connector f LEFT JOIN converted c ON f.user_id = c.user_id LEFT JOIN has_automation ha ON f.user_id = ha.user_id
    UNION ALL
    SELECT 'sms' AS feature,
        COUNT(DISTINCT CASE WHEN hs2.user_id IS NOT NULL THEN f.user_id END),
        COUNT(DISTINCT CASE WHEN hs2.user_id IS NOT NULL AND c.user_id IS NOT NULL THEN f.user_id END),
        ROUND(SAFE_DIVIDE(COUNT(DISTINCT CASE WHEN hs2.user_id IS NOT NULL AND c.user_id IS NOT NULL THEN f.user_id END), NULLIF(COUNT(DISTINCT CASE WHEN hs2.user_id IS NOT NULL THEN f.user_id END), 0)) * 100, 1),
        ROUND(SAFE_DIVIDE(COUNT(DISTINCT CASE WHEN hs2.user_id IS NULL AND c.user_id IS NOT NULL THEN f.user_id END), NULLIF(COUNT(DISTINCT CASE WHEN hs2.user_id IS NULL THEN f.user_id END), 0)) * 100, 1)
    FROM free_connector f LEFT JOIN converted c ON f.user_id = c.user_id LEFT JOIN has_sms hs2 ON f.user_id = hs2.user_id
    """


def multi_product_stacking_sql() -> str:
    """Does using 2+ products compound WAU engagement?"""
    return f"""
    WITH ai_users AS (
        SELECT DISTINCT i.user_id
        FROM `{TABLES['integrations']}` i
        WHERE i.type = 'oauth2' AND LOWER(i.name) IN ('chatgpt', 'claude')
    ),
    products AS (
        SELECT u.user_id,
            (CASE WHEN seg.user_id IS NOT NULL THEN 1 ELSE 0 END
             + CASE WHEN aut.user_id IS NOT NULL THEN 1 ELSE 0 END
             + CASE WHEN sms.user_id IS NOT NULL THEN 1 ELSE 0 END
             + CASE WHEN em.user_id IS NOT NULL THEN 1 ELSE 0 END) AS product_count
        FROM ai_users u
        LEFT JOIN (SELECT DISTINCT user_id FROM `{TABLES['tags_segments']}` WHERE action_type LIKE '%segment%' AND action_date >= '{ANALYSIS_START_DATE}') seg ON u.user_id = seg.user_id
        LEFT JOIN (SELECT DISTINCT user_id FROM `{TABLES['customer_journey']}`) aut ON u.user_id = aut.user_id
        LEFT JOIN (SELECT DISTINCT user_id FROM `{TABLES['sms']}` WHERE metrics.message.outbound.delivered_message_count > 0) sms ON u.user_id = sms.user_id
        LEFT JOIN (SELECT DISTINCT user_id FROM `{TABLES['email_sends']}` WHERE send_date >= '{ANALYSIS_START_DATE}' AND sends.delivered > 0) em ON u.user_id = em.user_id
    ),
    wau AS (
        SELECT DISTINCT user_id FROM `{TABLES['users_weekly_rollup']}`
        WHERE week = DATE_TRUNC(CURRENT_DATE(), WEEK(SUNDAY)) AND wau = TRUE
    )
    SELECT p.product_count,
        COUNT(DISTINCT p.user_id) AS users,
        COUNT(DISTINCT CASE WHEN w.user_id IS NOT NULL THEN p.user_id END) AS wau_users,
        ROUND(SAFE_DIVIDE(COUNT(DISTINCT CASE WHEN w.user_id IS NOT NULL THEN p.user_id END), COUNT(DISTINCT p.user_id)) * 100, 1) AS wau_pct
    FROM products p
    LEFT JOIN wau w ON p.user_id = w.user_id
    GROUP BY p.product_count
    ORDER BY p.product_count
    """
