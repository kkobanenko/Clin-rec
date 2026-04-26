# PRD — CR Intelligence Platform v2.5

Status: active product contract for pilot hardening execution  
Date: 2026-04-26  
Supersedes: v2.4 for execution priorities and acceptance wording.

## 1. Product Stage

```text
Pilot hardening execution stage.
```

## 2. Product Objective

Deliver a reproducible and auditable clinical recommendation intelligence platform where every critical output can be traced to locally stored source artifacts and deterministic normalization flows.

## 3. Delivered Baseline

1. Runtime stack (API, worker, DB, storage, UI).
2. Document ingestion and artifact lifecycle surfaces.
3. Evidence/matrix/output pipelines in MVP-ready shape.
4. Pilot operations scripts and verification entrypoints.
5. JSON-first strategic direction and foundational implementation package.

## 4. Execution Objectives for v2.5

### FR-1 Stage Integrity

The project must publish stage claims only from current-head evidence.

### FR-2 Traceability Completeness

The platform must expose measurable traceability coverage for sections, fragments, and evidence chains.

### FR-3 Controlled Backfill

Legacy data remediation must preserve evidence linkage and provide explicit skip/remap reporting.

### FR-4 OCR Operational Readiness

Image-driven fragments must use a degraded-safe OCR contract with explicit status/counter visibility.

### FR-5 Corpus Completeness Governance

Corpus completeness must be reported separately from smoke and cannot be inferred from smoke runs.

### FR-6 Operator Transparency

Operator surfaces must show clear diagnostics for missing lineage, fallback usage, and unresolved quality gaps.

## 5. Non-Functional Requirements

1. Backward compatibility: additive changes only unless migration explicitly approved.
2. Auditability: deterministic IDs and path conventions.
3. Locality: operator review actions remain local-storage based.
4. Reliability: failed optional stages must degrade safely.
5. Reproducibility: same input yields same block/fragment mapping.

## 6. Success Metrics

1. Traceability coverage ratio by run.
2. Protected backfill skip ratio and reason breakdown.
3. OCR attempted/succeeded/degraded counters.
4. Corpus mode discovered vs expected ratio.
5. Release evidence completeness on current head.

## 7. Acceptance Gate

Promotion to validated internal pilot build requires:

1. Preflight pass.
2. Full release-ready pass.
3. Current-head release evidence summary.
4. Traceability report attached.
5. Backfill safety report attached.
6. Corpus completeness statement attached.
