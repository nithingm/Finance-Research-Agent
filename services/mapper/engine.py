from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Optional, Any
import json
from pathlib import Path


@dataclass(frozen=True)
class MappingRule:
    tag: str
    canonical: str
    sign: int = 1  # multiply value by sign before aggregation
    precedence: int = 0
    units: Optional[List[str]] = None


@dataclass
class Mapper:
    rules: List[MappingRule]
    aliases: Dict[str, str]

    @staticmethod
    def from_json_path(path: str | Path) -> "Mapper":
        data = json.loads(Path(path).read_text())
        rules = [
            MappingRule(
                tag=r["tag"],
                canonical=r["canonical"],
                sign=int(r.get("sign", 1)),
                precedence=int(r.get("precedence", 0)),
                units=r.get("units"),
            )
            for r in data.get("rules", [])
        ]
        # sort rules by precedence desc so higher precedence applied later (can overwrite)
        rules.sort(key=lambda r: r.precedence)
        return Mapper(rules=rules, aliases=data.get("aliases", {}))

    def resolve_alias(self, tag: str) -> str:
        return self.aliases.get(tag, tag)

    def map_period(self, facts_by_tag: Dict[str, float], unit: str = "USD") -> Dict[str, float]:
        """Map a dict of {tag: value} into canonical lines for a single period.
        - Applies aliases
        - Applies sign and precedence (later rules overwrite earlier for same canonical)
        - Only applies rules whose units include the provided unit if units are specified
        - Adds derived fields when possible (e.g., gross_profit = revenue - cogs)
        """
        # normalize keys via aliases
        norm = {self.resolve_alias(k): v for k, v in facts_by_tag.items()}

        out: Dict[str, float] = {}
        for rule in self.rules:
            if rule.units and unit not in (rule.units or []):
                continue
            if rule.tag in norm:
                out[rule.canonical] = rule.sign * float(norm[rule.tag])

        # Derived lines
        if "revenue" in out and "cogs" in out and "gross_profit" not in out:
            out["gross_profit"] = float(out["revenue"]) - float(out["cogs"])  # assume cogs is positive expense
        return out

