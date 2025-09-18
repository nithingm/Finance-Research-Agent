from __future__ import annotations
from dataclasses import dataclass
from typing import List, Dict, Any, Tuple
from datetime import datetime


@dataclass(frozen=True)
class PeriodRow:
    period_end: str  # ISO date YYYY-MM-DD
    period_type: str  # 'A' or 'Q'
    currency: str | None = None
    # arbitrary numeric fields stored in extras
    extras: Dict[str, float] | None = None


def _parse_date(d: str) -> datetime:
    return datetime.strptime(d, "%Y-%m-%d")


def _days_in_period(ptype: str) -> int:
    return 365 if ptype.upper() == "A" else 90


def stitch_periods(
    annual: List[Dict[str, Any]], quarterly: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """Stitch annual (A) and quarterly (Q) rows into a single tidy list.

    - Expect each row to contain at least: period_end (YYYY-MM-DD), period_type ('A'|'Q')
    - Normalize keys to lower snake case; keep numeric fields as-is
    - Drop exact duplicates (same period_end & period_type)
    - Sort ascending by period_end, then A before Q for same date
    - Ensure no overlapping duplicate periods per period_type
    """
    def norm(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        out: List[Dict[str, Any]] = []
        for r in rows:
            pe = str(r.get("period_end") or r.get("periodEnd"))
            pt = str(r.get("period_type") or r.get("periodType") or r.get("type") or "").upper()
            if not pe or pt not in {"A", "Q"}:
                continue
            o = {k: v for k, v in r.items()}
            o["period_end"], o["period_type"] = pe, pt
            out.append(o)
        return out

    a = norm(annual)
    q = norm(quarterly)

    seen: set[Tuple[str, str]] = set()
    merged: List[Dict[str, Any]] = []
    for r in a + q:
        key = (r["period_end"], r["period_type"])
        if key in seen:
            continue
        seen.add(key)
        merged.append(r)

    merged.sort(key=lambda r: (_parse_date(r["period_end"]), r["period_type"]))
    return merged


def validate_accounting_identities(rows: List[Dict[str, Any]], eps: float = 1e-3) -> bool:
    """Validate CFO+CFI+CFF == delta_cash across consecutive periods (when present).
    Returns True if identities hold for all comparable consecutive rows, else False.
    Missing fields are ignored for that pair.
    """
    ok = True
    prev_cash = None
    prev_date = None
    for r in rows:
        cash = r.get("cash")
        if cash is not None and prev_cash is not None and prev_date is not None:
            cfo, cfi, cff = r.get("cfo"), r.get("cfi"), r.get("cff")
            if cfo is not None and cfi is not None and cff is not None:
                delta = float(cfo) + float(cfi) + float(cff)
                obs = float(cash) - float(prev_cash)
                if abs(delta - obs) > eps:
                    ok = False
        prev_cash = cash if cash is not None else prev_cash
        prev_date = r.get("period_end")
    return ok

