"""LLM evaluation tests — verify fallback and output structure."""

from agent.llm.evaluator import _fallback_evaluation


def test_fallback_has_required_fields():
    metrics = {"analyzer_segment_lift": 2.6}
    recs = [
        {"category": "marketing_analyzer", "priority": "high",
         "finding": "test", "recommendation": "test"},
    ]
    result = _fallback_evaluation(metrics, recs)
    assert "headline" in result
    assert "anomalies" in result
    assert "recommendation_evaluations" in result
    assert len(result["recommendation_evaluations"]) == 1
    assert result["recommendation_evaluations"][0]["confidence"] == "medium"


def test_fallback_with_empty_recs():
    result = _fallback_evaluation({}, [])
    assert result["headline"] != ""
    assert result["recommendation_evaluations"] == []
