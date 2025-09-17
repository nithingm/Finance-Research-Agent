from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
import re

SEC_BASE = "https://data.sec.gov/api"


def normalize_cik(cik: str | int) -> str:
    s = str(cik)
    s = re.sub(r"[^0-9]", "", s)
    return f"CIK{int(s):010d}"


def build_company_facts_url(cik: str | int) -> str:
    ncik = normalize_cik(cik)
    return f"{SEC_BASE}/xbrl/companyfacts/{ncik}.json"


def build_frames_url(taxonomy: str, tag: str, unit: str, period: str) -> str:
    # Example: /xbrl/frames/US-GAAP/Revenues/USD/FY2023
    path = f"/xbrl/frames/{taxonomy}/{tag}/{unit}/{period}"
    return f"{SEC_BASE}{path}"


@dataclass(frozen=True)
class FactPoint:
    end: str  # period end date ISO
    val: float
    accn: Optional[str] = None
    fy: Optional[int] = None
    fp: Optional[str] = None  # Q1..Q4 or FY
    form: Optional[str] = None
    frame: Optional[str] = None


def extract_facts_companyfacts(payload: Dict[str, Any], taxonomy: str, tag: str, unit: str) -> List[FactPoint]:
    """Extract a series for a given taxonomy/tag/unit from companyfacts JSON.
    Returns newest-first list based on end date.
    """
    tx = payload.get("facts", {}).get(taxonomy, {})
    t = tx.get(tag)
    if not t:
        return []
    units = t.get("units", {})
    arr = units.get(unit, [])
    out: List[FactPoint] = []
    for item in arr:
        try:
            val = float(item["val"])  # ignore non-numeric
        except Exception:
            continue
        out.append(
            FactPoint(
                end=item.get("end") or item.get("filed", ""),
                val=val,
                accn=item.get("accn"),
                fy=item.get("fy"),
                fp=item.get("fp"),
                form=item.get("form"),
                frame=item.get("frame"),
            )
        )
    out.sort(key=lambda p: (p.end or ""), reverse=True)
    return out

