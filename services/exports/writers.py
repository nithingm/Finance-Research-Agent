from __future__ import annotations
from typing import List, Dict, Any, Iterable
import csv
import io

# CSV schemas (abridged) aligned with PRD
SCHEMAS = {
    "income_statement": [
        "company_id","basis","currency","period_end","period_type","revenue","cogs","gross_profit","rnd","sma","gna","da","ebit","interest_net","pretax","tax","net_income","nci"
    ],
    "dcf": [
        "period_end","ebit","tax_rate","nopat","da","capex","delta_nwc","fcf","discount_factor","pv_fcf","terminal_value","pv_terminal","ev","net_cash","equity_value","shares","value_per_share"
    ],
    "metadata": [
        "run_id","company_key","basis","currency","fiscal_year_end","generated_at","mapper_version","taxonomy_version","code_sha"
    ],
}


def write_csv(rows: Iterable[Dict[str, Any]], columns: List[str]) -> str:
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=columns, extrasaction="ignore")
    w.writeheader()
    for r in rows:
        w.writerow({k: r.get(k) for k in columns})
    return buf.getvalue()


def write_income_statement(rows: Iterable[Dict[str, Any]]) -> str:
    return write_csv(rows, SCHEMAS["income_statement"])


def write_dcf(rows: Iterable[Dict[str, Any]]) -> str:
    return write_csv(rows, SCHEMAS["dcf"])


def write_metadata(rows: Iterable[Dict[str, Any]]) -> str:
    return write_csv(rows, SCHEMAS["metadata"])

