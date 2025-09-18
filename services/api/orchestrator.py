from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional
import threading
import time
import uuid

from services.resolver.core import resolve as resolve_entity
from services.mapper.engine import Mapper
from services.historical.timeseries import stitch_periods, validate_accounting_identities
from services.historical.kpi import enrich_with_kpis
from services.forecasting.assumptions import Scenario, validate_scenario
from services.forecasting.engine import project_12q
from services.valuation.fcff import FCFFInputs, fcff
from services.valuation.wacc import WACCInputs, wacc
from services.valuation.terminal import TerminalInputs, gordon_pv
from services.valuation.discount import discount_factors
from services.exports.writers import write_dcf, write_income_statement, write_metadata
from services.exports.reports import assumptions_md, validation_report_md


@dataclass
class Run:
    id: str
    company_name: str
    status: str = "queued"  # queued|running|completed|failed
    events: List[Dict[str, Any]] = field(default_factory=list)
    summary: Dict[str, Any] = field(default_factory=dict)
    artifacts: Dict[str, str] = field(default_factory=dict)  # filename -> content
    error: Optional[str] = None


class RunRegistry:
    def __init__(self):
        self._runs: Dict[str, Run] = {}
        self._lock = threading.Lock()

    def create(self, company_name: str) -> Run:
        rid = f"r_{uuid.uuid4().hex[:8]}"
        run = Run(id=rid, company_name=company_name)
        with self._lock:
            self._runs[rid] = run
        return run

    def get(self, rid: str) -> Optional[Run]:
        with self._lock:
            return self._runs.get(rid)

    def update(self, rid: str, **kwargs):
        with self._lock:
            r = self._runs.get(rid)
            if not r:
                return
            for k, v in kwargs.items():
                setattr(r, k, v)


REGISTRY = RunRegistry()


def _event(run: Run, stage: str, message: str):
    run.events.append({"stage": stage, "message": message, "ts": time.time()})


def orchestrate(run: Run):
    try:
        run.status = "running"
        # Resolve
        _event(run, "Resolve", f"Resolving entity for '{run.company_name}'")
        cands = resolve_entity(run.company_name)
        if not cands:
            raise ValueError("No entity candidates found")
        entity = cands[0].entity

        # Ingestion (stub): create tiny facts and map
        _event(run, "Ingest", "Fetching & mapping facts (stub dataset)")
        mapper = Mapper.from_json_path("services/mapper/mapping_gaap.json")
        facts = {
            "RevenueFromContractWithCustomerExcludingAssessedTax": 1000.0,
            "CostOfRevenue": 400.0,
            "ResearchAndDevelopmentExpense": 50.0,
            "SellingGeneralAndAdministrativeExpense": 100.0,
            "OperatingIncomeLoss": 200.0,
            "DepreciationAndAmortization": 30.0,
        }
        mapped = mapper.map_period(facts, unit="USD")

        # Historical build
        _event(run, "Map", "Building historical series")
        annual = [{"period_end": "2023-12-31", "period_type": "A", **mapped, "ar": 100, "inventory": 80, "ap": 70}]
        quarterly = [{"period_end": "2023-09-30", "period_type": "Q", **mapped}]
        hist = stitch_periods(annual, quarterly)
        hist = enrich_with_kpis(hist)
        identities_ok = validate_accounting_identities(hist)

        # Forecast
        _event(run, "Forecast", "Projecting 12 quarters")
        scenario = Scenario(
            revenue_growth_qoq=0.02,
            target_gross_margin=0.6,
            target_operating_margin=0.2,
            dso=45, dio=60, dpo=50,
            capex_pct_revenue=0.05,
            da_pct_revenue=0.03,
            tax_rate=0.25,
        )
        validate_scenario(scenario)
        last_q = {**hist[-1]}
        fcast = project_12q(last_q, scenario)

        # Valuation (build dcf rows from forecast)
        _event(run, "DCF", "Computing FCFF and DCF")
        tax_rate = scenario.tax_rate
        fcfs: List[float] = []
        dcf_rows: List[Dict[str, Any]] = []
        for idx, r in enumerate(fcast, start=1):
            fi = FCFFInputs(ebit=r["ebit"], tax_rate=tax_rate, da=r["da"], capex=r["capex"], delta_nwc=r["delta_nwc"])
            f = fcff(fi)
            fcfs.append(f)
            dcf_rows.append({
                "period_end": f"T+{idx}",
                "ebit": r["ebit"],
                "tax_rate": tax_rate,
                "nopat": r["ebit"] * (1 - tax_rate),
                "da": r["da"],
                "capex": r["capex"],
                "delta_nwc": r["delta_nwc"],
                "fcf": f,
            })
        w = wacc(WACCInputs(rf=0.03, erp=0.05, beta=1.0, tax_rate=0.25, debt_ratio=0.2, equity_ratio=0.8, rd=0.05))
        dfs = discount_factors(w, len(fcfs))
        pv_fcfs = [f * df for f, df in zip(fcfs, dfs)]
        # Terminal at T+12 based on next period FCF with g
        g = 0.03
        last_fcf_next = fcfs[-1] * (1 + g)
        tv = gordon_pv(TerminalInputs(last_fcf=last_fcf_next, wacc=w, g=g))
        pv_tv = tv * dfs[-1]
        ev = sum(pv_fcfs) + pv_tv
        equity = ev  # net cash omitted in MVP

        # fill dcf rows last row with terminal/pv
        dcf_rows[-1].update({
            "discount_factor": dfs[-1],
            "pv_fcf": pv_fcfs[-1],
            "terminal_value": tv,
            "pv_terminal": pv_tv,
            "ev": ev,
            "net_cash": 0.0,
            "equity_value": equity,
            "shares": 1.0,
            "value_per_share": equity / 1.0,
        })

        # Exports
        _event(run, "Export", "Generating CSVs and reports")
        dcf_csv = write_dcf(dcf_rows)
        is_csv = write_income_statement([
            {
                "company_id": f"{entity.ticker}",
                "basis": "US-GAAP",
                "currency": entity.currency or "USD",
                "period_end": "T+1",
                "period_type": "Q",
                "revenue": fcast[0]["revenue"],
                "cogs": fcast[0]["cogs"],
                "gross_profit": fcast[0]["gross_profit"],
                "da": fcast[0]["da"],
                "ebit": fcast[0]["ebit"],
                "tax": fcast[0]["tax"],
                "net_income": fcast[0]["net_income"],
            }
        ])
        md_csv = write_metadata([
            {
                "run_id": run.id,
                "company_key": f"{entity.ticker}/{entity.exchange}",
                "basis": "US-GAAP",
                "currency": entity.currency or "USD",
                "fiscal_year_end": "12-31",
                "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "mapper_version": "0.1",
                "taxonomy_version": "2024.0",
                "code_sha": "dev",
            }
        ])
        assumptions = assumptions_md(asdict(scenario), warnings=["identities_ok" if identities_ok else "identity_failed"])
        validation = validation_report_md({
            "cash_flow_identity": validate_accounting_identities(fcast),
        })

        run.artifacts = {
            "dcf.csv": dcf_csv,
            "income_statement.csv": is_csv,
            "metadata.csv": md_csv,
            "assumptions.md": assumptions,
            "validation_report.md": validation,
        }
        run.summary = {
            "ev": ev,
            "equity_value": equity,
            "wacc": w,
            "g": g,
        }
        run.status = "completed"
        _event(run, "Done", "Run completed")
    except Exception as e:
        run.status = "failed"
        run.error = str(e)
        _event(run, "Error", str(e))


def start_run(company_name: str) -> str:
    run = REGISTRY.create(company_name)
    t = threading.Thread(target=orchestrate, args=(run,), daemon=True)
    t.start()
    return run.id

