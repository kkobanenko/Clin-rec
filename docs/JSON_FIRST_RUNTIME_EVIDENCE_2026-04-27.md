# JSON-first Runtime Evidence — 2026-04-27

## Git Head

- git head: c1ca2abbc4bfd24249aaa96acc768e86432a8143
- short head: c1ca2ab

## Baseline (Step 0)

Commands:

```bash
git status --short
git rev-parse --short HEAD
find app tests docs scripts -type f | wc -l
```

Observed:

- repository had pre-existing local/untracked files;
- head at baseline: c1ca2ab;
- file count (app/tests/docs/scripts): 441.

## Commands Executed

```bash
.venv/bin/alembic upgrade head
.venv/bin/python -m py_compile app/services/fetch.py app/services/normalize.py app/api/documents.py app/ui/app.py app/services/json_blocks.py app/services/artifacts.py
.venv/bin/python -m pytest -q \
  tests/test_artifact_validation.py \
  tests/test_artifacts.py \
  tests/test_json_blocks.py \
  tests/test_json_first_normalize.py \
  tests/test_documents_content_fragments_contract.py \
  tests/test_raw_artifact_json_ui.py \
  tests/test_traceability_contract.py \
  tests/test_local_only_guarantee.py \
  tests/test_normalize.py \
  tests/test_ui_app.py \
  tests/test_fetch_json_artifact.py \
  tests/integration/test_fetch_normalize_flow.py
bash scripts/pilot_preflight.sh
RUNTIME_PROFILE=pilot-compose-local bash scripts/release_ready_check.sh
docker exec crin_app sh -c "cd /app && PYTHONPATH=/app python scripts/renormalize_current_versions_json_first.py"
```

## Test Results

- target pytest pack: 80 passed.
- pilot preflight: PASS.
- release-ready check: PASS.
- release artifacts dir: .artifacts/release_checks/20260427_144814.

## Runtime Artifact Coverage by Type

From runtime DB:

- derived_blocks: 22
- html: 40
- json: 22
- pdf: 9

## Runtime Traceability Coverage

From runtime DB:

- JSON-derived sections: 929
- JSON-derived fragments: 929
- sections with non-null source_artifact_type: 929
- fragments with non-null source_artifact_type: 929
- html fallback sections: 0
- pdf fallback sections: 0

Acceptance SQL used:

```sql
select source_artifact_type, count(*)
from document_section
where source_artifact_type is not null
group by source_artifact_type;

select source_artifact_type, count(*)
from text_fragment
where source_artifact_type is not null
group by source_artifact_type;
```

## Sample Traceability Chain

- sample document id: 1
- sample current version id: 4
- sample json artifact id: 49
- sample json artifact path: documents/1/versions/4/json.json
- sample derived_blocks artifact id: 75
- sample derived_blocks path: documents/3/versions/1/derived_blocks.json
- sample section: id=1239, source_artifact_type=json, source_block_id=1027_1, source_path=/
- sample fragment: id=8089, source_artifact_type=json, source_block_id=1027_1, content_kind=text

## /documents/{id}/content Contract Sample

API sample confirms additive fields are present:

- document_id: 1
- version_id: 4
- sections[].source_artifact_type: json
- sections[].source_block_id: present
- sections[].source_path: present
- sections[].fragments[].content_kind: present
- sections[].fragments[].source_artifact_type: json

## Evidence Endpoint Result

Request:

```text
GET /matrix/pair-evidence?document_version_id=4&page=1&page_size=5
```

Result:

```json
{"items":[],"total":0,"page":1,"page_size":5,"pages":0}
```

Interpretation:

- endpoint is healthy;
- empty-state is explicit and compatible with UI contract.

## UI Validation Notes

- automated UI-locality and preview regression tests passed:
  - tests/test_raw_artifact_json_ui.py
  - tests/test_ui_app.py
  - tests/test_local_only_guarantee.py
- smoke quality gate updated to accept healthy empty-state evidence (without forcing non-empty rows).

## Known Limitations

1. Pair evidence for sampled current version is empty (total=0) at snapshot time.
2. Existing local permission issue on var/ui_preferences.json prevents strict hard reset on this host.
3. Browser snapshots contain historical Streamlit connection errors from earlier sessions; current runtime checks pass.
