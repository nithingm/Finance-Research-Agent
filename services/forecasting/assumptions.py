from __future__ import annotations
from dataclasses import dataclass
from typing import Optional

@dataclass(frozen=True)
class Scenario:
    # Growth and margins
    revenue_growth_qoq: float  # quarterly growth rate (e.g., 0.02 for ~8.2% annualized)
    target_gross_margin: float  # 0..1
    target_operating_margin: float  # 0..1

    # Working capital days
    dso: float
    dio: float
    dpo: float

    # Capex and depreciation
    capex_pct_revenue: float  # 0..1
    da_pct_revenue: float     # simple rule of thumb for MVP

    # Taxes and financing
    tax_rate: float  # 0..1
    net_interest_rate: float = 0.0  # net interest as % of beginning net cash/debt (simplified)


def validate_scenario(s: Scenario) -> None:
    if not (0.0 <= s.target_gross_margin <= 0.95):
        raise ValueError("gross margin must be between 0 and 95% for MVP guardrails")
    if not (0.0 <= s.target_operating_margin <= 0.6):
        raise ValueError("operating margin must be between 0 and 60% for MVP guardrails")
    if not (0.0 <= s.tax_rate <= 0.5):
        raise ValueError("tax rate must be between 0 and 50% for MVP")
    if not (0.0 <= s.capex_pct_revenue <= 0.5):
        raise ValueError("capex % revenue must be between 0 and 50% for MVP")
    if not (0.0 <= s.da_pct_revenue <= 0.3):
        raise ValueError("D&A % revenue must be between 0 and 30% for MVP")

