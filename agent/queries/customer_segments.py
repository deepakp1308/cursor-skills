"""Module 3: Customer segment analysis — industry, ecommerce, high-value, geography."""

from agent.config import TABLES


def industry_breakdown_sql() -> str:
    return f"""
    WITH ai_users AS (
        SELECT DISTINCT i.user_id,
            CASE WHEN LOWER(i.name) = 'chatgpt' THEN 'chatgpt' ELSE 'claude' END AS channel
        FROM `{TABLES['integrations']}` i
        WHERE i.type = 'oauth2' AND LOWER(i.name) IN ('chatgpt', 'claude')
    )
    SELECT a.channel, e.industry,
        COUNT(DISTINCT a.user_id) AS users,
        ROUND(SAFE_DIVIDE(
            COUNT(DISTINCT a.user_id),
            SUM(COUNT(DISTINCT a.user_id)) OVER (PARTITION BY a.channel)
        ) * 100, 1) AS pct_of_channel
    FROM ai_users a
    LEFT JOIN `{TABLES['genai_eligibility']}` e
        ON a.user_id = e.user_id AND e.month = DATE_TRUNC(CURRENT_DATE(), MONTH)
    GROUP BY a.channel, e.industry
    ORDER BY a.channel, users DESC
    """


def ecomm_and_high_value_sql() -> str:
    return f"""
    WITH ai_users AS (
        SELECT DISTINCT i.user_id,
            CASE WHEN LOWER(i.name) = 'chatgpt' THEN 'chatgpt' ELSE 'claude' END AS channel
        FROM `{TABLES['integrations']}` i
        WHERE i.type = 'oauth2' AND LOWER(i.name) IN ('chatgpt', 'claude')
    )
    SELECT a.channel,
        COUNT(DISTINCT a.user_id) AS total,
        COUNT(DISTINCT CASE WHEN e.ecomm_level IS NOT NULL AND e.ecomm_level != '' THEN a.user_id END) AS ecomm_users,
        ROUND(SAFE_DIVIDE(COUNT(DISTINCT CASE WHEN e.ecomm_level IS NOT NULL AND e.ecomm_level != '' THEN a.user_id END), COUNT(DISTINCT a.user_id)) * 100, 1) AS ecomm_pct,
        COUNT(DISTINCT CASE WHEN e.is_high_value = TRUE THEN a.user_id END) AS high_value_users,
        ROUND(SAFE_DIVIDE(COUNT(DISTINCT CASE WHEN e.is_high_value = TRUE THEN a.user_id END), COUNT(DISTINCT a.user_id)) * 100, 1) AS high_value_pct
    FROM ai_users a
    LEFT JOIN `{TABLES['genai_eligibility']}` e
        ON a.user_id = e.user_id AND e.month = DATE_TRUNC(CURRENT_DATE(), MONTH)
    GROUP BY a.channel
    """


def geography_breakdown_sql() -> str:
    return f"""
    WITH ai_users AS (
        SELECT DISTINCT i.user_id,
            CASE WHEN LOWER(i.name) = 'chatgpt' THEN 'chatgpt' ELSE 'claude' END AS channel
        FROM `{TABLES['integrations']}` i
        WHERE i.type = 'oauth2' AND LOWER(i.name) IN ('chatgpt', 'claude')
    )
    SELECT a.channel, e.country,
        COUNT(DISTINCT a.user_id) AS users,
        ROUND(SAFE_DIVIDE(
            COUNT(DISTINCT a.user_id),
            SUM(COUNT(DISTINCT a.user_id)) OVER (PARTITION BY a.channel)
        ) * 100, 1) AS pct_of_channel
    FROM ai_users a
    LEFT JOIN `{TABLES['genai_eligibility']}` e
        ON a.user_id = e.user_id AND e.month = DATE_TRUNC(CURRENT_DATE(), MONTH)
    WHERE e.country IS NOT NULL
    GROUP BY a.channel, e.country
    ORDER BY a.channel, users DESC
    LIMIT 40
    """


def language_breakdown_sql() -> str:
    return f"""
    WITH ai_users AS (
        SELECT DISTINCT i.user_id,
            CASE WHEN LOWER(i.name) = 'chatgpt' THEN 'chatgpt' ELSE 'claude' END AS channel
        FROM `{TABLES['integrations']}` i
        WHERE i.type = 'oauth2' AND LOWER(i.name) IN ('chatgpt', 'claude')
    )
    SELECT a.channel, e.language,
        COUNT(DISTINCT a.user_id) AS users,
        ROUND(SAFE_DIVIDE(
            COUNT(DISTINCT a.user_id),
            SUM(COUNT(DISTINCT a.user_id)) OVER (PARTITION BY a.channel)
        ) * 100, 1) AS pct_of_channel
    FROM ai_users a
    LEFT JOIN `{TABLES['genai_eligibility']}` e
        ON a.user_id = e.user_id AND e.month = DATE_TRUNC(CURRENT_DATE(), MONTH)
    WHERE e.language IS NOT NULL
    GROUP BY a.channel, e.language
    ORDER BY a.channel, users DESC
    """
