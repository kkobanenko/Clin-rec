# Technical Specification — CR Intelligence Platform v2.4

Status: active technical execution spec for pilot hardening tranche  
Date: 2026-04-26

## 1. Scope

Implement execution-phase hardening tasks after rollback baseline fa7c90e:

1. Traceability closure.
2. Controlled backfill safety.
3. OCR phase-1 operationalization.
4. Corpus validation evidence.
5. Current-head release evidence renewal.

## 2. Technical Work Packages

### WP-A Traceability Closure

Requirements:
1. Standardize source path schemas for sections/fragments.
2. Ensure artifact-type lineage is present on normalized outputs.
3. Add deterministic chain IDs for audit comparisons.
4. Publish traceability counters in run diagnostics.

Validation:
- targeted tests for lineage fields and chain rendering.

### WP-B Controlled Backfill

Requirements:
1. Classify document versions into safe/protected sets.
2. Skip protected versions by default.
3. Emit structured skip reasons.
4. Emit before/after coverage reports.

Validation:
- no FK breakage in evidence tables.

### WP-C OCR Phase-1

Requirements:
1. OCR result contract with status and confidence.
2. Degraded-safe fallback when OCR unavailable.
3. Optional derived artifact/fragment persistence.
4. UI visibility of OCR status.

Validation:
- tests for available/unavailable OCR paths.

### WP-D Corpus Validation

Requirements:
1. Run corpus mode separately from smoke mode.
2. Report discovered count, expected baseline, and variance.
3. Attach fallback and failure reasons.
4. Update decision language based on claim level.

Validation:
- corpus validation report generated for current head.

### WP-E Release Evidence Renewal

Requirements:
1. Run pilot preflight.
2. Run release-ready pack.
3. Capture artifact paths and run IDs.
4. Publish summary tied to exact current SHA.

Validation:
- summary SHA equals git HEAD SHA.

## 3. Required Commands

```bash
bash scripts/pilot_preflight.sh
RUNTIME_PROFILE=pilot-compose-local bash scripts/release_ready_check.sh
```

Targeted pack for execution tranche:

```bash
pytest -q tests/test_artifact_validation.py
pytest -q tests/test_json_blocks.py
pytest -q tests/test_json_first_normalize.py
pytest -q tests/test_traceability_contract.py
```

## 4. Done Criteria

1. All work packages produce machine-verifiable evidence files.
2. No destructive schema rewrites outside declared migrations.
3. No stage claim beyond attached evidence.
4. Final release summary references current head exactly.
