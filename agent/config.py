"""Configuration constants for the MC Everywhere Analyzer Agent."""

import os

BQ_PROJECT = os.getenv("BQ_PROJECT", "mc-business-intelligence")

CONNECTOR_NAMES = ("chatgpt", "claude")
CONNECTOR_TYPE = "oauth2"

ANALYSIS_START_DATE = "2025-12-01"

DATASETS = {
    "reporting": "bi_reporting",
    "reporting_beta": "bi_reporting_beta",
    "activities": "bi_activities",
    "product": "bi_product",
    "data_science": "bi_data_science",
}

TABLES = {
    "integrations": f"{BQ_PROJECT}.{DATASETS['reporting']}.integrations",
    "users": f"{BQ_PROJECT}.{DATASETS['reporting']}.users",
    "users_weekly_rollup": f"{BQ_PROJECT}.{DATASETS['reporting']}.users_weekly_rollup",
    "orders": f"{BQ_PROJECT}.{DATASETS['reporting']}.orders",
    "tags_segments": f"{BQ_PROJECT}.{DATASETS['reporting']}.tags_segments_daily_rollup",
    "email_sends": f"{BQ_PROJECT}.{DATASETS['reporting']}.daily_email_send_stats",
    "customer_journey": f"{BQ_PROJECT}.{DATASETS['reporting']}.emails_customer_journey",
    "sms": f"{BQ_PROJECT}.{DATASETS['reporting']}.sms_daily_rollup",
    "transactional": f"{BQ_PROJECT}.{DATASETS['reporting']}.daily_transactional_sends",
    "messaging_outreach": f"{BQ_PROJECT}.{DATASETS['reporting']}.messaging_outreach_daily_rollup",
    "churn": f"{BQ_PROJECT}.{DATASETS['reporting']}.churn_details",
    "daily_logins": f"{BQ_PROJECT}.{DATASETS['reporting']}.daily_logins",
    "ecommerce": f"{BQ_PROJECT}.{DATASETS['reporting']}.ecommerce_orders_daily_rollup",
    "audiences": f"{BQ_PROJECT}.{DATASETS['reporting']}.audiences_daily_rollup",
    "genai_eligibility": f"{BQ_PROJECT}.{DATASETS['reporting_beta']}.monthly_genai_user_eligibility",
}

PLAN_TIERS = ("free", "standard", "legacy", "premium")

VALIDATION_THRESHOLDS = {
    "min_connector_users": 1000,
    "max_null_rate": 0.05,
    "max_freshness_hours": 72,
    "rate_min": 0.0,
    "rate_max": 100.0,
    "max_wow_change": 0.50,
}

SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
REPORT_URL = "https://deepakp1308.github.io/cursor-skills/ai-connector-executive-summary.html"
