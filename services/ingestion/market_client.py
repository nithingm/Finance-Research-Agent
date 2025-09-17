from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, Optional

"""
Free providers (no-key or free-tier):
- Stooq (no key): historical prices CSV; example URL builder included.
- Alpha Vantage (free key): JSON time series; we stub parser shape.

Tests are offline using tiny JSON/CSV fixtures.
"""

STOOQ_BASE = "https://stooq.com/q/d/l/"  # CSV endpoint


def build_stooq_daily_csv(symbol: str, exchange_hint: Optional[str] = None) -> str:
    # Stooq uses suffixes like AAPL.US, MSFT.US; NSE may vary. We accept a hint but don't validate.
    sym = symbol
    if exchange_hint and exchange_hint.upper() in {"US", "NASDAQ", "NYSE"} and "." not in sym:
        sym = f"{symbol}.US"
    return f"{STOOQ_BASE}?s={sym}&i=d"


@dataclass(frozen=True)
class PricePoint:
    date: str  # YYYY-MM-DD
    close: float


def parse_alpha_vantage_daily(payload: Dict[str, Any], symbol: str) -> Dict[str, PricePoint]:
    """Parse Alpha Vantage TIME_SERIES_DAILY or *_ADJUSTED payload into date->PricePoint.
    Accepts minimal shape used in tests; ignores missing/invalid rows.
    """
    ts = None
    for k in payload.keys():
        if "Time Series" in k:
            ts = payload[k]
            break
    out: Dict[str, PricePoint] = {}
    if not isinstance(ts, dict):
        return out
    for date, row in ts.items():
        try:
            close_str = row.get("4. close") or row.get("5. adjusted close")
            if close_str is None:
                continue
            close = float(close_str)
        except Exception:
            continue
        out[date] = PricePoint(date=date, close=close)
    return out

