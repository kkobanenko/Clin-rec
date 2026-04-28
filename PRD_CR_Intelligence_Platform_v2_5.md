# PRD v2.5 — CR Intelligence Platform

## 1. Product Purpose

CR Intelligence Platform is an internal evidence engineering system for reproducible local ingestion, normalization, extraction, scoring, and audit of clinical recommendation content.

## 2. Current Product Stage

```text
Validated JSON-first internal pilot build.
```

The previous product goal of validating the JSON-first runtime path has been met. The next product goal is to turn that validated baseline into an evidence-rich internal pilot workflow with stronger downstream operator trust.

## 3. Product Objective For v2.5

Build the next pilot tranche on top of the validated JSON-first baseline by improving downstream evidence richness, operator clarity, and release-governed pilot operations.

## 4. Users

### Operator

Reviews local raw artifacts, normalized content, evidence availability, diagnostics, and release evidence.

### Pharma Analyst

Inspects extracted clinical contexts, pair evidence, and downstream matrix readiness.

### Medical Expert

Reviews evidence-backed claims and highlights missing or insufficient evidence.

### Technical Administrator

Executes reruns, release checks, corpus diagnostics, and runtime evidence collection.

## 5. Updated Product Requirements

### FR-1. Stage Integrity

Stage claims must be tied to current-head runtime evidence and not only to unit or contract tests.

### FR-2. JSON-first Baseline Preservation

JSON remains the canonical source when valid; HTML/PDF remain fallback and presentation layers only.

### FR-3. Evidence Density Visibility

The system must expose whether current versions have non-empty downstream evidence, healthy empty-state, or degraded routing.

### FR-4. Operator Explanation Layer

The operator UI must clearly explain artifact source, traceability fields, and evidence empty-state semantics.

### FR-5. Release Evidence Completeness

Release evidence must include runtime artifact coverage, JSON-derived section/fragment counts, evidence endpoint behavior, and sample traceability chains.

### FR-6. Additive API Guarantees

All improvements must remain additive for `/documents`, `/matrix`, `/pipeline`, and `/outputs` APIs.

### FR-7. Pilot Operations Repeatability

The internal pilot workflow must be repeatable from documented commands and current-head release artifacts.

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

## 7. Acceptance Gate

`evidence-rich internal pilot operations build` is allowed only if:

1. current-head release-ready checks pass;
2. JSON-first runtime evidence is refreshed;
3. inspected versions expose rows or explicit empty-state reasons;
4. operator-facing workflow remains local-only and traceable;
5. stage claims are updated in project analysis and plan documents.

## 8. Out Of Scope For v2.5

1. Full production RBAC.
2. Multi-tenant deployment.
3. Advanced diagram understanding.
4. Non-deterministic clinical reasoning detached from traceability.