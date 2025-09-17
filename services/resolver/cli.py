import json
import sys
from .core import resolve


def main():
    if len(sys.argv) < 2:
        print("Usage: python -m services.resolver.cli <company name>")
        sys.exit(2)
    name = " ".join(sys.argv[1:])
    cands = resolve(name)
    print(json.dumps([
        {
            "name": c.entity.name,
            "ticker": c.entity.ticker,
            "exchange": c.entity.exchange,
            "country": c.entity.country,
            "cik": c.entity.cik,
            "currency": c.entity.currency,
            "score": round(c.score, 2),
            "reason": c.reason,
        }
        for c in cands
    ], indent=2))


if __name__ == "__main__":
    main()

