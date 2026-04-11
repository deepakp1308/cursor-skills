"""Post messages to Slack via incoming webhook."""

import json
import logging
import requests

from agent.config import SLACK_WEBHOOK_URL

logger = logging.getLogger(__name__)


def post_to_slack(message: str, webhook_url: str = "") -> bool:
    url = webhook_url or SLACK_WEBHOOK_URL
    if not url:
        logger.warning("No SLACK_WEBHOOK_URL configured; skipping Slack post")
        return False

    payload = {"text": message, "mrkdwn": True}
    try:
        resp = requests.post(url, json=payload, timeout=30)
        resp.raise_for_status()
        logger.info("Slack message posted successfully")
        return True
    except requests.RequestException as exc:
        logger.error("Failed to post to Slack: %s", exc)
        return False
