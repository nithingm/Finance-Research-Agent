from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class WACCInputs:
    rf: float      # risk-free rate
    erp: float     # equity risk premium
    beta: float    # levered beta
    tax_rate: float
    debt_ratio: float  # D / (D + E)
    equity_ratio: float  # E / (D + E)
    rd: float      # pre-tax cost of debt


def wacc(i: WACCInputs) -> float:
    """Weighted Average Cost of Capital.
    Cost of equity = rf + beta * erp
    After-tax cost of debt = rd * (1 - tax_rate)
    WACC = E/(D+E) * CoE + D/(D+E) * CoD_aftertax
    Guardrails: g < WACC to be checked by caller where needed.
    """
    coe = i.rf + i.beta * i.erp
    cod = i.rd * (1.0 - i.tax_rate)
    return float(i.equity_ratio * coe + i.debt_ratio * cod)

