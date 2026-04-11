"""Unit tests for data validation logic."""

from agent.validation.data_checks import check_row_count, check_null_rate, DataQualityResult


class TestRowCount:
    def test_above_minimum(self):
        status, _ = check_row_count(5000, "test", minimum=1000)
        assert status == "pass"

    def test_below_minimum(self):
        status, _ = check_row_count(500, "test", minimum=1000)
        assert status == "warn"


class TestNullRate:
    def test_no_nulls(self):
        rows = [{"channel": "chatgpt"}, {"channel": "claude"}]
        status, _ = check_null_rate(rows, "channel")
        assert status == "pass"

    def test_all_nulls(self):
        rows = [{"channel": None}, {"channel": None}]
        status, _ = check_null_rate(rows, "channel", max_rate=0.05)
        assert status == "warn"

    def test_empty_rows(self):
        status, _ = check_null_rate([], "channel")
        assert status == "warn"


class TestDataQualityResult:
    def test_all_pass(self):
        dq = DataQualityResult()
        dq.add("test1", "pass")
        dq.add("test2", "pass")
        assert dq.passed is True
        assert dq.summary == "All checks passed"

    def test_with_failure(self):
        dq = DataQualityResult()
        dq.add("test1", "pass")
        dq.add("test2", "fail", "bad data")
        assert dq.passed is False
        assert "1 failed" in dq.summary
