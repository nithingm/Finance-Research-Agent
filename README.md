# Finance Research Agent — 3-Statement Model + DCF (MVP scaffold)

This repository implements the first steps of the PRD and Execution Plan:
- Phase 0: Repo scaffold, CI, docs.
- Phase 1 (partial): A testable, deterministic Entity Resolver (name → ticker/exchange/CIK) using only Python stdlib.
- Phase 2 (partial): Offline SEC, Market, and FX URL builders and parsers with unit tests.

What’s here now
- Two source docs: `prd.md`, `execution_plan_tasks_subtasks.md` (authoritative requirements).
- Python entity resolver module with unit tests.
- Ingestion clients: SEC (company-facts/frames parsing), Market (Stooq URL; Alpha Vantage parser), FX (exchangerate.host URL/parse).
- Minimal docs and a CI workflow (Python tests).

Local quickstart (no installs)
- Run tests: `python -m unittest -v`
- Try the resolver CLI:
  - `python -m services.resolver.cli "Apple"`
  - `python -m services.resolver.cli "Gooogle"` (intentional misspelling → Alphabet)

Configuration
- Create a `.env` (optional) or set env vars in your shell:
  - `SEC_USER_AGENT` — e.g., `FinanceResearchAgent/0.1 (your-email@example.com)`
  - `ALPHAVANTAGE_API_KEY` — optional; tests do not require live calls.

Planned next (per execution plan)
- Phase 2–3 scaffolds for SEC ingestion + mapping (std‑lib first, then providers behind feature flags).
- Backend API (POST /runs) once core pipeline stubs are in place.
- UI scaffold (Next.js) after we get permission to run a package manager.

Contributing & workflow
- Keep core math/mapping/forecasting as pure functions with clear inputs/outputs.
- Every step must be testable. Add unit tests for new modules. CI must stay green.

License
- TBC.

