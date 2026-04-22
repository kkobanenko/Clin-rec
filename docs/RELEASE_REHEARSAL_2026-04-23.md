# Release Rehearsal 2026-04-23

## 1. Build Identification

- Date: 2026-04-23 01:09:35 MSK
- Branch: `main`
- Commit SHA: `61eb4e7`
- Runtime profile: `docker-compose-only`
- Validation path: `full`
- Artifact bundle:
  - `.artifacts/release_checks/20260423_010935`
- Operator: `GitHub Copilot`

## 2. Observed Gate Results

| Gate | Result | Notes |
| --- | --- | --- |
| Runtime preflight | pass | Compose-backed runtime stayed healthy and full release runner executed on same `docker-compose-only` profile. |
| Structural smoke | pass | Run `71` completed successfully; health, sync lifecycle, outputs, KB, storage stages, task polling, generated output retrieval, documents, content and fragments were green. |
| Quality smoke | pass | Run `72` completed successfully; output task completion, pair evidence and matrix cell checks were green. |
| API regression | pass | Review API, matrix model ops, outputs API and auxiliary mounts suites all passed in same full pack. |
| Downstream verification | pass | `tests/test_kb_integration_postgres.py` completed as `2 passed` in same full pack. |

## 3. Key Evidence

- Structural smoke:
  - run created: `71`
  - status: `completed`
  - discovered: `5`
  - queued memo task: `SUCCESS`
  - generated output detail: `GET /outputs/29` green
  - enforced auxiliary checks: outputs, KB master index, storage stages, task status, generated output
- Quality smoke:
  - run created: `72`
  - status: `completed`
  - queued memo task: `SUCCESS`
  - generated output detail: `GET /outputs/30` green
  - pair evidence page: `10` items, `60` total
  - matrix cell: score `0.13`, confidence `0.575`, supporting evidence `2`
- API regression:
  - `tests/test_pipeline_review_api.py`: `9 passed`
  - `tests/test_matrix_model_ops_api.py`: `10 passed`
  - `tests/test_outputs_api.py`: `7 passed`
  - `tests/test_aux_api_mounts.py`: `2 passed`
- KB integration:
  - `tests/test_kb_integration_postgres.py`: `2 passed`

## 4. Blocking Issue Observed

- none

## 5. Interim Decision

- Current status: `pass`
- Reason: full release-ready verification pack completed successfully end-to-end through smoke, targeted regression and KB integration gates on compose-backed runtime after raw-artifact access rollout and document-model health fix.

## 6. Immediate Next Actions

1. Preserve `.artifacts/release_checks/20260423_010935` as current clean reference bundle for 2026-04-23 rehearsal.
2. Reuse `Release Ready Check` and `UI Stack Health` as primary operator entrypoints for same local runtime profile.
3. Track remaining phase-2 backlog items separately from this clean MVP release record.