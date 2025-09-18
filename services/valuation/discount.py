from __future__ import annotations
from typing import Iterable, List


def discount_factors(rate: float, periods: int) -> List[float]:
    """Return [1/(1+r)^1, ..., 1/(1+r)^periods]."""
    return [1.0 / ((1.0 + rate) ** t) for t in range(1, periods + 1)]


def present_value(cashflows: Iterable[float], rate: float) -> float:
    total = 0.0
    for t, cf in enumerate(cashflows, start=1):
        total += float(cf) / ((1.0 + rate) ** t)
    return total

