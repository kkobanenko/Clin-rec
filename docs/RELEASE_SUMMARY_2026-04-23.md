# Release Summary 2026-04-23

## 1. Build Identification

- Date: 2026-04-23 01:15:21 MSK
- Branch: `main`
- Commit SHA: `47fed51`
- Runtime profile: `docker-compose-only`
- Validation path: `composite`
- Full rehearsal baseline: `docs/RELEASE_REHEARSAL_2026-04-23.md` at commit `61eb4e7`
- Late-stage rerun closed remaining regression gates at commit `47fed51`
- Artifact bundle(s):
  - `.artifacts/release_checks/20260423_010935`
  - `.artifacts/release_checks/20260423_011521`
- Operator: `GitHub Copilot`

## 2. Gate Results

| Gate | Result | Notes |
| --- | --- | --- |
| Runtime preflight | pass | Compose-backed runtime stayed healthy across full rehearsal and late-stage rerun on same profile. |
| Structural smoke | pass | Full rehearsal baseline remained green: run `71` completed successfully, including worker-backed memo-task completion, generated output retrieval and auxiliary-route checks. |
| Quality smoke | pass | Full rehearsal baseline remained green: run `72` completed successfully with worker-backed memo-task completion, downstream pair-evidence and matrix checks green. |
| API regression | pass | Review API, matrix model ops, outputs API, document outcomes API and auxiliary mounts suites all passed on late-stage rerun at commit `47fed51`. |
| Downstream verification | pass | `tests/test_kb_integration_postgres.py` completed as `2 passed`. |

## 3. Key Evidence

- Structural smoke:
  - run `71`
  - status `completed`
  - discovered `5`
  - queued memo task `SUCCESS`
  - generated output `29` retrievable via `/outputs/29`
  - auxiliary route/task checks enforced in terminal pass/fail decision
- Quality smoke:
  - run `72`
  - status `completed`
  - queued memo task `SUCCESS`
  - generated output `30` retrievable via `/outputs/30`
  - pair evidence `10 items` on inspected page, `60 total`
  - matrix cell score `0.13`, confidence `0.575`, supporting evidence `2`
- API regression:
  - `tests/test_pipeline_review_api.py`: `9 passed`
  - `tests/test_matrix_model_ops_api.py`: `10 passed`
  - `tests/test_outputs_api.py`: `7 passed`
  - `tests/test_document_pipeline_outcomes_api.py`: `5 passed`
  - `tests/test_aux_api_mounts.py`: `2 passed`
- KB integration:
  - `tests/test_kb_integration_postgres.py`: `2 passed`

## 4. Blockers

- none

## 5. Residual Risks

- This summary covers only `docker-compose-only` runtime profile; any other runtime path still needs separate validation.
- Structural smoke still discovered only `5` records because discovery strategy remained `playwright_fallback`; acceptable for runtime verification, not completeness claim.
- Remaining phase-2 backlog items around deeper governance, richer UI and broader knowledge automation remain outside immediate MVP release scope.

## 6. Scope Boundaries

- Explicitly out of scope for this release: full matrix governance, full reviewer productization, external distribution.
- Deferred to post-MVP: deeper release governance, broader UI productization, extended KB automation beyond current operator workflows.
- Follow-up items for next tranche: close remaining phase-2 backlog gaps, keep release docs/versioning synced, decide whether future packs should fail on unexpected warnings.

## 7. Decision

- Final status: `release-ready`
- Decision rationale: full rehearsal established smoke-green baseline on compose runtime, and committed late-stage rerun at `47fed51` closed targeted regression including document outcomes/raw-artifact coverage without open blocker.
- Required next action: preserve this summary alongside `docs/RELEASE_REHEARSAL_2026-04-23.md` as current composite reference record for compose validation.

## 8. Sources of Truth

- `PRD_CR_Intelligence_Platform_v1_6.md`
- `TZ_CR_Intelligence_Platform_v1_5.md`
- `RUNBOOK_RUNTIME_PROFILE.md`
- `docs/RELEASE_READY_CHECKLIST.md`
- `docs/RELEASE_REHEARSAL_2026-04-23.md`
- `DOD_MVP.md`