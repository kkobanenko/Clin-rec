# PRD v2.6 — CR Intelligence Platform

## 1. Product Purpose

CR Intelligence Platform is an internal evidence engineering system for reproducible local ingestion, normalization, extraction, scoring, and audit of clinical recommendation content.

## 2. Current Product Stage

```text
Evidence-rich internal pilot operations in progress.
```

The v2.5 objective (evidence density diagnostics, operator panel, release evidence API) has been delivered. The current tranche extends that baseline with candidate diagnostics, corpus quality monitoring, and content-kind-aware scoring.

## 3. Product Objective For v2.6

Extend the evidence-rich pilot with:

1. **Candidate-level diagnostics** — per-fragment candidate generation reasons visible to operators and in pipeline telemetry.
2. **Corpus quality monitoring** — a single `/outputs/corpus-quality` endpoint giving content-kind breakdown, evidence richness, scoring coverage, and quality flags.
3. **Content-kind-aware scoring** — scoring engine multiplies image-derived evidence scores by 0.0, table/unknown by reduced factors.
4. **Per-version incremental scoring** — `score_version()` called alongside `score_all()` in the extract task, reducing redundant full-corpus re-scores.

## 4. Users

### Operator

Reviews local raw artifacts, normalized content, evidence availability, diagnostics, candidate reasons, and corpus quality flags.

### Pharma Analyst

Inspects extracted clinical contexts, pair evidence, scoring coverage, and matrix readiness. Uses candidate diagnostics to identify low-coverage document versions.

### Medical Expert

Reviews evidence-backed claims, highlights insufficient evidence, and uses corpus quality health to assess release readiness.

### Technical Administrator

Executes reruns, release checks, corpus diagnostics, and runtime evidence collection. Monitors `skip_rate` and `fragments_no_mnn` from candidate diagnostics.

## 5. Updated Product Requirements

### FR-1. Stage Integrity

Stage claims must be tied to current-head runtime evidence and not only to unit or contract tests.

### FR-2. JSON-first Baseline Preservation

JSON remains the canonical source when valid; HTML/PDF remain fallback and presentation layers only.

### FR-3. Evidence Density Visibility

The system must expose whether current versions have non-empty downstream evidence, healthy empty-state, or degraded routing.

### FR-4. Operator Explanation Layer

The operator UI must clearly explain artifact source, traceability fields, evidence empty-state semantics, and candidate generation reasons.

### FR-5. Release Evidence Completeness

Release evidence must include runtime artifact coverage, JSON-derived section/fragment counts, evidence endpoint behavior, and sample traceability chains.

### FR-6. Additive API Guarantees

All improvements must remain additive for `/documents`, `/matrix`, `/pipeline`, and `/outputs` APIs.

### FR-7. Pilot Operations Repeatability

The internal pilot workflow must be repeatable from documented commands and current-head release artifacts.

### FR-8 *(NEW)*. Candidate Diagnostics Telemetry

The extract pipeline must log per-version candidate generation diagnostics, including `skip_rate`, `fragments_no_mnn`, `fragments_single_mnn`, `fragments_image`, `total_new_pairs`, and `total_skipped_pairs`.

### FR-9 *(NEW)*. Corpus Quality Monitoring

The system must expose a `/outputs/corpus-quality` endpoint returning:

- content_kind breakdown;
- evidence richness (fragments with evidence, fragments scored);
- quality flags with severity, metric, value, threshold, message;
- overall health: healthy / degraded / critical / empty.

### FR-10 *(NEW)*. Content-Kind-Aware Scoring

Scoring must apply content-kind multipliers: `{text:1.0, html:1.0, table_like:0.9, unknown:0.8, image:0.0}`. Image fragments must not contribute positive evidence scores.

## 6. Success Metrics

| Metric | Target |
|---|---:|
| Current versions with JSON artifact where source payload exists | 100% |
| JSON-derived sections | > 0 and runtime-verified |
| JSON-derived fragments | > 0 and runtime-verified |
| Derived blocks artifacts | > 0 and downloadable |
| Evidence endpoint health for inspected version | 100% |
| Inspected versions with explicit evidence state explanation | 100% |
| Current-head release-ready pack | Passed |
| `/outputs/corpus-quality` returns valid JSON with `overall_health` | 100% |
| Candidate diagnostics logged for each extract task invocation | 100% |
| Image-derived evidence scores | 0.0 |

## 7. Acceptance Gate

`evidence-rich internal pilot operations build` is allowed only if:

1. current-head release-ready checks pass;
2. JSON-first runtime evidence is refreshed;
3. inspected versions expose rows or explicit empty-state reasons;
4. operator-facing workflow remains local-only and traceable;
5. stage claims are updated in project analysis and plan documents;
6. corpus-quality endpoint responds with valid JSON *(NEW)*;
7. candidate diagnostics are present in pipeline event log detail_json *(NEW)*;
8. no image fragment contributes a positive score *(NEW)*.

## 8. Out Of Scope For v2.6

1. Full production RBAC.
2. Multi-tenant deployment.
3. Advanced diagram understanding.
4. Automated alert delivery for quality flag thresholds.
