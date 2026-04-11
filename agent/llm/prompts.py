"""Structured prompts for the LLM evaluator."""

EVALUATION_PROMPT = """You are evaluating a weekly analytics report on Mailchimp's AI connector channels (ChatGPT and Claude).

## Computed Metrics
{metrics_json}

## Draft Recommendations
{recommendations_json}

## Your Tasks
1. Verify each recommendation is logically supported by the data. Flag any that are not.
2. Flag any metrics that appear anomalous (unexpected values, large week-over-week swings).
3. Write a 2-3 sentence executive headline summarizing the most important finding this week.
4. For each recommendation, assign a confidence level: high, medium, or low.

## Output Format (JSON)
{{
  "headline": "...",
  "anomalies": ["..."],
  "recommendation_evaluations": [
    {{
      "category": "...",
      "confidence": "high|medium|low",
      "supported": true|false,
      "note": "..."
    }}
  ]
}}
"""
