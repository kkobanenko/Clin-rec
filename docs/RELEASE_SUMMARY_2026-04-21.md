# Release Summary 2026-04-21

## 1. Build Identification

- Date: 2026-04-21 23:42:18 MSK
- Branch: `main`
- Commit SHA: `18074ee`
- Runtime profile: `docker-compose-only`
- Primary artifact bundles:
  - `.artifacts/release_checks/runtime_rehearsal_final_20260421_233024`
  - `.artifacts/release_checks/skip_fast_after_pg_url`

## 2. Gate Results

| Gate | Result | Notes |
| --- | --- | --- |
| Runtime preflight | pass | `docker compose ps` confirmed app, worker, postgres, redis, minio and streamlit were up. |
| Structural smoke | pass | Final smoke run `53` completed successfully. |
| Quality smoke | pass | Final smoke run `54` completed successfully with downstream pair-evidence and matrix checks green. |
| API regression | pass | `test_pipeline_review_api`, `test_matrix_model_ops_api`, `test_outputs_api`, `test_aux_api_mounts` all passed. |
| Downstream verification | pass | Mandatory KB integration gate passed after defaulting `CRIN_INTEGRATION_POSTGRES_URL`; `skip_fast_after_pg_url` completed green. |

## 3. Key Evidence

- Structural smoke:
  - run `53`
  - status `completed`
  - discovered `20`
  - content `8 sections`
  - fragments `18`
- Quality smoke:
  - run `54`
  - status `completed`
  - pair evidence `10 items` on inspected page, `60 total`
  - matrix cell score `0.13`, confidence `0.575`, supporting evidence `2`
- API regression:
  - `tests/test_pipeline_review_api.py`: `9 passed`
  - `tests/test_matrix_model_ops_api.py`: `10 passed`
  - `tests/test_outputs_api.py`: `7 passed`
  - `tests/test_aux_api_mounts.py`: `2 passed`
- KB integration:
  - `tests/test_kb_integration_postgres.py`: `2 passed, 1 warning`

## 4. Blockers

- none

## 5. Residual Risks

- Alembic emitted a deprecation warning about missing `path_separator` in config; this did not block the run, but should be cleaned up later.
- The final green verdict combines one full live rehearsal bundle with one fast late-stage rerun on the same runtime/profile after the runner fix for `CRIN_INTEGRATION_POSTGRES_URL`.
- Runtime queue latency for quality smoke was materially longer than structural smoke, so operator guidance continues to recommend explicit timeout overrides when needed.

## 6. Scope Boundaries

- Explicitly out of scope for this release: full matrix governance, full reviewer productization, external distribution.
- Deferred to post-MVP: deeper release governance, broader UI productization, extended KB automation beyond current operator workflows.
- Follow-up items for next tranche: clean Alembic warning, keep runtime rehearsal artifacts organized, and decide whether to add stricter treatment for warnings in the release pack.

## 7. Decision

- Final status: `release-ready`
- Decision rationale: all mandatory release gates are green after the runner fixes; the previously skipped KB integration gate now executes and passes against the compose-backed Postgres instance.
- Required next action: preserve this summary as the reference go/no-go record and use the updated release runner/checklist for subsequent rehearsals.

## 8. Sources of Truth

- `PRD_CR_Intelligence_Platform_v1_6.md`
- `TZ_CR_Intelligence_Platform_v1_5.md`
- `RUNBOOK_RUNTIME_PROFILE.md`
- `docs/RELEASE_READY_CHECKLIST.md`
- `docs/RELEASE_REHEARSAL_2026-04-21.md`
- `DOD_MVP.md`