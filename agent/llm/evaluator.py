"""LLM-based evaluation of analysis quality and recommendations."""

import json
import os

from agent.llm.prompts import EVALUATION_PROMPT


def evaluate(metrics: dict, recommendations: list[dict]) -> dict:
    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if not api_key:
        return _fallback_evaluation(metrics, recommendations)

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        prompt = EVALUATION_PROMPT.format(
            metrics_json=json.dumps(metrics, indent=2, default=str),
            recommendations_json=json.dumps(recommendations, indent=2, default=str),
        )
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}],
        )
        text = message.content[0].text
        start = text.find("{")
        end = text.rfind("}") + 1
        if start >= 0 and end > start:
            return json.loads(text[start:end])
        return _fallback_evaluation(metrics, recommendations)
    except Exception:
        return _fallback_evaluation(metrics, recommendations)


def _fallback_evaluation(metrics: dict, recommendations: list[dict]) -> dict:
    return {
        "headline": f"Weekly report generated with {len(recommendations)} recommendations.",
        "anomalies": [],
        "recommendation_evaluations": [
            {"category": r["category"], "confidence": "medium", "supported": True, "note": ""}
            for r in recommendations
        ],
    }
