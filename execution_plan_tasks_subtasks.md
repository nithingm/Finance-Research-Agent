# Execution Plan — Tasks & Subtasks for UI‑Enabled 3‑Statement Model Agent

> This is a detailed, phased breakdown to execute the project described in the PRD (single‑field UI → automated 3‑statement model + DCF + CSV outputs). Each phase lists tasks, subtasks, deliverables, and acceptance criteria. Use it as your project board (convert sections into tickets).

---

## Phase 0 — Program Setup & Governance

**Goals:** Create the repo, CI, environments, secrets handling, and working agreements.

- [ ] **0.1 Repository & Branching**
  - [ ] Create mono‑repo (e.g., `apps/ui`, `services/agent`, `services/ingestion`, `packages/core`).
  - [ ] Define branch strategy (e.g., `main` protected, `dev` integration, feature branches).
  - **Deliverable:** Repo scaffold with README and CODEOWNERS.
  - **Accept:** PRs require review; CI runs on PR.

- [ ] **0.2 Tooling & CI/CD**
  - [ ] Set up CI (lint, type‑check, tests, build).
  - [ ] Containerize services (Dockerfiles) and compose for local.
  - [ ] Basic CD to a staging env.
  - **Deliverable:** Passing CI badge; staging deploy job.
  - **Accept:** CI < 10 min; deploys reproducible.

- [ ] **0.3 Secrets & Config**
  - [ ] Add secrets manager (e.g., dotenv for local, cloud vault for staging/prod).
  - [ ] Define config schema (SEC UA header, API keys, rate limits).
  - **Deliverable:** `config.example.*`, vault policies.
  - **Accept:** Secrets not committed; config validated at boot.

- [ ] **0.4 Tracking & Project Board**
  - [ ] Create labels, templates, milestones matching phases.
  - **Deliverable:** Kanban board with Phase swimlanes.
  - **Accept:** Issues link back to this plan.

---

## Phase 1 — Entity Resolution (Name → Ticker/Exchange/CIK)

**Goals:** Given a free‑text company name, reliably resolve to the correct public entity.

- [ ] **1.1 Data Sources & Cache**
  - [ ] Choose provider(s) for name→symbol (exchange metadata, regulator queries, curated alias list).
  - [ ] Build local cache (nightly refresh) with keys: name, ticker, exchange, country, CIK, currency, fiscal YE.
  - **Deliverable:** `entity_store` with seed dataset and refresh job.
  - **Accept:** 95%+ resolution on a 500‑company test list.

- [ ] **1.2 Resolver Service**
  - [ ] Implement fuzzy search + ranking (exact symbol > exchange match > fuzzy name).
  - [ ] Expose API: `POST /resolve { company_name }` → candidates list.
  - **Deliverable:** Resolver microservice with tests.
  - **Accept:** P95 latency < 200 ms; deterministic ranking given same inputs.

- [ ] **1.3 Disambiguation UX hooks** (used later by UI)
  - [ ] Response format supports logos, region, exchange badge, confidence score.
  - **Deliverable:** JSON contract documented in OpenAPI.
  - **Accept:** UI can render top 5 candidates.

**Hint:** Keep a curated `aliases.json` for frequent edge cases (e.g., “Alphabet/Google”).

---

## Phase 2 — Filings & Market Data Ingestion

**Goals:** Fetch structured facts (XBRL) and market/FX; handle rate limits and retries.

- [ ] **2.1 SEC Client**
  - [ ] Implement **company‑facts** and **xbrl/frames** clients with proper User‑Agent + backoff.
  - [ ] Add `filings index` client to discover accessions and periods.
  - **Deliverable:** `sec_client` module with typed responses and fixtures.
  - **Accept:** Can pull 10Y annual + latest quarterlies for a test CIK without throttling errors.

- [ ] **2.2 Market & FX Client**
  - [ ] Select provider (e.g., Alpha Vantage or equivalent).
  - [ ] Implement endpoints for close price, shares outstanding, FX spot.
  - **Deliverable:** `market_client` module + rate‑limit guard.
  - **Accept:** 99th percentile accurate vs a benchmark for 20 symbols.

- [ ] **2.3 PDF Fallback (MVP‑lite)**
  - [ ] Parse key tables from PDF (Income, Balance, Cash Flow) when XBRL is missing.
  - **Deliverable:** `pdf_tables` extractor with confidence scores.
  - **Accept:** Extracts ≥ 70% of required lines on a 10‑file test set.

- [ ] **2.4 Ingestion Orchestrator**
  - [ ] Build job that given `{ticker|CIK}` fetches raw facts + metadata, writes to object store.
  - **Deliverable:** `ingest_job` with idempotency + resume.
  - **Accept:** Re‑run yields identical artifact hashes.

**Hint:** Stamp each request with a `run_id` and store raw payloads for audit.

---

## Phase 3 — Taxonomy‑Aware Mapping (US‑GAAP / IFRS → Canonical)

**Goals:** Normalize diverse tags into a stable, modeled schema.

- [ ] **3.1 Canonical Schema**
  - [ ] Finalize canonical line items (IS/BS/CF) including leases, NCI, other income.
  - **Deliverable:** `schema.yaml` + column dictionary for CSVs.
  - **Accept:** Reviewed by accounting SME; locked for MVP.

- [ ] **3.2 Mapping Rules**
  - [ ] Create GAAP and IFRS mapping tables (tag → canonical line, sign, precedence).
  - [ ] Handle common aliases and fallbacks; unit/scale normalization.
  - **Deliverable:** `mapping_gaap.json`, `mapping_ifrs.json` with tests.
  - **Accept:** ≥ 95% coverage of S&P1500 sample; conflicts logged.

- [ ] **3.3 Mapper Engine**
  - [ ] Implement rule application with precedence, aggregations, and sign handling.
  - [ ] Flag unmapped or imputed values for assumptions report.
  - **Deliverable:** `mapper` library with golden‑file tests.
  - **Accept:** Balance sheet balances on 30+ random issuers.

**Hint:** Keep mapping versioned; include taxonomy year in outputs.

---

## Phase 4 — Historical Model Assembly

**Goals:** Build clean time series (10Y annual + quarterlies), compute KPIs used by forecasting.

- [ ] **4.1 Period Stitching**
  - [ ] Align fiscal calendars; convert to report currency if requested.
  - [ ] Fill sparse quarters via interpolation or exclusions (flagged).
  - **Deliverable:** `historical_timeseries` with period_type (A/Q) and tidy rows.
  - **Accept:** No duplicate or overlapping periods; unit tests pass.

- [ ] **4.2 Derived Metrics**
  - [ ] Compute margins, turnover days (DSO/DPO/DIO), capex % revenue, cash conversion, ROE/ROIC.
  - **Deliverable:** `kpi` module with formulas documented.
  - **Accept:** KPIs match manual calc for 5 sample issuers within tolerance.

- [ ] **4.3 Segment Table (optional)**
  - [ ] Assemble segment revenues if disclosed; reconcile to total.
  - **Deliverable:** `segments.csv` when available.
  - **Accept:** Sum(segment) == consolidated ± rounding.

**Hint:** Treat working capital changes via days‑based approach for consistency across firms.

---

## Phase 5 — Forecasting Engine (12Q)

**Goals:** Project quarterly IS/BS/CF tied by accounting identities.

- [ ] **5.1 Assumptions Model**
  - [ ] Define assumption object per scenario (growth, margins, capex %, DSO/DPO/DIO, tax, SBC rule).
  - **Deliverable:** `assumptions.json` schema + validators.
  - **Accept:** Invalid combos (e.g., g ≥ WACC) rejected with clear error.

- [ ] **5.2 Revenue & Margin Stack**
  - [ ] Top‑down revenue by segment (fallback to consolidated if missing).
  - [ ] Model COGS & Opex to target operating margin bands.
  - **Deliverable:** Forecasted IS with quarterly granularity.
  - **Accept:** Annualized margins track guidance within user‑set bands.

- [ ] **5.3 Working Capital**
  - [ ] AR/AP/Inventory via days; compute ΔNWC by quarter.
  - **Deliverable:** WC schedule linked to CFO.
  - **Accept:** CFO reflects WC movements; identities hold.

- [ ] **5.4 Capex, PPE, D&A**
  - [ ] Capex as % of revenue; PPE roll‑forward; depreciation policy.
  - **Deliverable:** PPE & D&A schedules; IS/CF links.
  - **Accept:** Depreciation matches schedule; PPE balances.

- [ ] **5.5 Other Items**
  - [ ] Interest income/expense from net cash/debt; taxes; SBC.
  - **Deliverable:** Full projected IS/BS/CF per quarter (Base/Bull/Bear).
  - **Accept:** `BS == L+E` to tolerance; `CFO+CFI+CFF=ΔCash`.

**Hint:** Build forecasts as pure functions of assumptions + history to keep re‑runs deterministic.

---

## Phase 6 — Valuation (FCFF DCF + Sensitivities)

**Goals:** Compute EV → equity → per‑share with transparent inputs.

- [ ] **6.1 FCFF**
  - [ ] NOPAT, +D&A, −Capex, −ΔNWC from projections.
  - **Deliverable:** `dcf.csv` base columns ready.
  - **Accept:** Matches derived from cash flow statement.

- [ ] **6.2 WACC & Terminal**
  - [ ] Compute WACC from rf, ERP, beta, tax; guardrails on inputs.
  - [ ] Terminal value via Gordon growth (check `g < WACC`).
  - **Deliverable:** PV factors, PV of FCFs, PV of terminal; EV.
  - **Accept:** Unit tests on classic examples; sensitivity grid produced.

- [ ] **6.3 Equity Bridge**
  - [ ] EV + net cash − minority interests + investments → equity; per‑share.
  - **Deliverable:** Summary card data for UI.
  - **Accept:** Cross‑checked with sample hand calc.

**Hint:** Keep a `sensitivity(WACC, g)` matrix for quick UI heatmap.

---

## Phase 7 — Exports, Assumptions & Validation Reports

**Goals:** Produce tidy CSVs and human‑readable reports with provenance.

- [ ] **7.1 CSV Writers**
  - [ ] Emit `income_statement.csv`, `balance_sheet.csv`, `cash_flow.csv`, `assumptions.csv`, `dcf.csv`, `metadata.csv`, `citations.csv`.
  - **Deliverable:** Writer library with schema checks.
  - **Accept:** Columns exactly match dictionary; parsers ingest back losslessly.

- [ ] **7.2 Assumptions & Validation**
  - [ ] Generate `assumptions.md` (plain English) + `validation_report.md` (tie‑outs, warnings).
  - **Deliverable:** Markdown reports with anchors for UI linking.
  - **Accept:** Warnings displayed when mapping coverage < 95% or identities fail.

- [ ] **7.3 Packaging**
  - [ ] Zip bundle; signed hash for reproducibility.
  - **Deliverable:** Downloadable artifact set per run.
  - **Accept:** Hash stable across identical re‑runs.

---

## Phase 8 — Backend API & Orchestration

**Goals:** Expose clean endpoints and job lifecycle with progress events.

- [ ] **8.1 API Gateway**
  - [ ] Endpoints: `POST /runs`, `GET /runs/{id}`, `WS /runs/{id}/events`.
  - **Deliverable:** OpenAPI spec + handlers + auth middleware.
  - **Accept:** Contract tests; 429s under flood.

- [ ] **8.2 Agent Orchestrator (OpenAI Agents SDK)**
  - [ ] Tools: filings, market/FX, mapper, forecaster, valuation, exporter, validator.
  - [ ] Deterministic step order; structured logs with stage names.
  - **Deliverable:** Orchestrator service.
  - **Accept:** Progress events: Resolve → Ingest → Map → Forecast → DCF → Export.

- [ ] **8.3 Job Queue & Storage**
  - [ ] Background workers; retries; exponential backoff; idempotency.
  - [ ] Object storage for artifacts; metadata DB for runs.
  - **Deliverable:** Queue + storage wiring.
  - **Accept:** Crash‑safe; jobs resume without data loss.

---

## Phase 9 — Web UI

**Goals:** Single‑field UX with disambiguation, progress, results, and downloads.

- [ ] **9.1 Shell & Routing**
  - [ ] React/Next shell; routes for home (search), run status, results.
  - **Deliverable:** App skeleton with layout and theme.
  - **Accept:** Lighthouse perf ≥ 90 on desktop.

- [ ] **9.2 Search & Disambiguation**
  - [ ] Autosuggest component calling resolver; modal for multiple matches.
  - **Deliverable:** Polished search UX.
  - **Accept:** Keyboard nav; screen‑reader labels; P95 < 200 ms.

- [ ] **9.3 Run Progress**
  - [ ] Timeline component via WebSocket events; logs panel on demand.
  - **Deliverable:** Live progress view.
  - **Accept:** No missed stages; reconnect logic works.

- [ ] **9.4 Results Dashboard**
  - [ ] IS/BS/CF tables (quarterly/annual toggle, column chooser, CSV download buttons).
  - [ ] DCF summary card + WACC×g heatmap.
  - [ ] Assumptions panel; validation banner; shareable permalink.
  - **Deliverable:** Results page.
  - **Accept:** Tables virtualized for large data; copy‑link works.

- [ ] **9.5 Advanced Panel (Optional)**
  - [ ] Driver overrides with sensible constraints; rerun button.
  - **Deliverable:** Drawer/modal with forms.
  - **Accept:** Input validation; changes reflected on rerun.

- [ ] **9.6 Downloads**
  - [ ] Trigger zip download; show artifact list with sizes and hashes.
  - **Deliverable:** Download manager.
  - **Accept:** Files verified after download.

---

## Phase 10 — Observability, QA & Test Suites

**Goals:** Ensure correctness, stability, and traceability.

- [ ] **10.1 Unit & Property Tests**
  - [ ] Mapper golden tests; accounting identities; DCF math; edge cases (negative working capital, lease treatment).
  - **Deliverable:** Test suite with coverage report.
  - **Accept:** Coverage ≥ 80%; mutation tests pass on core math.

- [ ] **10.2 Integration & Contract Tests**
  - [ ] API contracts; resolver + UI e2e; WebSocket events; CSV schema round‑trip.
  - **Deliverable:** E2E test plan + scripts.
  - **Accept:** Green runs on staging.

- [ ] **10.3 Observability**
  - [ ] Structured logs; traces per run; metrics (success rate, latency, mapping coverage).
  - **Deliverable:** Dashboards + alerts.
  - **Accept:** On‑call can triage from dashboards alone.

---

## Phase 11 — Security, Compliance & Legal

**Goals:** Protect data, respect provider and regulator requirements.

- [ ] **11.1 Access & Rate Policies**
  - [ ] Implement per‑IP and per‑user rate limits; CSRF; HTTPS only.
  - **Deliverable:** Security middleware.
  - **Accept:** Pen test basic checks pass.

- [ ] **11.2 Secrets & Keys**
  - [ ] Rotate keys; restrict scopes; audit logs.
  - **Deliverable:** Key rotation runbook.
  - **Accept:** Secrets leak scanner clean.

- [ ] **11.3 Legal**
  - [ ] Review data source ToS; add attributions; store UA header requirements.
  - **Deliverable:** Compliance page + README section.
  - **Accept:** No ToS conflicts identified.

---

## Phase 12 — Performance, Scale & Cost

**Goals:** Hit UX SLAs and keep costs predictable.

- [ ] **12.1 Caching & Batching**
  - [ ] Cache SEC and market responses; dedupe concurrent requests.
  - **Deliverable:** Cache layer with TTLs.
  - **Accept:** Cold vs warm run latency improvement > 3×.

- [ ] **12.2 Concurrency & Queue Tuning**
  - [ ] Worker pool sizing; backpressure; circuit breakers on upstream.
  - **Deliverable:** Tuning guide.
  - **Accept:** P95 end‑to‑end ≤ 120s at 50 concurrent runs.

- [ ] **12.3 Cost Guardrails**
  - [ ] Budget alerts; per‑run cost estimation; model/token usage caps.
  - **Deliverable:** Cost dashboard.
  - **Accept:** No surprise bills during load tests.

---

## Phase 13 — Documentation & Onboarding

**Goals:** Make the system easy to run, extend, and support.

- [ ] **13.1 Dev Docs**
  - [ ] Architecture diagram; module READMEs; local dev guide; troubleshooting.
  - **Deliverable:** `/docs` site.
  - **Accept:** New dev sets up in < 30 minutes (measured).

- [ ] **13.2 API & UI Docs**
  - [ ] OpenAPI; UI how‑to; glossary (GAAP/IFRS terms, KPIs).
  - **Deliverable:** Published docs + examples.
  - **Accept:** Usability review complete.

- [ ] **13.3 Runbooks**
  - [ ] On‑call SOP; incident response; rollback; data refresh cadence.
  - **Deliverable:** Runbook PDFs/MD.
  - **Accept:** Dry‑run drill completed.

---

## Phase 14 — Launch & Post‑Launch

**Goals:** Ship MVP, gather feedback, iterate.

- [ ] **14.1 Beta Launch**
  - [ ] Invite pilot users; collect feedback; prioritize fixes.
  - **Deliverable:** Beta report.
  - **Accept:** ≥ 10 full runs by external users; CSAT ≥ 4/5.

- [ ] **14.2 Public Launch**
  - [ ] Hardened infra; rate limits; docs polished; announce.
  - **Deliverable:** v1.0 tag; change log.
  - **Accept:** Error rate < 1% week‑1.

- [ ] **14.3 Iteration Backlog**
  - [ ] IFRS deepening; better PDF extraction; more data sources; peer‑based default drivers.
  - **Deliverable:** v1.5 roadmap.
  - **Accept:** Roadmap signed off.

---

## Cross‑Cutting Acceptance Gates (Definition of Done)

- **Accounting identities pass** for historical and forecasted periods.
- **Mapping coverage ≥ 95%** or clearly flagged with imputations.
- **Zero‑input flow** completes with only a company name for ≥ 95% of SEC names tested.
- **All artifacts** (CSVs, MD) downloadable and validated against schema.
- **Citations present** for every numeric historical fact.
- **Observability** shows stage timings and success/failure with Run IDs.

---

## Dependencies & Sequencing (at a glance)

1. Phase 0 → 1 → 2 → 3 must precede 4–6.
2. Phase 7 (exports) can develop in parallel with 5–6 once schemas are stable.
3. Phase 8 (API) unblocks 9 (UI); 9 depends on 1 (resolver) and 8 (events).
4. Phases 10–12 run alongside feature work after first end‑to‑end path exists.

---

## Nice‑to‑Haves (Backlog)
- Peer benchmarking to auto‑seed assumptions when history is thin.
- Multi‑currency views (functional vs USD with FX scenarios).
- Notebook export (Jupyter) of the model for power users.
- Scheduled runs & webhooks for automation.

---

## Quick Hints for Implementation (no full code)
- Keep **pure functions** for mapping, forecasting, and DCF; pass a single `Context` object.
- Store raw payloads + computed artifacts with a **content hash** for reproducibility.
- Use a **rule engine** (simple precedence table) for mapping before considering ML.
- Validate CSVs with a schema tool (e.g., JSON Schema) in CI.
- For UI tables, implement **virtual scrolling** to handle long quarter spans smoothly.

