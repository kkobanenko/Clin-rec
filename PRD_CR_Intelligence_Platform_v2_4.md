# PRD — CR Intelligence Platform v2.4

Document status: canonical draft for post-JSON-first pilot hardening  
Date: 2026-04-26  
Supersedes: PRD v2.3 in staging/roadmap sections.

## 1. Product Stage

Current product stage:

```text
JSON-first baseline delivered.
Platform moves to traceability backfill, OCR operationalization, and pilot rerun.
```

## 2. Product goal (unchanged)

Trusted, locally reproducible extraction and evidence pipeline for clinical recommendations with audit-grade provenance.

## 3. What is already delivered

1. JSON raw artifact is materialized and supported as canonical source for normalize.
2. HTML/PDF retained as fallback and operator presentation/download layers.
3. Additive content contract provides non-empty sections+fragments rendering path.
4. Local-only artifact actions preserved for UI review flow.
5. Traceability schema fields and migration are in place.

## 4. Next product requirements (v2.4)

### FR-4.1 Traceability completeness

For current pilot corpus:

- 100% sections/fragments generated under JSON-first pipeline must carry source artifact and block lineage.
- Any fallback-generated fragment must carry fallback source metadata.

### FR-4.2 Controlled backfill

Backfill/renormalization must not break existing evidence FK integrity.

### FR-4.3 OCR phase-1

Enable optional OCR execution for image blocks with confidence and degraded-safe behavior.

### FR-4.4 Runtime observability

Expose JSON-first operational metrics:

- JSON normalize success rate
- fallback rate (html/pdf)
- fragments with traceability coverage
- OCR attempted/succeeded/degraded

### FR-4.5 Pilot rerun readiness

Pilot rerun gate requires:

1. preflight green
2. release-ready pack green
3. JSON-first traceability report
4. operator UI smoke for documents/content/evidence paths

## 5. Non-functional constraints

1. Backward compatibility: existing APIs remain additive only.
2. Local-only UI review actions remain mandatory.
3. No external fetch during operator preview/download/evidence load.
4. Deterministic serialization for JSON block materialization and rules text.

## 6. Release acceptance (v2.4)

Build can be promoted only if all true:

1. JSON-first tests pass.
2. Preflight and release-ready checks pass.
3. Traceability completeness report is present.
4. Pilot corpus has no undocumented fallback anomalies.
5. OCR degraded cases are explicitly logged and non-fatal.
