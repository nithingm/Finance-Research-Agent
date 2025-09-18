from __future__ import annotations
from typing import Dict, Any, List


def assumptions_md(assumptions: Dict[str, Any], warnings: List[str] | None = None) -> str:
    lines = ["# Assumptions", ""]
    for k, v in assumptions.items():
        lines.append(f"- {k}: {v}")
    if warnings:
        lines.append("\n## Warnings")
        for w in warnings:
            lines.append(f"- {w}")
    return "\n".join(lines) + "\n"


def validation_report_md(checks: Dict[str, bool], details: Dict[str, Any] | None = None) -> str:
    lines = ["# Validation Report", ""]
    for k, ok in checks.items():
        lines.append(f"- {k}: {'PASS' if ok else 'FAIL'}")
    if details:
        lines.append("\n## Details")
        for k, v in details.items():
            lines.append(f"- {k}: {v}")
    return "\n".join(lines) + "\n"
