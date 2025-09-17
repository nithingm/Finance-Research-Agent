from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, Optional
from services.config.env import get_fx_config

"""
Free FX provider: exchangerate.host (no key required, fair-use).
We build URLs and parse a minimal response shape. Tests are offline.
"""


def build_fx_latest_url(base: str = "USD", symbols: Optional[str] = None) -> str:
    cfg = get_fx_config()
    url = f"{cfg.base_url}/latest?base={base}"
    if symbols:
        url += f"&symbols={symbols}"
    return url


@dataclass(frozen=True)
class FXQuote:
    base: str
    quote: str
    rate: float
    date: Optional[str] = None


def parse_fx_latest(payload: Dict[str, Any], quote: str) -> Optional[FXQuote]:
    try:
        base = payload.get("base")
        date = payload.get("date")
        rates = payload.get("rates", {})
        rate_val = float(rates[quote])
        return FXQuote(base=base, quote=quote, rate=rate_val, date=date)
    except Exception:
        return None

