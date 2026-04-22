# Release Rehearsal 2026-04-21

## 1. Build Identification

- Date: 2026-04-21 23:38:21 MSK
- Branch: `main`
- Commit SHAs observed:
  - `49fb4aa` for the full `runtime_rehearsal_final_*` pack
  - `3b5d815` for the fast late-stage rerun with smoke skips and mandatory KB skip guard
  - `8117d35` for the follow-up Alembic warning fix validated by a clean full release pack
- Runtime profile: `docker-compose-only`
- Artifact bundles:
  - `.artifacts/release_checks/runtime_rehearsal_final_20260421_233024`
  - `.artifacts/release_checks/skip_fast`
  - `.artifacts/release_checks/20260422_154108`

## 2. Observed Gate Results

| Gate | Result | Notes |
| --- | --- | --- |
| Runtime preflight | pass | `docker compose ps` confirmed `crin_app`, `crin_worker`, `crin_postgres`, `crin_redis`, `crin_minio`, `crin_streamlit` were up. |
| Structural smoke | pass | Final rehearsal run `53`; lifecycle, outputs, KB, storage stages, task polling, documents/content/fragments all green. |
| Quality smoke | pass | Final rehearsal run `54`; pair evidence and matrix cell checks passed after a long `pending` phase. |
| API regression | pass | Review, matrix model ops, outputs and auxiliary mounts suites all passed in the late-stage part of the final rehearsal. |
| Downstream verification | pass | The original skipped KB gate was fixed first via `CRIN_INTEGRATION_POSTGRES_URL`, then revalidated in the clean full pack `20260422_154108`; `tests/test_kb_integration_postgres.py` completed as `2 passed` without warnings. |

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
  - original blocker state: `2 skipped`
  - final clean full-pack state: `2 passed`

## 4. Blocking Issue Observed

- The original runner issue after quality smoke was resolved: a later full rehearsal reached the pytest stages successfully.
- The narrower KB integration blocker was then resolved by wiring the compose-backed integration Postgres URL into the runner.
- A later config cleanup added `path_separator = os` to `alembic.ini`, and the subsequent full release pack completed without the earlier Alembic warning.

## 5. Interim Decision

- Current status: `pass`
- Reason: the previously blocked mandatory KB integration gate now executes cleanly in both targeted and full-pack validation, so the rehearsal record no longer carries an open blocker.

## 6. Immediate Next Actions

1. Preserve the clean full-pack artifact `20260422_154108` as the latest warning-free reference bundle.
2. Keep using the release runner/checklist pair for subsequent rehearsals on the same `docker-compose-only` profile.
3. If warning policy becomes stricter later, fail the pack on unexpected warnings rather than documenting them post hoc.