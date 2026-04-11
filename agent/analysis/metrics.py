"""Pure metric computation functions — each maps to one formula in the appendix."""


def rate(numerator: int | float, denominator: int | float) -> float:
    if not denominator:
        return 0.0
    return round((numerator / denominator) * 100, 1)


def lift(rate_a: float, rate_b: float) -> float:
    if not rate_b:
        return 0.0
    return round(rate_a / rate_b, 1)


def delta(rate_a: float, rate_b: float) -> float:
    return round(rate_a - rate_b, 1)


def pct_reduction(higher: float, lower: float) -> float:
    if not higher:
        return 0.0
    return round((higher - lower) / higher * 100, 1)


def multiplier(rate_a: float, rate_b: float) -> float:
    return lift(rate_a, rate_b)


def segment_creation_rate(creators: int, total: int) -> float:
    return rate(creators, total)


def email_send_rate(senders: int, total: int) -> float:
    return rate(senders, total)


def wau_rate(wau_users: int, total: int) -> float:
    return rate(wau_users, total)


def disconnect_rate(disconnected: int, total: int) -> float:
    return rate(disconnected, total)


def disconnect_rate_reduction(non_seg_disconnect: float, seg_disconnect: float) -> float:
    return pct_reduction(non_seg_disconnect, seg_disconnect)


def upgrade_multiplier(segmenter_rate: float, non_segmenter_rate: float) -> float:
    return multiplier(segmenter_rate, non_segmenter_rate)


def free_to_paid_rate(converted: int, free_users: int) -> float:
    return rate(converted, free_users)


def paid_pct(paid_users: int, total: int) -> float:
    return rate(paid_users, total)


def product_attachment_multiplier(ai_rate: float, platform_rate: float) -> float:
    return lift(ai_rate, platform_rate)
