from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any, List
from services.forecasting.assumptions import Scenario, validate_scenario


def project_12q(history_last_q: Dict[str, float], scenario: Scenario) -> List[Dict[str, Any]]:
    """Project 12 quarters given last historical quarter and scenario.

    Inputs (history_last_q) expected keys (subset):
    - revenue, cogs, ebit, da (optional), ar, inventory, ap, cash (optional), shares (optional)

    Outputs: list of 12 rows with fields:
    - revenue, cogs, gross_profit, ebit, tax, net_income
    - ar, inventory, ap, delta_nwc, cfo, capex, cfi, cff, delta_cash (cash optional)
    - da

    Accounting identities enforced where possible:
    - CFO = NOPAT + D&A - ΔNWC (simplified; excludes interest/SBC for MVP)
    - CFI = -Capex (MVP simplification)
    - ΔCash = CFO + CFI + CFF (CFF defaults to 0 in MVP)
    """
    validate_scenario(scenario)

    rows: List[Dict[str, Any]] = []

    rev = float(history_last_q.get("revenue", 0.0))
    ar = float(history_last_q.get("ar", 0.0))
    inv = float(history_last_q.get("inventory", 0.0))
    ap = float(history_last_q.get("ap", 0.0))

    for t in range(1, 13):
        # Revenue
        rev = rev * (1.0 + scenario.revenue_growth_qoq)
        gross_margin = scenario.target_gross_margin
        op_margin = scenario.target_operating_margin
        cogs = rev * (1.0 - gross_margin)
        ebit = rev * op_margin

        # D&A and capex
        da = rev * scenario.da_pct_revenue
        capex = rev * scenario.capex_pct_revenue

        # Working capital levels from days
        days = 90
        ar_level = (scenario.dso / days) * rev
        inv_level = (scenario.dio / days) * cogs if cogs else 0.0
        ap_level = (scenario.dpo / days) * cogs if cogs else 0.0
        delta_nwc = (ar_level - ar) + (inv_level - inv) - (ap_level - ap)

        # Taxes on operating income
        tax = max(0.0, ebit * scenario.tax_rate)
        nopat = ebit - tax

        # Cash flow components (simplified MVP)
        cfo = nopat + da - delta_nwc
        cfi = -capex
        cff = 0.0
        delta_cash = cfo + cfi + cff

        row = {
            "revenue": rev,
            "cogs": cogs,
            "gross_profit": rev - cogs,
            "ebit": ebit,
            "tax": tax,
            "net_income": nopat,  # no interest for MVP
            "da": da,
            "capex": capex,
            "ar": ar_level,
            "inventory": inv_level,
            "ap": ap_level,
            "delta_nwc": delta_nwc,
            "cfo": cfo,
            "cfi": cfi,
            "cff": cff,
            "delta_cash": delta_cash,
        }

        rows.append(row)

        # roll working capital forward for next period base
        ar, inv, ap = ar_level, inv_level, ap_level

    return rows

