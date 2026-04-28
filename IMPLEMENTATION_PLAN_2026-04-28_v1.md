# IMPLEMENTATION PLAN — 2026-04-28 (v1)

## Current Delivery Stage

```text
Validated JSON-first internal pilot build -> transitioning to evidence-rich internal pilot operations.
```

## Workstream A — Downstream Evidence Density

Goal: move inspected current versions from healthy empty-state evidence to meaningful evidence rows where extractable content exists.

Tasks:
1. Audit fragment coverage by content kind and document family.
2. Find current versions with valid JSON-derived fragments but zero pair evidence.
3. Improve extraction routing and candidate generation on JSON-derived fragments.
4. Add runtime diagnostics explaining why a version has zero evidence.
5. Extend release evidence with evidence-density counters.

Exit criteria:
1. inspected sample version either yields rows or yields explicit machine-readable reasons;
2. evidence endpoint remains stable;
3. UI presents rows or honest explanation consistently.

## Workstream B — Operator Workflow Closure

Goal: make operator validation around raw artifacts, content, and evidence operationally complete.

Tasks:
1. Expand RawSourceArtifacts guidance and error messages.
2. Add explicit empty-state language for evidence loading.
3. Add operator-facing diagnostics for source type, source block, and fallback reason.
4. Add manual smoke instructions tied to current-head evidence files.
5. Record sample operator validation paths in release artifacts.

Exit criteria:
1. operator can explain artifact source and evidence state without inspecting code;
2. UI/local API path is stable and documented.

## Workstream C — Corpus and Quality Governance

Goal: distinguish runtime health from corpus completeness and from evidence richness.

Tasks:
1. Add explicit corpus-quality counters to release evidence.
2. Separate content completeness, evidence richness, and scoring readiness metrics.
3. Publish residual limitations for zero-evidence current versions.
4. Add acceptance language for healthy empty-state vs insufficient evidence density.
5. Refresh project analysis and roadmap after each runtime tranche.

Exit criteria:
1. release summary cannot overstate quality;
2. all stage claims are evidence-bound.

## Workstream D — Pilot Operations Hardening

Goal: prepare repeatable internal pilot execution.

Tasks:
1. Stabilize runbook for re-normalization and release-ready reruns.
2. Keep backup/restore and locality guarantees visible.
3. Ensure release pack can be rerun on current head without ambiguity.
4. Publish pilot operations decision table.
5. Tie stage claims to current release artifacts directory.

Exit criteria:
1. validated rerun path is documented;
2. pilot operator has a deterministic execution sequence.

## Recommended Execution Order

1. Evidence density diagnostics.
2. Operator empty-state and traceability messaging.
3. Corpus-quality/release evidence hardening.
4. Pilot operations and rerun readiness.

## Current Definition Of Done For Next Tranche

1. At least one inspected current version has non-empty evidence rows, or zero rows are explained by explicit structured diagnostics.
2. Release evidence distinguishes runtime health from evidence density.
3. Operator workflow for local artifacts/content/evidence is documented and stable.
4. Current-head release pack remains green after updates.