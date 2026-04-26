# ROADMAP_PILOT_TO_PRODUCTION_v7

Date: 2026-04-26

## Current Stage

```text
Pilot hardening execution stage after rollback baseline fa7c90e.
```

## Milestone M1 — Traceability Closure

Goal: guarantee stable source lineage from artifact to fragment/evidence.

Tasks:
1. Normalize source-path conventions for JSON/HTML/PDF paths.
2. Align section and fragment provenance semantics.
3. Add deterministic identifiers for trace chains.
4. Add coverage counters for traced vs untraced fragments.
5. Extend diagnostics to expose uncovered chains.

Exit:
- traceability coverage >= 95% on pilot corpus.

## Milestone M2 — Backfill and Legacy Safety

Goal: run controlled backfill without breaking FK integrity.

Tasks:
1. Define protected version set.
2. Define safe reprocess set.
3. Add skip/remap policy for linked evidence.
4. Generate before/after backfill reports.
5. Store operator-facing remediation notes.

Exit:
- no broken evidence links after backfill.

## Milestone M3 — OCR Phase-1

Goal: operational OCR placeholders with degraded-safe behavior.

Tasks:
1. Add OCR execution contract and status states.
2. Add confidence/engine metadata.
3. Add non-fatal degraded path handling.
4. Add UI surfacing for OCR-derived fragments.
5. Add test and metrics hooks.

Exit:
- OCR failures no longer block pipeline.

## Milestone M4 — Corpus Validation

Goal: separate smoke reliability from corpus completeness claims.

Tasks:
1. Run corpus-mode discovery.
2. Compare expected vs discovered counts.
3. Publish completeness report with limitations.
4. Record fallback reasons and known gaps.
5. Update release decision language.

Exit:
- completeness claim explicitly justified.

## Milestone M5 — Pilot Release Evidence Renewal

Goal: lock release evidence on current head.

Tasks:
1. Run preflight.
2. Run full release-ready pack.
3. Capture evidence paths and run IDs.
4. Publish release summary with current SHA.
5. Publish residual risk matrix.

Exit:
- validated internal pilot build decision possible.
