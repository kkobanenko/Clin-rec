# Release Rehearsal 2026-04-22

## 1. Build Identification

- Date: 2026-04-22 16:17:07 MSK
- Branch: `main`
- Commit SHA: `1391f95`
- Runtime profile: `docker-compose-only`
- Validation path: `full`
- Artifact bundle:
  - `.artifacts/release_checks/20260422_161707`
- Operator: `GitHub Copilot`

## 2. Observed Gate Results

| Gate | Result | Notes |
| --- | --- | --- |
| Runtime preflight | pass | Compose-backed runtime was already up and the release runner completed against the same `docker-compose-only` profile. |
| Structural smoke | pass | Run `59` completed successfully; health, sync lifecycle, outputs, KB, storage stages, task polling, documents, content and fragments were all green. |
| Quality smoke | pass | Run `60` completed successfully; pair evidence and matrix cell checks were green. |
| API regression | pass | Review API, matrix model ops, outputs API and auxiliary mounts suites all passed in the same full pack. |
| Downstream verification | pass | `tests/test_kb_integration_postgres.py` completed as `2 passed` in the same full pack. |

## 3. Key Evidence

- Structural smoke:
  - run created: `59`
  - status: `completed`
  - discovered: `5`
  - outputs route: green
  - KB master index route: green
- Quality smoke:
  - run created: `60`
  - status: `completed`
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
- Reason: the full release-ready verification pack completed successfully end-to-end through smoke, targeted regression, and KB integration gates on the compose-backed runtime.

## 6. Immediate Next Actions

1. Preserve `.artifacts/release_checks/20260422_161707` as the current clean reference bundle for the 2026-04-22 rehearsal.
2. Reuse `Release Ready Check` and `UI Stack Health` as the primary operator entrypoints for the same local runtime profile.
3. If a later rehearsal is run on a different profile, record it as a separate validation path rather than extending this full-pack record.