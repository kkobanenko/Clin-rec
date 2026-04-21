# Release Rehearsal 2026-04-21

## 1. Build Identification

- Date: 2026-04-21 23:38:21 MSK
- Branch: `main`
- Commit SHAs observed:
  - `49fb4aa` for the full `runtime_rehearsal_final_*` pack
  - `3b5d815` for the fast late-stage rerun with smoke skips and mandatory KB skip guard
- Runtime profile: `docker-compose-only`
- Artifact bundles:
  - `.artifacts/release_checks/runtime_rehearsal_final_20260421_233024`
  - `.artifacts/release_checks/skip_fast`

## 2. Observed Gate Results

| Gate | Result | Notes |
| --- | --- | --- |
| Runtime preflight | pass | `docker compose ps` confirmed `crin_app`, `crin_worker`, `crin_postgres`, `crin_redis`, `crin_minio`, `crin_streamlit` were up. |
| Structural smoke | pass | Final rehearsal run `53`; lifecycle, outputs, KB, storage stages, task polling, documents/content/fragments all green. |
| Quality smoke | pass | Final rehearsal run `54`; pair evidence and matrix cell checks passed after a long `pending` phase. |
| API regression | pass | Review, matrix model ops, outputs and auxiliary mounts suites all passed in the late-stage part of the final rehearsal. |
| Downstream verification | blocked | `tests/test_kb_integration_postgres.py` completed as `2 skipped`; the runner now treats that as a failed mandatory gate. |

## 3. Key Evidence

- Structural smoke highlights:
  - run created: `53`
  - status: `completed`
  - discovered: `20`
  - content: `8` sections
  - fragments: `18`
- Quality smoke highlights:
  - run created: `54`
  - final status: `completed`
  - long `pending` period before transition to `running`
  - pair evidence: `10` items on inspected page, `60` total
  - matrix cell: score `0.13`, confidence `0.575`, supporting evidence `2`
- API regression highlights:
  - `tests/test_pipeline_review_api.py`: `9 passed`
  - `tests/test_matrix_model_ops_api.py`: `10 passed`
  - `tests/test_outputs_api.py`: `7 passed`
  - `tests/test_aux_api_mounts.py`: `2 passed`
- KB integration highlight:
  - `tests/test_kb_integration_postgres.py`: `2 skipped`

## 4. Blocking Issue Observed

- The original runner issue after quality smoke was resolved: a later full rehearsal reached the pytest stages successfully.
- The current blocker is narrower and explicit: the mandatory KB integration gate currently skips, and the runner now fails the pack when that happens.

## 5. Interim Decision

- Current status: `blocked`
- Reason: release-ready decision cannot be declared while the mandatory KB integration gate remains unexecuted and reports `skipped` instead of a real pass/fail outcome.

## 6. Immediate Next Actions

1. Make `tests/test_kb_integration_postgres.py` runnable in the active release environment instead of skipping.
2. Rerun the release pack or the late-stage `skip_fast` path and confirm KB integration turns green instead of skipped.
3. When the KB gate passes, generate a final go/no-go summary from `docs/RELEASE_SUMMARY_TEMPLATE.md`.