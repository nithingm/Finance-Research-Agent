from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any

@dataclass(frozen=True)
class FCFFInputs:
    ebit: float
    tax_rate: float  # effective tax on operating income (0..1)
    da: float        # depreciation & amortization
    capex: float
    delta_nwc: float


def fcff(i: FCFFInputs) -> float:
    """Free Cash Flow to Firm: NOPAT + D&A - Capex - ΔNWC."""
    nopat = i.ebit * (1.0 - i.tax_rate)
    return float(nopat + i.da - i.capex - i.delta_nwc)

