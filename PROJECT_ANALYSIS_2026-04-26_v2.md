# PROJECT ANALYSIS — 2026-04-26 (v2)

## Current Stage Summary

Project: CR Intelligence Platform  
Current stage: JSON-first architecture baseline implemented; pilot hardening and controlled backfill stage  
Timestamp: 2026-04-26 23:02:10 MSK

### Implementation status snapshot

- JSON-first raw artifact pipeline: implemented.
- Local-only UI download/preview for artifacts: implemented and verified.
- `/documents/{id}/content` now returns sections with fragments (additive contract): implemented.
- Traceability fields and migration `006_json_first_traceability`: implemented.
- Cleaned HTML derived artifact layer: implemented (v1 sanitizer + persistence path).
- OCR-first placeholder contract: implemented.
- Release gates:
  - `pilot_preflight`: pass
  - `release_ready_check`: pass
  - JSON-first targeted tests: pass

## Milestone map (updated)

### M0 — JSON-first foundation (DONE)

Completed:
1. Artifact abstraction module and mappings.
2. JSON artifact validation and reason codes.
3. JSON materialization from `source_payload_json` in fetch stage.
4. JSON-first normalize path with fallback chain (`json -> html -> pdf`).
5. Canonical JSON blocks + deterministic rules serialization.
6. Traceability schema/model updates.
7. UI/API contract alignment for non-empty content expanders.
8. Local-only guarantee tests.

### M1 — Traceability backfill and runtime consistency (IN PROGRESS)

Pending:
1. Backfill strategy for existing versions with legacy fragments referenced by evidence.
2. Safe renormalization policy (avoid FK conflicts with `pair_evidence.fragment_id`).
3. Incremental migration runbook for production-like datasets.

### M2 — OCR operationalization (PLANNED)

Pending:
1. OCR engine integration (configurable provider).
2. Confidence thresholds and degraded/skip policy.
3. Metrics for OCR coverage and quality.

### M3 — Pilot corpus execution (PLANNED)

Pending:
1. Full pilot rerun under JSON-first normalize.
2. Coverage and quality comparison against previous HTML/PDF-first baseline.
3. Operator sign-off on reviewed outputs.

## Risks and blockers

1. Existing fragment-evidence FK chains block naive renormalization for historical versions.
2. JSON artifact exists for current versions, but JSON-derived trace rows are not guaranteed for legacy normalized rows until controlled backfill is executed.
3. OCR currently contract-only; production extraction quality for image-heavy blocks remains limited.

## Updated priority order

1. Safe backfill/renormalize for traceability completeness.
2. Runtime metrics for JSON-first coverage and fallback rates.
3. OCR engine integration (phase-1 quality gate).
4. Pilot run and acceptance evidence refresh.
