from dataclasses import dataclass
from typing import List, Optional, Tuple
import math
import re

# Minimal seed dataset; can be swapped for provider/cached store later.
@dataclass(frozen=True)
class Entity:
    name: str
    ticker: str
    exchange: str
    country: str
    cik: Optional[str] = None
    currency: Optional[str] = None


SEED_ENTITIES: Tuple[Entity, ...] = (
    Entity(name="Apple Inc.", ticker="AAPL", exchange="NASDAQ", country="US", cik="0000320193", currency="USD"),
    Entity(name="Alphabet Inc.", ticker="GOOGL", exchange="NASDAQ", country="US", cik="0001652044", currency="USD"),
    Entity(name="Microsoft Corporation", ticker="MSFT", exchange="NASDAQ", country="US", cik="0000789019", currency="USD"),
    Entity(name="Infosys Limited", ticker="INFY", exchange="NSE", country="IN", cik=None, currency="INR"),
)

ALIASES = {
    "google": "Alphabet Inc.",
    "alphabet": "Alphabet Inc.",
    "apple": "Apple Inc.",
    "microsoft": "Microsoft Corporation",
    "infosys": "Infosys Limited",
}


def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", s.lower())


def _lev(a: str, b: str) -> int:
    # Levenshtein distance (iterative DP) for fuzzy matching; small strings only
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        curr = [i]
        for j, cb in enumerate(b, 1):
            ins = curr[j - 1] + 1
            dele = prev[j] + 1
            sub = prev[j - 1] + (ca != cb)
            curr.append(min(ins, dele, sub))
        prev = curr
    return prev[-1]


@dataclass(frozen=True)
class Candidate:
    entity: Entity
    score: float  # higher is better
    reason: str


def resolve(name: str, limit: int = 5) -> List[Candidate]:
    """Resolve a free-text name to ranked candidates from SEED_ENTITIES.

    Ranking heuristic:
    - Exact ticker match (case-insensitive) => score 100
    - Alias/exact name match => score 95
    - Fuzzy name (normalized) via Levenshtein => score 90 - distance
    - Otherwise small bonus for substring containment
    Deterministic tie-break by (exchange, ticker).
    """
    q = name.strip()
    if not q:
        return []
    qn = _norm(q)

    ranked: List[Candidate] = []

    # 1) Exact ticker match
    for e in SEED_ENTITIES:
        if e.ticker.lower() == qn:
            ranked.append(Candidate(e, 100.0, "exact_ticker"))

    # 2) Alias / exact name match
    if qn in (_norm(k) for k in ALIASES.keys()):
        target = ALIASES[[k for k in ALIASES.keys() if _norm(k) == qn][0]]
        for e in SEED_ENTITIES:
            if e.name == target:
                ranked.append(Candidate(e, 95.0, "alias"))
    for e in SEED_ENTITIES:
        if _norm(e.name) == qn:
            ranked.append(Candidate(e, 95.0, "exact_name"))

    # 3) Fuzzy name
    for e in SEED_ENTITIES:
        dist = _lev(_norm(e.name), qn)
        score = 90.0 - dist
        if score >= 80:  # allow small typos
            ranked.append(Candidate(e, score, f"lev:{dist}"))

    # 4) Substring bonus
    for e in SEED_ENTITIES:
        if qn and _norm(e.ticker) in qn:
            ranked.append(Candidate(e, 82.0, "ticker_substr"))
        if qn in _norm(e.name):
            ranked.append(Candidate(e, 81.0, "name_substr"))

    # Deduplicate by entity with max score
    best: dict[Tuple[str, str], Candidate] = {}
    for c in ranked:
        key = (c.entity.exchange, c.entity.ticker)
        if key not in best or c.score > best[key].score:
            best[key] = c

    # Sort by score desc, then stable tiebreaker
    out = sorted(best.values(), key=lambda c: (-c.score, c.entity.exchange, c.entity.ticker))
    return out[:limit]

