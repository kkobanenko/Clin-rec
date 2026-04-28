# TZ v2.4 — Evidence-Rich JSON-first Pilot Operations

## 1. Goal Of This Tranche

Advance the validated JSON-first internal pilot build into an evidence-rich internal pilot operations build without breaking existing APIs or JSON-first locality guarantees.

## 2. Baseline Assumption

The following are already validated on current head:

1. JSON raw artifact persistence.
2. JSON-first normalize flow.
3. Derived blocks artifact generation.
4. Traceability propagation into sections and fragments.
5. Current-head release-ready pack.

## 3. Technical Objective

Make evidence availability operationally explainable and improve downstream usefulness of JSON-derived fragments for pilot inspection and release claims.

## 4. Work Packages

### WP-1. Evidence Density Diagnostics

Implement diagnostics that classify inspected current versions into:

1. evidence_rows_present;
2. healthy_empty_state;
3. degraded_routing;
4. extraction_missing;
5. scoring_missing.

Outputs:

1. release evidence counters;
2. API-visible reason fields where additive;
3. operator-readable explanations.

### WP-2. Operator Empty-State Hardening

Ensure UI and API contracts support the following:

1. local-only artifact preview/download;
2. explicit traceability fields in normalized content;
3. honest empty-state for evidence loading;
4. no fallback to external card/html/pdf URLs for current version review.

### WP-3. Fragment-to-Evidence Explainability

Add runtime observability explaining why JSON-derived fragments do or do not produce pair evidence.

Minimum dimensions:

1. document_version_id;
2. source_artifact_type;
3. content_kind;
4. candidate generation outcome;
5. evidence outcome state.

### WP-4. Release Evidence Hardening

Every release evidence document must include:

1. git head;
2. commands executed;
3. target test results;
4. artifact coverage by type;
5. JSON-derived sections count;
6. JSON-derived fragments count;
7. sample traceability chain;
8. evidence endpoint sample;
9. known limitations.

### WP-5. Pilot Rerun Operations

Support repeatable commands for:

1. current-version re-normalization;
2. release-ready verification;
3. pilot preflight;
4. SQL coverage checks;
5. evidence endpoint spot checks.

## 5. Technical Constraints

1. No breaking changes in `/documents`, `/matrix`, `/pipeline`, `/outputs`.
2. No replacement of JSON by HTML/PDF as primary source.
3. No external raw artifact fetch during current version preview/download/review.
4. Runtime validation is mandatory; unit tests alone are not sufficient.

## 6. Required Validation Pack

```bash
python -m py_compile app/services/fetch.py app/services/normalize.py app/api/documents.py app/ui/app.py app/services/json_blocks.py app/services/artifacts.py
python -m pytest -q \
  tests/test_artifact_validation.py \
  tests/test_artifacts.py \
  tests/test_json_blocks.py \
  tests/test_json_first_normalize.py \
  tests/test_documents_content_fragments_contract.py \
  tests/test_raw_artifact_json_ui.py \
  tests/test_traceability_contract.py \
  tests/test_local_only_guarantee.py \
  tests/test_normalize.py \
  tests/test_ui_app.py
bash scripts/pilot_preflight.sh
RUNTIME_PROFILE=pilot-compose-local bash scripts/release_ready_check.sh
```

## 7. Acceptance

This tranche is accepted if:

1. current-head release-ready pack passes;
2. runtime JSON-derived sections remain > 0;
3. runtime JSON-derived fragments remain > 0;
4. derived blocks artifacts remain downloadable;
5. evidence endpoint works for inspected current version;
6. evidence state is either non-empty or explicitly empty with no crash and no misleading claim.