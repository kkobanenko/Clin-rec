# Release Summary 2026-04-22

## 1. Build Identification

- Date: 2026-04-22 16:17:07 MSK
- Branch: `main`
- Commit SHA: `1391f95`
- Runtime profile: `docker-compose-only`
- Validation path: `full`
- Artifact bundle(s):
  - `.artifacts/release_checks/20260422_161707`
- Operator: `GitHub Copilot`

## 2. Gate Results

| Gate | Result | Notes |
| --- | --- | --- |
| Runtime preflight | pass | Compose-backed runtime stayed healthy for the full pack. |
| Structural smoke | pass | Run `59` completed successfully. |
| Quality smoke | pass | Run `60` completed successfully with downstream pair-evidence and matrix checks green. |
| API regression | pass | Review API, matrix model ops, outputs API and auxiliary mounts suites all passed. |
| Downstream verification | pass | `tests/test_kb_integration_postgres.py` completed as `2 passed`. |

## 3. Key Evidence

- Structural smoke:
  - run `59`
  - status `completed`
  - discovered `5`
- Quality smoke:
  - run `60`
  - status `completed`
  - pair evidence `10 items` on inspected page, `60 total`
  - matrix cell score `0.13`, confidence `0.575`, supporting evidence `2`
- API regression:
  - `tests/test_pipeline_review_api.py`: `9 passed`
  - `tests/test_matrix_model_ops_api.py`: `10 passed`
  - `tests/test_outputs_api.py`: `7 passed`
  - `tests/test_aux_api_mounts.py`: `2 passed`
- KB integration:
  - `tests/test_kb_integration_postgres.py`: `2 passed`

## 4. Blockers

- none

## 5. Residual Risks

- This summary covers only the `docker-compose-only` runtime profile; any other runtime path should be validated separately.
- Structural smoke still discovered only `5` records on this rehearsal because the discovery strategy remained `playwright_fallback`; this is acceptable for runtime verification but not a completeness claim.

## 6. Scope Boundaries

- Explicitly out of scope for this release: full matrix governance, full reviewer productization, external distribution.
- Deferred to post-MVP: deeper release governance, broader UI productization, extended KB automation beyond current operator workflows.
- Follow-up items for next tranche: preserve rehearsal artifacts, keep operator tasks aligned with the runbook, and decide whether future packs should fail on unexpected warnings.

## 7. Decision

- Final status: `release-ready`
- Decision rationale: the full release-ready verification pack completed successfully end-to-end on the compose-backed runtime without an open blocker.
- Required next action: preserve this summary alongside `docs/RELEASE_REHEARSAL_2026-04-22.md` as the current clean reference record for the 2026-04-22 compose rehearsal.

## 8. Sources of Truth

- `PRD_CR_Intelligence_Platform_v1_6.md`
- `TZ_CR_Intelligence_Platform_v1_5.md`
- `RUNBOOK_RUNTIME_PROFILE.md`
- `docs/RELEASE_READY_CHECKLIST.md`
- `docs/RELEASE_REHEARSAL_2026-04-22.md`
- `DOD_MVP.md`