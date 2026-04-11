"""Module 1b: Marketing Analyzer impact queries — email/segment lift, retention, upgrades."""

from agent.config import TABLES, ANALYSIS_START_DATE


def analyzer_lift_sql() -> str:
    """Connector + Marketing Analyzer vs Connector alone on segments and emails."""
    return f"""
    WITH with_analyzer AS (
        SELECT DISTINCT i.user_id
        FROM `{TABLES['integrations']}` i
        JOIN `{TABLES['genai_eligibility']}` e
            ON i.user_id = e.user_id
            AND e.month = DATE_TRUNC(CURRENT_DATE(), MONTH)
            AND e.marketing_analyzer = TRUE
        WHERE i.type = 'oauth2' AND LOWER(i.name) IN ('chatgpt', 'claude')
    ),
    without_analyzer AS (
        SELECT DISTINCT i.user_id
        FROM `{TABLES['integrations']}` i
        WHERE i.type = 'oauth2' AND LOWER(i.name) IN ('chatgpt', 'claude')
            AND i.user_id NOT IN (SELECT user_id FROM with_analyzer)
    ),
    segments AS (
        SELECT user_id, SUM(all_action_count) AS seg_actions
        FROM `{TABLES['tags_segments']}`
        WHERE action_date >= '{ANALYSIS_START_DATE}' AND action_type LIKE '%segment%'
        GROUP BY user_id
    ),
    emails AS (
        SELECT user_id, SUM(sends.delivered) AS delivered
        FROM `{TABLES['email_sends']}`
        WHERE send_date >= '{ANALYSIS_START_DATE}'
        GROUP BY user_id
    )
    SELECT 'Connector + Marketing Analyzer' AS cohort,
        COUNT(DISTINCT a.user_id) AS users,
        ROUND(SAFE_DIVIDE(COUNT(DISTINCT CASE WHEN seg.user_id IS NOT NULL THEN a.user_id END), COUNT(DISTINCT a.user_id)) * 100, 1) AS segment_pct,
        ROUND(SAFE_DIVIDE(COUNT(DISTINCT CASE WHEN em.user_id IS NOT NULL THEN a.user_id END), COUNT(DISTINCT a.user_id)) * 100, 1) AS email_pct,
        ROUND(AVG(seg.seg_actions), 1) AS avg_seg_actions,
        ROUND(AVG(em.delivered), 0) AS avg_emails
    FROM with_analyzer a
    LEFT JOIN segments seg ON a.user_id = seg.user_id
    LEFT JOIN emails em ON a.user_id = em.user_id
    UNION ALL
    SELECT 'Connector alone' AS cohort,
        COUNT(DISTINCT a.user_id) AS users,
        ROUND(SAFE_DIVIDE(COUNT(DISTINCT CASE WHEN seg.user_id IS NOT NULL THEN a.user_id END), COUNT(DISTINCT a.user_id)) * 100, 1) AS segment_pct,
        ROUND(SAFE_DIVIDE(COUNT(DISTINCT CASE WHEN em.user_id IS NOT NULL THEN a.user_id END), COUNT(DISTINCT a.user_id)) * 100, 1) AS email_pct,
        ROUND(AVG(seg.seg_actions), 1) AS avg_seg_actions,
        ROUND(AVG(em.delivered), 0) AS avg_emails
    FROM without_analyzer a
    LEFT JOIN segments seg ON a.user_id = seg.user_id
    LEFT JOIN emails em ON a.user_id = em.user_id
    """


def retention_by_segment_behavior_sql() -> str:
    """Connector disconnect rate for segment creators vs non-creators."""
    return f"""
    WITH connector_paid AS (
        SELECT DISTINCT i.user_id
        FROM `{TABLES['integrations']}` i
        JOIN `{TABLES['genai_eligibility']}` e
            ON i.user_id = e.user_id
            AND e.month = DATE_TRUNC(CURRENT_DATE(), MONTH)
            AND e.monthly_plan IS NOT NULL
        WHERE i.type = 'oauth2' AND LOWER(i.name) IN ('chatgpt', 'claude')
    ),
    seg_creators AS (
        SELECT DISTINCT user_id
        FROM `{TABLES['tags_segments']}`
        WHERE action_date >= '2026-01-01' AND action_type LIKE '%segment%'
    ),
    churn AS (SELECT DISTINCT user_id FROM `{TABLES['churn']}`),
    disconnected AS (
        SELECT DISTINCT user_id
        FROM `{TABLES['integrations']}`
        WHERE type = 'oauth2' AND LOWER(name) IN ('chatgpt', 'claude') AND is_deleted = TRUE
    )
    SELECT
        CASE WHEN sc.user_id IS NOT NULL THEN 'Active segment creators'
             ELSE 'No segment activity' END AS behavior,
        COUNT(DISTINCT c.user_id) AS users,
        ROUND(SAFE_DIVIDE(COUNT(DISTINCT CASE WHEN ch.user_id IS NOT NULL THEN c.user_id END), COUNT(DISTINCT c.user_id)) * 100, 1) AS churn_pct,
        ROUND(SAFE_DIVIDE(COUNT(DISTINCT CASE WHEN d.user_id IS NOT NULL THEN c.user_id END), COUNT(DISTINCT c.user_id)) * 100, 1) AS disconnect_pct
    FROM connector_paid c
    LEFT JOIN churn ch ON c.user_id = ch.user_id
    LEFT JOIN disconnected d ON c.user_id = d.user_id
    LEFT JOIN seg_creators sc ON c.user_id = sc.user_id
    GROUP BY behavior
    """


def platform_churn_sql() -> str:
    return f"""
    SELECT
        COUNT(DISTINCT c.user_id) AS total,
        COUNT(DISTINCT CASE WHEN ch.user_id IS NOT NULL THEN c.user_id END) AS churned,
        ROUND(SAFE_DIVIDE(
            COUNT(DISTINCT CASE WHEN ch.user_id IS NOT NULL THEN c.user_id END),
            COUNT(DISTINCT c.user_id)
        ) * 100, 1) AS churn_pct
    FROM (
        SELECT DISTINCT i.user_id
        FROM `{TABLES['integrations']}` i
        JOIN `{TABLES['genai_eligibility']}` e
            ON i.user_id = e.user_id
            AND e.month = DATE_TRUNC(CURRENT_DATE(), MONTH)
            AND e.monthly_plan IS NOT NULL
        WHERE i.type = 'oauth2' AND LOWER(i.name) IN ('chatgpt', 'claude')
    ) c
    LEFT JOIN `{TABLES['churn']}` ch ON c.user_id = ch.user_id
    """


def upgrade_rate_sql() -> str:
    """Standard-to-Premium upgrade rate: active segmenters vs non-segmenters."""
    return f"""
    WITH std_jan AS (
        SELECT e.user_id,
            CASE WHEN e.user_id IN (
                SELECT DISTINCT user_id
                FROM `{TABLES['tags_segments']}`
                WHERE action_date >= '2025-10-01' AND action_date < '2026-01-01'
                    AND action_type LIKE '%segment%'
            ) THEN TRUE ELSE FALSE END AS active_segmenter
        FROM `{TABLES['genai_eligibility']}` e
        WHERE e.month = '2026-01-01'
            AND e.monthly_plan = 'standard'
            AND e.marketing_analyzer = TRUE
    ),
    apr AS (
        SELECT user_id, monthly_plan
        FROM `{TABLES['genai_eligibility']}`
        WHERE month = DATE_TRUNC(CURRENT_DATE(), MONTH)
    )
    SELECT
        CASE WHEN j.active_segmenter THEN 'Active segmenters' ELSE 'Non-segmenters' END AS cohort,
        COUNT(DISTINCT j.user_id) AS total,
        COUNT(DISTINCT CASE WHEN a.monthly_plan = 'premium' THEN j.user_id END) AS upgraded_premium,
        ROUND(SAFE_DIVIDE(
            COUNT(DISTINCT CASE WHEN a.monthly_plan = 'premium' THEN j.user_id END),
            COUNT(DISTINCT j.user_id)
        ) * 100, 3) AS upgrade_rate
    FROM std_jan j
    LEFT JOIN apr a ON j.user_id = a.user_id
    GROUP BY cohort
    """


def free_to_paid_conversion_sql() -> str:
    return f"""
    WITH free_cohorts AS (
        SELECT DISTINCT u.user_id,
            CASE
                WHEN u.user_id IN (
                    SELECT DISTINCT user_id FROM `{TABLES['integrations']}`
                    WHERE type = 'oauth2' AND LOWER(name) IN ('chatgpt', 'claude')
                ) THEN 'connector_free'
                WHEN u.user_id IN (
                    SELECT user_id FROM `{TABLES['genai_eligibility']}`
                    WHERE month = DATE_TRUNC(CURRENT_DATE(), MONTH) AND marketing_analyzer = TRUE
                ) THEN 'in_app_with_analyzer'
                ELSE 'platform_no_analyzer'
            END AS cohort
        FROM `{TABLES['users']}` u
        WHERE u.primary_plan_type = 'free'
    ),
    conversions AS (
        SELECT DISTINCT user_id
        FROM `{TABLES['orders']}`
        WHERE new_conversion = TRUE AND ordered_at >= '{ANALYSIS_START_DATE}'
    )
    SELECT f.cohort,
        COUNT(DISTINCT f.user_id) AS free_users,
        COUNT(DISTINCT CASE WHEN c.user_id IS NOT NULL THEN f.user_id END) AS converted,
        ROUND(SAFE_DIVIDE(
            COUNT(DISTINCT CASE WHEN c.user_id IS NOT NULL THEN f.user_id END),
            COUNT(DISTINCT f.user_id)
        ) * 100, 2) AS conversion_rate
    FROM free_cohorts f
    LEFT JOIN conversions c ON f.user_id = c.user_id
    GROUP BY f.cohort
    ORDER BY conversion_rate DESC
    """
