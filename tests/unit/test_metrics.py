"""Unit tests for every formula in the appendix."""

from agent.analysis.metrics import (
    rate, lift, delta, pct_reduction, segment_creation_rate,
    email_send_rate, wau_rate, disconnect_rate, disconnect_rate_reduction,
    upgrade_multiplier, free_to_paid_rate, paid_pct, product_attachment_multiplier,
)


class TestRate:
    def test_basic(self):
        assert rate(68, 100) == 68.0

    def test_zero_denominator(self):
        assert rate(10, 0) == 0.0

    def test_rounding(self):
        assert rate(1692, 2479) == 68.3


class TestLift:
    def test_basic(self):
        assert lift(68.3, 26.7) == 2.6

    def test_zero_base(self):
        assert lift(50, 0) == 0.0


class TestDelta:
    def test_positive(self):
        assert delta(82.0, 63.0) == 19.0

    def test_negative(self):
        assert delta(44.8, 88.7) == -43.9


class TestDisconnectRateReduction:
    def test_known_values(self):
        assert disconnect_rate_reduction(1.5, 0.9) == 40.0

    def test_zero_higher(self):
        assert disconnect_rate_reduction(0, 0) == 0.0


class TestUpgradeMultiplier:
    def test_known_values(self):
        result = upgrade_multiplier(0.223, 0.061)
        assert result == 3.7


class TestSegmentCreationRate:
    def test_known_values(self):
        assert segment_creation_rate(1692, 2479) == 68.3


class TestEmailSendRate:
    def test_known_values(self):
        assert email_send_rate(2198, 2479) == 88.7


class TestWauRate:
    def test_known_values(self):
        assert wau_rate(1934, 2693) == 71.8


class TestFreeToPaidRate:
    def test_known_values(self):
        assert free_to_paid_rate(25001, 25159) == 99.4


class TestPaidPct:
    def test_claude(self):
        assert paid_pct(1706, 2693) == 63.3


class TestProductAttachmentMultiplier:
    def test_sms(self):
        result = product_attachment_multiplier(7.9, 1.9)
        assert result == 4.2
