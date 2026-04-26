# Technical Specification — CR Intelligence Platform v2.3

Status: post-JSON-first hardening and pilot execution specification  
Date: 2026-04-26

## 1. Scope

Complete operationalization after JSON-first baseline:

1. Safe traceability backfill for legacy rows.
2. OCR phase-1 engine wiring.
3. JSON-first observability and release evidence automation.

## 2. Baseline delivered (input assumptions)

1. `fetch` persists `json` raw artifact from `source_payload_json`.
2. `normalize` uses source priority `json -> html_fallback -> pdf_fallback`.
3. `document_section` and `text_fragment` include traceability fields.
4. `/documents/{id}/content` returns sections with nested fragments.
5. UI supports JSON preview and local-only artifact download/preview flow.

## 3. Work package A — controlled backfill

### A.1 Safe candidate selection

Renormalize only versions that satisfy one of:

- no sections/fragments yet
- no evidence linked to existing fragments

### A.2 Protected versions

Versions with `pair_evidence.fragment_id` references are protected from destructive rewrite unless a dedicated remap strategy is applied.

### A.3 Backfill report

Produce report with:

- processed versions
- skipped protected versions
- success/failure reason codes
- traceability coverage before/after

## 4. Work package B — OCR phase-1

### B.1 Engine contract

Input: image bytes from image block references.  
Output: text, confidence, coordinates, engine, status, reason_code.

### B.2 Failure behavior

- OCR failures are degraded, non-fatal.
- Pipeline continues with image_ref placeholder fragment.

### B.3 Persistence

Optional derived `ocr_text` artifact and/or fragment tagged with `content_kind=ocr_text`.

## 5. Work package C — observability

Add metrics endpoints or structured logs for:

1. normalize_source_used counters
2. fallback reason_code counters
3. traceability completeness ratio
4. OCR execution outcomes

## 6. Work package D — release evidence

Generate evidence bundle containing:

1. git head
2. executed commands
3. test pass/fail
4. artifact type coverage
5. traceability sample chain
6. fallback/OCR summary

## 7. Validation commands

Required command pack:

```bash
python -m py_compile app/services/fetch.py app/services/normalize.py app/api/documents.py app/ui/app.py
pytest -q tests/test_artifact_validation.py tests/test_json_blocks.py tests/test_json_first_normalize.py tests/test_documents_content_fragments_contract.py tests/test_raw_artifact_json_ui.py tests/test_traceability_contract.py
bash scripts/pilot_preflight.sh
RUNTIME_PROFILE=pilot-compose-local bash scripts/release_ready_check.sh
```

## 8. Done criteria

1. Backfill runbook and report available.
2. OCR phase-1 integrated and tested in degraded-safe mode.
3. Observability counters exposed and validated.
4. Release evidence generated on current head.
5. No backward-incompatible API changes.
