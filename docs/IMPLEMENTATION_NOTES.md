## 2026-04-25 — Milestone A canonical docs sync

Changed:
- Updated README to reference PRD v1.7, TZ v1.6, DOD_MVP_PILOT_v1 and pilot docs in docs/.
- Updated stage wording to `release-ready MVP -> pilot hardening`.
- Split backlog into release blockers / pilot blockers / post-MVP polish.
- Added docs-level canonical wrappers: ROADMAP_PILOT_HARDENING_v1.md, OPERATOR_RUNBOOK_PILOT_v1.md, DISCOVERY_COMPLETENESS_PLAN_v1.md.

Tests:
- command: grep checks on README/docs links (run below)
- result: pass (old PRD/TZ refs now limited to historical release summary records)

Release impact:
- doc-only

Residual risks:
- Milestone B+ (discovery completeness reporting, pilot preflight, governance hardening) not implemented yet.

## 2026-04-25 — Milestone B discovery completeness hardening (partial complete)

Changed:
- Added `CRIN_DISCOVERY_MODE` support via `settings.discovery_mode` (`smoke` default, `corpus` optional).
- Added structured `discovery_strategy_report` to `PipelineRun.stats_json` in discovery execution path.
- Added API attempt/status/fallback metadata flow in discovery strategy stats.
- Updated full-sync limit behavior: applies only for `discovery_mode=smoke`.
- Added smoke wording clarifications in `scripts/e2e_smoke.py` to separate smoke validation from completeness claims.
- Expanded discovery tests for strategy report fields, fallback status propagation, and smoke/corpus limit semantics.
- Fixed sqlite pytest harness for PostgreSQL `TSVECTOR` type compilation in tests.

Tests:
- command: `.venv/bin/pytest -q tests/test_discovery.py tests/test_source_validation.py tests/test_api_health.py`
- result: pass (`15 passed`)

Release impact:
- non-blocker hardening (runtime/reporting + tests), additive only

Residual risks:
- Full architect Milestone B not fully closed yet: still need richer `completeness_claim` semantics and broader release-summary integration wording.
- Milestone C+ (pilot runtime preflight, output governance, KB lint expansion, auth minimum) not implemented yet.
