from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class TerminalInputs:
    last_fcf: float   # first cash flow of perpetuity sequence (FCF at T+1)
    wacc: float
    g: float


def gordon_pv(i: TerminalInputs) -> float:
    """Gordon growth (perpetuity) present value at terminal date.
    Caller must ensure g < WACC. No discounting to present applied here.
    """
    if i.wacc <= i.g:
        raise ValueError("Terminal growth must be < WACC")
    return float(i.last_fcf / (i.wacc - i.g))

