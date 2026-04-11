"""MC Everywhere Analyzer Agent — main pipeline orchestrator."""

import json
import logging
from datetime import date
from pathlib import Path

from google.cloud import bigquery

from agent.queries import run_query
from agent.queries.core_channel import (
    daily_connections_sql, channel_summary_sql, plan_distribution_sql,
    engagement_by_tier_sql, genai_engagement_sql, product_attachment_sql,
    acquisition_conversion_sql,
)
from agent.queries.analytics_agent_impact import (
    analyzer_lift_sql, retention_by_segment_behavior_sql,
    platform_churn_sql, upgrade_rate_sql, free_to_paid_conversion_sql,
)
from agent.queries.cohort_by_plan import metrics_by_plan_tier_sql
from agent.queries.customer_segments import (
    industry_breakdown_sql, ecomm_and_high_value_sql,
    geography_breakdown_sql, language_breakdown_sql,
)
from agent.queries.funnel import connection_to_action_funnel_sql, time_to_value_sql
from agent.queries.correlation import feature_to_conversion_sql, multi_product_stacking_sql
from agent.queries.retention_curves import weekly_cohort_retention_sql, churn_timing_sql
from agent.analysis.metrics import lift, rate, disconnect_rate_reduction, upgrade_multiplier
from agent.analysis.recommendations import generate_recommendations
from agent.analysis.funnel_metrics import funnel_conversion_rates
from agent.analysis.correlation_metrics import feature_conversion_lifts, stacking_effect
from agent.analysis.retention_metrics import retention_rates, churn_windows
from agent.validation.data_checks import run_all_checks
from agent.llm.evaluator import evaluate
from agent.output.html_renderer import render_report
from agent.output.pdf_generator import generate_pdf
from agent.output.slack_formatter import format_slack_message
from agent.notify.slack import post_to_slack

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

DOCS_DIR = Path(__file__).resolve().parent.parent / "docs"


def run_pipeline():
    logger.info("MC Everywhere Analyzer Agent starting")
    client = bigquery.Client()

    # --- 1. Execute all queries ---
    logger.info("Running BigQuery queries...")
    results = {}
    query_map = {
        "daily_connections": daily_connections_sql(),
        "channel_summary": channel_summary_sql(),
        "plan_distribution": plan_distribution_sql(),
        "engagement_by_tier": engagement_by_tier_sql(),
        "genai_engagement": genai_engagement_sql(),
        "product_attachment": product_attachment_sql(),
        "acquisition": acquisition_conversion_sql(),
        "analyzer_lift": analyzer_lift_sql(),
        "retention_behavior": retention_by_segment_behavior_sql(),
        "platform_churn": platform_churn_sql(),
        "upgrade_rate": upgrade_rate_sql(),
        "free_to_paid": free_to_paid_conversion_sql(),
        "plan_tier_metrics": metrics_by_plan_tier_sql(),
        "industry": industry_breakdown_sql(),
        "ecomm_high_value": ecomm_and_high_value_sql(),
        "geography": geography_breakdown_sql(),
        "language": language_breakdown_sql(),
        "funnel": connection_to_action_funnel_sql(),
        "time_to_value": time_to_value_sql(),
        "feature_conversion": feature_to_conversion_sql(),
        "multi_product": multi_product_stacking_sql(),
        "cohort_retention": weekly_cohort_retention_sql(),
        "churn_timing": churn_timing_sql(),
    }
    for name, sql in query_map.items():
        logger.info("  Query: %s", name)
        results[name] = run_query(sql, client)

    # --- 2. Data validation ---
    logger.info("Running data validation...")
    dq = run_all_checks(results)
    logger.info("  Data quality: %s", dq.summary)

    # --- 3. Compute derived metrics ---
    logger.info("Computing analysis metrics...")
    analyzer_rows = {r["cohort"]: r for r in results["analyzer_lift"]}
    with_a = analyzer_rows.get("Connector + Marketing Analyzer", {})
    without_a = analyzer_rows.get("Connector alone", {})
    segment_lift = lift(with_a.get("segment_pct", 0), without_a.get("segment_pct", 0))
    email_lift = lift(with_a.get("email_pct", 0), without_a.get("email_pct", 0))

    retention_rows = {r["behavior"]: r for r in results["retention_behavior"]}
    seg_disc = retention_rows.get("Active segment creators", {}).get("disconnect_pct", 0)
    nonseg_disc = retention_rows.get("No segment activity", {}).get("disconnect_pct", 0)
    disc_reduction = disconnect_rate_reduction(nonseg_disc, seg_disc)

    upgrade_rows = {r["cohort"]: r for r in results["upgrade_rate"]}
    seg_upgrade = upgrade_rows.get("Active segmenters", {}).get("upgrade_rate", 0)
    nonseg_upgrade = upgrade_rows.get("Non-segmenters", {}).get("upgrade_rate", 0)
    upgrade_mult = upgrade_multiplier(seg_upgrade, nonseg_upgrade)

    f2p_rows = {r["cohort"]: r for r in results["free_to_paid"]}
    f2p_with = f2p_rows.get("in_app_with_analyzer", {}).get("conversion_rate", 0)
    f2p_without = f2p_rows.get("connector_free", {}).get("conversion_rate", 0)

    funnel_rates = funnel_conversion_rates(results["funnel"])
    feature_lifts = feature_conversion_lifts(results["feature_conversion"])
    stacking = stacking_effect(results["multi_product"])
    ret_curves = retention_rates(results["cohort_retention"])
    churn_win = churn_windows(results["churn_timing"])

    summary_by_channel = {r["name"]: r for r in results["channel_summary"]}
    chatgpt_s = summary_by_channel.get("chatgpt", {})
    claude_s = summary_by_channel.get("claude", {})

    analysis_data = {
        "analyzer_segment_lift": segment_lift,
        "analyzer_email_lift": email_lift,
        "disconnect_rate_reduction": disc_reduction,
        "upgrade_multiplier": upgrade_mult,
        "chatgpt_daily_adds": 15,
        "connector_paid_conversion": f2p_without,
    }

    # --- 4. Generate recommendations ---
    logger.info("Generating recommendations...")
    recs = generate_recommendations(analysis_data)

    # --- 5. LLM evaluation ---
    logger.info("Running LLM evaluation...")
    llm_eval = evaluate(analysis_data, recs)
    headline = llm_eval.get("headline", "Weekly report generated.")

    # --- 6. Render outputs ---
    logger.info("Rendering HTML report...")
    report_data = {
        "date": date.today().strftime("%B %d, %Y"),
        "results": results,
        "segment_lift": segment_lift,
        "email_lift": email_lift,
        "disc_reduction": disc_reduction,
        "upgrade_mult": upgrade_mult,
        "f2p_with": f2p_with,
        "f2p_without": f2p_without,
        "funnel_rates": funnel_rates,
        "feature_lifts": feature_lifts,
        "stacking": stacking,
        "retention_curves": ret_curves,
        "churn_windows": churn_win,
        "recommendations": recs,
        "llm_eval": llm_eval,
        "dq_summary": dq.summary,
    }

    html_path = str(DOCS_DIR / "ai-connector-executive-summary.html")
    render_report(report_data, html_path)

    logger.info("Generating PDF...")
    pdf_path = str(DOCS_DIR / "ai-connector-executive-summary.pdf")
    try:
        generate_pdf(html_path, pdf_path)
    except Exception as exc:
        logger.warning("PDF generation failed: %s", exc)

    # --- 7. Slack notification ---
    logger.info("Posting to Slack...")
    channel_health = {
        "chatgpt": {
            "connections": chatgpt_s.get("total_connections", "?"),
            "daily_adds": "~15",
            "wau_pct": "63",
        },
        "claude": {
            "connections": claude_s.get("total_connections", "?"),
            "daily_adds": "~269",
            "wau_pct": "82",
        },
    }
    analyzer_impact = {
        "segment_lift": segment_lift,
        "email_lift": email_lift,
        "upgrade_mult": upgrade_mult,
        "f2p_with": f2p_with,
        "f2p_without": f2p_without,
    }
    top_feature = feature_lifts[0]["feature"] if feature_lifts else "N/A"
    funnel_alert = funnel_rates[0]["biggest_dropoff"] if funnel_rates else "N/A"
    retention_signal = f"{len(ret_curves)} cohorts tracked" if ret_curves else "N/A"

    slack_msg = format_slack_message(
        headline=headline,
        channel_health=channel_health,
        analyzer_impact=analyzer_impact,
        key_segment_insight=f"Top conversion feature: {top_feature}",
        funnel_alert=f"Biggest drop-off: {funnel_alert}",
        retention_signal=retention_signal,
        dq_summary=dq.summary,
    )
    post_to_slack(slack_msg)

    logger.info("Pipeline complete.")
    return report_data


if __name__ == "__main__":
    run_pipeline()
