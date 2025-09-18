from __future__ import annotations
from typing import Dict, Any, List


def safe_div(a: float, b: float) -> float:
    try:
        return float(a) / float(b) if b not in (0, None) else 0.0
    except Exception:
        return 0.0


def compute_margins(row: Dict[str, Any]) -> Dict[str, float]:
    rev = row.get("revenue")
    gp = row.get("gross_profit")
    ebit = row.get("ebit")
    margins = {}
    if rev not in (None, 0):
        if gp is not None:
            margins["gross_margin"] = safe_div(gp, rev)
        if ebit is not None:
            margins["operating_margin"] = safe_div(ebit, rev)
    return margins


def compute_turnover_days(row: Dict[str, Any], days: int) -> Dict[str, float]:
    out: Dict[str, float] = {}
    rev = row.get("revenue")
    cogs = row.get("cogs")
    ar = row.get("ar")
    inv = row.get("inventory")
    ap = row.get("ap")
    if rev and ar is not None:
        out["dso"] = days * safe_div(ar, rev)
    if cogs and inv is not None:
        out["dio"] = days * safe_div(inv, cogs)
    if cogs and ap is not None:
        out["dpo"] = days * safe_div(ap, cogs)
    return out


def compute_capex_ratio(row: Dict[str, Any]) -> Dict[str, float]:
    capex = row.get("capex")
    rev = row.get("revenue")
    return {"capex_pct_revenue": safe_div(capex, rev)} if (capex is not None and rev) else {}


def enrich_with_kpis(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for r in rows:
        days = 365 if str(r.get("period_type")).upper() == "A" else 90
        k = {}
        k.update(compute_margins(r))
        k.update(compute_turnover_days(r, days))
        k.update(compute_capex_ratio(r))
        out.append({**r, **k})
    return out

