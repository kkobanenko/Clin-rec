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
