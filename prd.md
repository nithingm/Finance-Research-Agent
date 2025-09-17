# PRD — Agent that Generates 3-Statement Financial Models (w/ DCF) for Any Company

## 1) Summary
Build an agent and **single-field UI** that, given only a **company name** (e.g., “Infosys”, “Apple”), will: **resolve the entity** (ticker/CIK/exchange, GAAP/IFRS, currency), **ingest filings & market data**, **map facts to a canonical schema**, **project quarterly financials for 3 years**, **compute a DCF**, and **return tidy CSVs** plus a human-readable assumptions/validation report. The system must be auditable (citations + data lineage), robust to ambiguous names, and compliant with regulator API rules.

**Zero‑input mode promise:** The default UI requires only a company name. All other settings have sensible defaults with an **Advanced** panel for overrides.

---

## 2) Goals / Non-Goals
**Goals**
- **One‑field UI:** Type a company name → get a complete model with **no additional inputs required**.
- Auto-build historical **IS/BS/CF** (10Y annual + as-available quarterlies), normalize to canonical schema (US‑GAAP or IFRS).
- Project **12 quarters** forward using configurable drivers (growth, margins, capex, DSO/DPO/DIO), with **Base/Bull/Bear** scenarios.
- Compute **FCFF‑based DCF** with explicit WACC inputs and terminal growth; output EV → equity → per‑share.
- Export **CSV artifacts** and a **markdown assumptions + validation** report; include **per‑fact citations** to sources/tags.
- Provide **UI + API + CLI**; orchestrate with **OpenAI Agents SDK** tools.

**Non-Goals (v1)**
- Specialized bank/insurance modeling (different statements).
- Equity research-style narrative or rating.
- Full PDF table extraction for every foreign regulator (PDF fallback is best‑effort).

---

## 3) Users & Use Cases
- **Analyst/PM:** Compare intrinsic values across tickers; tweak drivers; batch export models.
- **Founder/FP&A:** Quick bottoms-up with auditable assumptions.
- **Educator/Student:** Learn modeling mechanics with transparent ties to filings.

### 3.1 Primary UI Flow
1. User lands on app; sees a **single search box**: “Enter company name”.
2. User types a name → **entity resolution** (autosuggest + disambiguation if multiple matches: ticker, exchange, domicile, logo).
3. User clicks **Generate Model**.
4. App shows **run screen** with progress steps: Resolve → Ingest → Map → Forecast → DCF → Export.
5. On completion, show **Results Dashboard** with:
   - Preview tables (IS/BS/CF) with **quarterly/annual toggle**.
   - DCF summary (EV, equity, per‑share) + **WACC×g** sensitivity chart.
   - **Downloads**: CSV bundle (zip) + assumptions.md + validation_report.md.
   - **Advanced** accordion for overrides (optional): scenarios, currency, basis.
6. User can **adjust** drivers → **Re‑run** (delta computation) or **Save/Share** a permalink.

---

## 4) Inputs & Outputs

### 4.0 UI Input (one‑field mode)
- **Company name** (free text). System performs: name → (ticker, exchange, CIK), accounting basis, currency, fiscal calendar.
- Optional (Advanced): output currency, scaling, scenario presets, citation toggle.

### 4.1 Inputs (API request)

### 4.1 Inputs (API request)
- **Company key:** `{ticker, exchange}` (optional `{cik}` if SEC filer).
- **Accounting basis:** `US-GAAP` or `IFRS`; **reporting currency** + optional USD translation.
- **History horizon:** years (default 10) + quarterly backfill if available.
- **Projection horizon:** quarters (default 12).
- **Detail flags:** segments, geography, leases, SBC, minority interest.
- **Scenario set:** per-scenario {segment growth, margin, capex %, DSO/DPO/DIO, tax, WACC (rf, ERP, beta), terminal g}.
- **Data sources toggle:** SEC EDGAR XBRL, market/FX provider.
- **Output prefs:** currency, scaling (actual/thousands/millions), with_citations (bool).

### 4.2 Outputs (artifact list)
- **UI outputs**
  - Results dashboard with IS/BS/CF tables; quarterly/annual toggle; download buttons per artifact.
  - DCF summary card + sensitivity heatmap; assumptions panel; validation warnings banner.
  - **Shareable link** (permalink) and **Run ID**.
- **Files**
  - `income_statement.csv`, `balance_sheet.csv`, `cash_flow.csv`
  - `assumptions.csv`, `dcf.csv`, `citations.csv`, `validation_report.md`
  - `metadata.csv` (keys, basis, currency, fiscal calendar, generation time, model version)

---

## 5) Functional Requirements

### 5.0 UI & UX
- **Entity resolution**: autosuggest as user types; show ticker, exchange, country; support fuzzy matches; manual override to pick the right entity.
- **Disambiguation modal** when multiple entities match; remember last choice per user.
- **Run progress UI** with deterministic stages; expose logs on demand.
- **Results dashboard**: responsive tables; column chooser; CSV download buttons; copy‑link.
- **Advanced panel**: scenario presets (Base/Bull/Bear), driver sliders/inputs; currency switch; basis (GAAP/IFRS) if applicable.
- **Empty/error states**: helpful guidance, retry action, support link; gracefully degrade when filings/XBRL are missing.
- **Accessibility**: WCAG 2.1 AA; keyboard nav; ARIA labels; high‑contrast mode.

### 5.1 Ingestion
- Fetch **structured facts** via SEC EDGAR company‑facts / xbrl/frames for annual/quarterly series; store raw JSON + metadata (accession, period, units). Respect fair‑access limits and proper User‑Agent. Retry/backoff.
- Market/FX data: close price, share count, FX rates via provider.
- PDF fallback (when XBRL missing): extract key tables (best‑effort) for selected lines.

### 5.2 Normalization & Mapping
- Map US‑GAAP/IFRS tags to **canonical lines** (Revenue, COGS, SG&A, D&A, SBC, Interest, Taxes, NCI, PPE, ROU assets, Lease liabilities). Maintain **versioned mapping** aligned with current taxonomies; upgrade annually.
- Handle common aliases; normalize units/scales; optional currency translation.

### 5.3 Historical Model Build
- Assemble 10Y annual + latest available quarterlies for IS/BS/CF; compute derived KPIs (margins, turnover days, capex % revenue, cash conversion). Segment table if available.

### 5.4 Forecasting Engine
- Quarterly projections (12Q) using drivers: revenue by segment, margin stack, D&A, SBC, working capital via DSO/DPO/DIO, capex %, PPE roll, interest income/expense, taxes. Scenarios: Base/Bull/Bear.

### 5.5 Valuation
- Compute FCFF and DCF; WACC inputs; terminal growth (g < WACC); PVs; EV→equity→per‑share; **WACC×g** sensitivity.

### 5.6 Exports & Reporting
- Emit CSVs; generate assumptions.md and validation_report.md; include citations.csv with per‑fact provenance.

### 5.7 Notifications (optional)
- Email/webhook on run completion with link to results.

---

### 5.1 Ingestion
- Fetch **structured facts** via SEC EDGAR company-facts / xbrl/frames for annual/quarterly series; store raw JSON + metadata (accession, period, units). Respect **fair-access limit 10 req/s** and proper **User-Agent**. Retry/backoff.
- Market/FX data: close price, share count, FX rates via provider.
- PDF fallback (when XBRL missing): extract key tables (best-effort) for selected lines.

### 5.2 Normalization & Mapping
- Map US-GAAP/IFRS tags to **canonical lines** (e.g., Revenue, COGS, SG&A, D&A, SBC, Interest, Taxes, NCI, PPE, ROU assets, Lease liabilities). Maintain **versioned mapping** aligned with current GAAP and IFRS taxonomies; upgrade annually.
- Handle common **aliases** (e.g., `RevenueFromContractWithCustomer...` vs `Sales`).
- Units/scaling normalization; currency translation if requested.

### 5.3 Historical Model Build
- Assemble 10Y annual + latest available quarterlies for IS/BS/CF; compute **derived KPIs** (margins, turnover days, capex % revenue, cash conversion).
- Segment table if data available; reconcile totals.

### 5.4 Forecasting Engine
- Quarterly projections (12Q) using drivers:
  - Revenue by segment (growth %, optional seasonality).
  - COGS & Opex driven by margin stack; D&A tied to PPE roll-forward; SBC rule.
  - **Working capital** via DSO/DPO/DIO; link changes to CFO.
  - Capex % revenue; PPE roll; amort/intangibles if acquisitions.
  - Interest income/expense from net cash/debt; effective tax.
- Scenarios: Base/Bull/Bear driver sets.

### 5.5 Valuation
- Compute **FCFF** and **DCF**: WACC (rf + beta×ERP), terminal growth (g < WACC), present values, EV→equity→per-share; include **WACC×g** sensitivity grid.

### 5.6 Exports & Reporting
- Emit CSVs; generate **assumptions.md** (plain English listing of every driver & any imputations) and **validation_report.md** (tie-outs, warnings).
- Include **citations.csv** with per-fact provenance: SEC endpoint + taxonomy tag + period.

---

## 6) Non-Functional Requirements
- **Reliability:** deterministic mapping; idempotent runs given same data snapshot.
- **Performance:** single-company cold start < 60s on average SEC filers (excluding heavy PDF parsing).
- **Scalability:** batch mode (100+ tickers) with polite rate limiting + caching.
- **Observability:** structured logs (request IDs, endpoints, rate-limit sleeps), run manifest (versions: mapper, taxonomy, code SHA).
- **Security & Compliance:** comply with data-source TOS; store API keys securely; respect regulator rate limits.

---

## 7) Architecture

**Frontend (Web UI)**
- **Stack:** React/Next.js, TypeScript, Tailwind + shadcn/ui; charts via Recharts or equivalent.
- **Components:** Search box (entity resolver), disambiguation dialog, run-progress timeline, results tables, DCF card + sensitivity heatmap, downloads panel, advanced settings drawer.
- **State:** URL‑addressable **Run ID**; optimistic updates; error boundaries.

**Backend & Orchestration**
- **API Gateway** (REST + WebSocket for progress updates):
  - `POST /runs` (body: company name); returns Run ID.
  - `GET /runs/{id}` (status + artifacts + summary).
  - `WS /runs/{id}/events` (stage updates, logs, warnings).
- **Agent Service** (OpenAI Agents SDK): tools for filings, market/FX, mapper, forecaster, valuation, exporter, validator.
- **Ingestion Service**: SEC & market clients with caching and rate‑limit backoff.
- **Job Queue**: background workers (idempotent), retries, exponential backoff.
- **Storage**: object store for artifacts (CSV/MD/ZIP); metadata DB for runs and entity cache.
- **Caching**: company‑facts & frames responses; share price/FX snapshots.
- **Observability**: structured logs, traces, metrics; per‑run manifest (versions, parameters).

**Security**
- Input sanitization (search box), rate limiting, CSRF protection, HTTPS only, secrets in vault, audit logs.

---

## 8) Data Model (Canonical Lines, abridged)

**Income Statement:** Revenue; COGS; **Gross Profit**; R&D; S&M; G&A; SBC; **EBITDA**; D&A; **EBIT**; Interest (net); Other income; **Pre-tax**; Taxes; **Net income**; NCI.

**Balance Sheet:** Cash & equivalents; ST investments; AR; Inventory; Other CA; PPE gross/accum; ROU assets; Intangibles/Goodwill; Other NCA; **Total assets**; AP; ST debt; Lease liab (ST/LT); Deferred revenue; Other CL; LT debt; Other NCL; **Total liab**; Equity; **Total liab+equity**.

**Cash Flow (Indirect):** Net income; +D&A; +SBC; ΔAR/ΔInv/ΔAP/other WC; **CFO**; Capex; Acquisitions; **CFI**; Dividends; Buybacks; Debt issue/repay; **CFF**; **ΔCash** (CFO+CFI+CFF).

(Include IFRS/GAAP lease fields; IFRS 16/ASC 842 treatment).

---

## 9) CSV Schemas (excerpt)

**income_statement.csv**
- Columns: `company_id, basis, currency, period_end, period_type, revenue, cogs, gross_profit, rnd, sma, gna, sbc, ebitda, da, ebit, interest_net, other_income, pretax, tax, net_income, nci`

**dcf.csv**
- Columns: `period_end, ebit, tax_rate, nopat, da, capex, delta_nwc, fcf, discount_factor, pv_fcf, terminal_value, pv_terminal, ev, net_cash, equity_value, shares, value_per_share`

**citations.csv**
- Columns: `line_item, period_end, source, endpoint, taxonomy_tag, accession, unit, scale`

**metadata.csv**
- Columns: `run_id, company_key, basis, currency, fiscal_year_end, generated_at, mapper_version, taxonomy_version, code_sha`

---

## 10) Validation & Accounting Rules (must-pass)
- **Balance sheet balances:** `|Assets − (Liabilities + Equity)| < ε`.
- **Cash flow identity:** `CFO + CFI + CFF = ΔCash` (within rounding).
- **Period continuity:** roll‑forwards (Cash_t = Cash_{t-1} + ΔCash_t).
- **Mapping coverage:** ≥ 95% of required canonical lines mapped or imputed; else **warning**.
- **Units/currency:** all periods consistent; if translated, FX rate source logged.
- **Regulator compliance:** requests/sec within published limits; include User‑Agent.
- **UI checks:** page renders < 2s on 3G; keyboard nav works across all controls; downloads verified.

---

## 11) Assumptions & Defaults
- If segment history missing, default to top-line growth with **static mix** and flag in assumptions.
- If share count variants exist, prefer **diluted** for per-share; cite source.
- **WACC defaults**: rf from current curve; ERP from published datasets; beta from industry or trailing regression; all values **override-able** & cited.
- **Terminal g** default 2.5–3.0% (must be < WACC).

---

## 12) Edge Cases
- Restatements/reclassifications → detect via new accession; rebuild affected history.
- Multi-currency disclosures; ADR ratios; stock splits.
- Lease accounting differences (IFRS 16 vs ASC 842): separate ROU and lease liabilities; interest vs principal in CFF.

---

## 13) Risks & Mitigations
- **Taxonomy drift** (annual updates): pin mapping by taxonomy version; scheduled updates & snapshot tests.
- **API throttling/outage**: local cache; exponential backoff; resumable pipelines.
- **Parsing errors** (PDFs): conservative fallbacks; mark unmapped/imputed fields in assumptions.

---

## 14) Success Metrics (v1)
- **Zero‑input success:** ≥ 95% of runs complete with **only company name** entered (no manual overrides).
- **Coverage:** ≥ 90% of SEC S&P 1500 tickers produce full 10Y/quarterly models without manual intervention.
- **Accuracy:** key line tie‑outs within 0.5% vs reported totals; DCF recomputation deterministic.
- **Latency:** median end‑to‑end ≤ 60s; p95 ≤ 120s; first results paint ≤ 2s.
- **Auditability:** 100% of numeric facts have a `citations.csv` row.
- **UX:** CSAT ≥ 4.5/5 on disambiguation & downloads.

---

## 15) Phases & Milestones
**MVP (4–6 weeks)**
- UI (search → disambiguate → run → results); US‑GAAP SEC filers; EDGAR ingestion; canonical mapping (core lines); 10Y build; 12Q forecast; single‑scenario DCF; CSV exports; validation report; Agents SDK orchestration.

**v1**
- Scenarios (Base/Bull/Bear) in UI; segment support; citations.csv; WACC×g sensitivity chart; batch via CSV upload; FX translation; market data integration; shareable links.

**v1.5**
- IFRS mapping; leases detail; PDF fallback; scheduled taxonomy updates; notifications; role‑based access.

---

## 16) Open Questions
- Preferred name‑to‑entity data sources (priority order) and licensing.
- Default currency for UI (company functional vs USD) and when to auto‑translate.
- Should UI expose advanced drivers inline or in a separate modal?
- Retention policy for runs/artifacts; versioned permalinks.

---

## 17) References (key specs this PRD relies on)
- SEC EDGAR APIs (company‑facts, xbrl/frames; access rules).
- US‑GAAP & SEC Reporting taxonomies (latest).
- IFRS Accounting Taxonomy (latest).
- OpenAI Agents SDK (agents, tools, handoffs).
- Market/FX data provider (e.g., Alpha Vantage).
- Cost of Capital/DCF references (Damodaran et al.).

## 18) Appendix — API (UI‑centric)
**POST /runs**
```json
{ "company_name": "Infosys", "advanced": { "output_currency": "USD", "with_citations": true }}
```
**Response**
```json
{ "run_id": "r_123", "status": "queued" }
```
**GET /runs/{id}** → status, summary, artifacts
**WS /runs/{id}/events** → stage updates, logs

## 19) Appendix — Entity Resolution
- Sources: ticker/exchange tables, regulator name search, curated alias list.
- Ranking: exact symbol match > exchange/domestic match > fuzzy name score.
- UI: show top 5 with logo, exchange, country; allow manual override.

