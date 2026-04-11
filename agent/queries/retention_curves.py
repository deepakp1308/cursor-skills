"""Module 6: Cohort retention curves — weekly retention by connection cohort, churn timing."""

from agent.config import TABLES


def weekly_cohort_retention_sql() -> str:
    return f"""
    WITH cohorts AS (
        SELECT DISTINCT i.user_id,
            CASE WHEN LOWER(i.name) = 'chatgpt' THEN 'chatgpt' ELSE 'claude' END AS channel,
            DATE_TRUNC(DATE(i.created_at), WEEK(SUNDAY)) AS cohort_week
        FROM `{TABLES['integrations']}` i
        WHERE i.type = 'oauth2' AND LOWER(i.name) IN ('chatgpt', 'claude')
    ),
    weekly_activity AS (
        SELECT user_id, week
        FROM `{TABLES['users_weekly_rollup']}`
        WHERE wau = TRUE
    )
    SELECT c.channel, c.cohort_week,
        COUNT(DISTINCT c.user_id) AS cohort_size,
        COUNT(DISTINCT CASE WHEN wa.week = c.cohort_week THEN c.user_id END) AS week_0,
        COUNT(DISTINCT CASE WHEN wa.week = DATE_ADD(c.cohort_week, INTERVAL 1 WEEK) THEN c.user_id END) AS week_1,
        COUNT(DISTINCT CASE WHEN wa.week = DATE_ADD(c.cohort_week, INTERVAL 2 WEEK) THEN c.user_id END) AS week_2,
        COUNT(DISTINCT CASE WHEN wa.week = DATE_ADD(c.cohort_week, INTERVAL 4 WEEK) THEN c.user_id END) AS week_4,
        COUNT(DISTINCT CASE WHEN wa.week = DATE_ADD(c.cohort_week, INTERVAL 8 WEEK) THEN c.user_id END) AS week_8,
        COUNT(DISTINCT CASE WHEN wa.week = DATE_ADD(c.cohort_week, INTERVAL 12 WEEK) THEN c.user_id END) AS week_12
    FROM cohorts c
    LEFT JOIN weekly_activity wa ON c.user_id = wa.user_id
    GROUP BY c.channel, c.cohort_week
    ORDER BY c.channel, c.cohort_week
    """


def churn_timing_sql() -> str:
    """When do connector users churn relative to connection date?"""
    return f"""
    WITH connector_users AS (
        SELECT DISTINCT i.user_id,
            CASE WHEN LOWER(i.name) = 'chatgpt' THEN 'chatgpt' ELSE 'claude' END AS channel,
            DATE(i.created_at) AS connected_date,
            DATE(i.deleted_at) AS deleted_date
        FROM `{TABLES['integrations']}` i
        WHERE i.type = 'oauth2' AND LOWER(i.name) IN ('chatgpt', 'claude')
            AND i.is_deleted = TRUE
    )
    SELECT channel,
        COUNT(*) AS total_churned,
        COUNT(CASE WHEN DATE_DIFF(deleted_date, connected_date, DAY) <= 7 THEN 1 END) AS churned_week1,
        COUNT(CASE WHEN DATE_DIFF(deleted_date, connected_date, DAY) BETWEEN 8 AND 30 THEN 1 END) AS churned_month1,
        COUNT(CASE WHEN DATE_DIFF(deleted_date, connected_date, DAY) BETWEEN 31 AND 60 THEN 1 END) AS churned_month2,
        COUNT(CASE WHEN DATE_DIFF(deleted_date, connected_date, DAY) > 60 THEN 1 END) AS churned_after_60d,
        ROUND(AVG(DATE_DIFF(deleted_date, connected_date, DAY)), 1) AS avg_days_to_churn
    FROM connector_users
    GROUP BY channel
    """
