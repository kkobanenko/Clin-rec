# JSON-First Release Evidence (2026-04-26)

## Git head

- Head at evidence generation time: `23d02f0`

## Commands executed

1. Pre-check compile + baseline tests:
   - `/home/kobanenkokn/Clin-rec/.venv/bin/python -m py_compile app/services/fetch.py app/services/normalize.py app/api/documents.py app/ui/app.py`
   - `/home/kobanenkokn/Clin-rec/.venv/bin/pytest -q tests/test_artifact_validation.py tests/test_normalize.py tests/test_ui_app.py`
   - Result: `56 passed`

2. JSON-first focused suite:
   - `/home/kobanenkokn/Clin-rec/.venv/bin/pytest -q tests/test_artifacts.py tests/test_artifact_validation.py`
   - Result: `12 passed`

3. JSON blocks and serialization:
   - `/home/kobanenkokn/Clin-rec/.venv/bin/pytest -q tests/test_json_blocks.py tests/test_artifacts.py tests/test_artifact_validation.py`
   - Result: `16 passed`

4. JSON-first + UI/API contract + traceability + local-only:
   - `/home/kobanenkokn/Clin-rec/.venv/bin/python -m py_compile app/services/fetch.py app/services/normalize.py app/api/documents.py app/ui/app.py app/services/json_blocks.py app/services/cleaned_html.py app/services/ocr.py`
   - `/home/kobanenkokn/Clin-rec/.venv/bin/pytest -q tests/test_artifact_validation.py tests/test_json_blocks.py tests/test_json_first_normalize.py tests/test_documents_content_fragments_contract.py tests/test_raw_artifact_json_ui.py tests/test_traceability_contract.py tests/test_local_only_guarantee.py tests/test_normalize.py tests/test_ui_app.py`
   - Result: `72 passed`

5. Required v7 final compile/tests block:
   - `/home/kobanenkokn/Clin-rec/.venv/bin/python -m py_compile app/services/fetch.py app/services/normalize.py app/api/documents.py app/ui/app.py`
   - `/home/kobanenkokn/Clin-rec/.venv/bin/pytest -q tests/test_artifact_validation.py tests/test_json_blocks.py tests/test_json_first_normalize.py tests/test_documents_content_fragments_contract.py tests/test_raw_artifact_json_ui.py tests/test_traceability_contract.py`
   - Result: `20 passed`

6. Runtime/release checks:
   - `bash scripts/pilot_preflight.sh`
   - Result: PASS after migration
   - `RUNTIME_PROFILE=pilot-compose-local bash scripts/release_ready_check.sh`
   - Result: PASS
   - Artifacts dir: `.artifacts/release_checks/20260426_195008`

## Passed/failed summary

- Compile checks: PASSED
- Targeted JSON-first tests: PASSED
- Pilot preflight: PASSED
- Release-ready check pack: PASSED
- Initial blocker fixed during run:
  - Document outcomes API regression expected old `/documents/{id}/content` contract.
  - Adjusted tests for additive `sections[*].fragments` contract.

## Artifact coverage (current versions)

Collected via DB query over `source_artifact` joined with current `document_version`:

- `json`: 22
- `html`: 40
- `pdf`: 9

## JSON-derived sections/fragments counts

Collected via DB query over traceability fields:

- `document_section.source_artifact_type='json'`: 0
- `text_fragment.source_artifact_type='json'`: 0

Note:
- This runtime currently contains legacy normalized rows without JSON traceability.
- JSON-first generation contract is validated by unit tests in:
  - `tests/test_json_first_normalize.py`
  - `tests/test_traceability_contract.py`

## Sample traceability chain

Runtime chain from production DB with `json` traceability was not available at evidence capture time.
Contract chain validated by tests:

- DocumentVersion -> `raw_json` SourceArtifact
- `raw_json` -> Canonical JSON block (`source_block_id`, `source_path`)
- Canonical block -> `TextFragment` (`source_artifact_type='json'`, `source_block_id`)
- `TextFragment` -> `PairEvidence.fragment_id` (existing evidence linkage model)

Representative contract checks:

- `tests/test_traceability_contract.py::test_normalize_json_produces_source_block_traceability`
- `tests/test_traceability_contract.py::test_extract_sections_detailed_marks_json_source`

## Local-only guarantees

Validated by tests:

- `tests/test_local_only_guarantee.py::test_preview_download_use_local_backend_endpoint`
- `tests/test_local_only_guarantee.py::test_normalize_current_version_does_not_require_external_http`

Guarantee statement:

- Preview/Download in UI uses local backend endpoints.
- Normalize uses local storage (`download_artifact`) and does not fetch external web-service content during current-version processing.
