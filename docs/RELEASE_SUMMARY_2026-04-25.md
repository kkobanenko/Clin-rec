# Release Summary 2026-04-25

## 1. Build Identification

- Date: 2026-04-25 14:07:20 MSK
- Branch: `main`
- Commit SHA: `b0f0484`
- Runtime profile: `pilot-compose-local`
- Validation path: `full`
- Artifact bundle(s):
  - `.artifacts/release_checks/20260425_140515`
- Operator: `GitHub Copilot`

## 2. Gate Results

| Gate | Result | Notes |
| --- | --- | --- |
| Runtime preflight | pass | `scripts/pilot_preflight.sh` passed before release pack (`PASS: pilot preflight completed`). |
| Structural smoke | pass | Run `88` completed; memo task `c0ae54ea-39e5-4eb2-afd3-a5dacc3172d9` reached `SUCCESS`; generated output `48` retrievable via `/outputs/48`. |
| Quality smoke | pass | Run `89` completed; memo task `07625ea3-ea0e-4ee4-a057-0beca74342f1` reached `SUCCESS`; generated output `49` retrievable; downstream pair-evidence and matrix checks passed. |
| Discovery report | pass | Smoke release pack remained bounded to smoke semantics; downstream pair-evidence for current version `4` still returned rows while completeness claim remains smoke-only. |
| Raw Source Artifacts UI smoke | pass | `Download`, `Preview` and `Load Evidence For Current Version` validated in Streamlit; no leaked `http://app:8000/...` browser URLs remain. |
| API regression | pass | Review, matrix model ops, outputs API, document outcomes API, and auxiliary route suites all green in full pack. |
| Downstream verification | pass | `tests/test_kb_integration_postgres.py` completed as `2 passed` in release pack. |

## 3. Key Evidence

- Structural smoke reference:
  - run `88`
  - terminal state `completed`
  - task `/tasks/c0ae54ea-39e5-4eb2-afd3-a5dacc3172d9` -> `SUCCESS`
  - output `/outputs/48` retrievable (`status=pending` as draft)
- Quality smoke reference:
  - run `89`
  - terminal state `completed`
  - task `/tasks/07625ea3-ea0e-4ee4-a057-0beca74342f1` -> `SUCCESS`
  - output `/outputs/49` retrievable (`status=pending` as draft)
  - pair evidence endpoint returned non-empty page (`10 items`, `60 total`)
  - matrix cell endpoint returned score/confidence/evidence tuple (`score=0.13`, `confidence=0.575`, `evidence=2`)
- Discovery strategy report reference:
  - smoke mode evidence remains bounded by release-pack logs and direct API checks for current document version `4`
  - `mode=smoke`
  - `strategy=playwright_fallback`
  - `source_count=5`
  - `limit_applied=false`
  - `completeness_claim=smoke_only`
  - Explicit scope statement: this confirms smoke runtime behavior only and is not a full-corpus completeness proof.
- Raw Source Artifacts UI smoke reference: `docs/UI_SMOKE_RAW_SOURCE_ARTIFACTS_2026-04-25.md`
- Review API regression reference: `.artifacts/release_checks/20260425_140515/review_api.log` (`10 passed`)
- Matrix model ops reference: `.artifacts/release_checks/20260425_140515/matrix_model_ops.log` (`10 passed`)
- Outputs API reference: `.artifacts/release_checks/20260425_140515/outputs_api.log` (`18 passed`)
- Document outcomes API regression reference: `.artifacts/release_checks/20260425_140515/document_outcomes_api.log` (`7 passed`)
- Auxiliary mounts reference: `.artifacts/release_checks/20260425_140515/aux_routes.log` (`2 passed`)
- KB/output verification reference: verified terminal completion plus readable output retrieval in both smoke modes; KB integration regression passed (`2 passed`).

## 4. Blockers

- none

## 5. Residual Risks

- Discovery remained in fallback strategy (`playwright_fallback`) with API status `451`; acceptable for smoke runtime checks, not for corpus completeness claims.
- Shared API key model is pilot-minimum security and remains internal-only hardening scope.
- Full-corpus verification workflow is still outside this smoke-oriented release pack and must be validated separately when corpus mode is scheduled.
- Manual browser-download event could not be captured from the integrated browser tooling, but the UI no longer exposes invalid artifact URLs and the server-side artifact path is covered by both smoke and regression tests.

## 6. Scope Boundaries

- Explicitly out of scope for this release: external user management, full production IAM, major architecture changes.
- Deferred to post-MVP: deeper governance automation, broader reviewer productization, full corpus verification playbook.
- Follow-up items for next tranche: run dedicated corpus-mode discovery validation and attach a separate completeness report artifact for that mode.

## 7. Decision

- Final status: `validated internal pilot build`
- Decision rationale: targeted RawSourceArtifacts UI blocker is closed; manual UI smoke passed for `Download`, `Preview` and evidence loading; focused regressions passed; pilot preflight and full release-ready verification pack passed on `pilot-compose-local`.
- Required next action: proceed with controlled internal pilot while keeping full-corpus completeness validation as a separate evidence track.

## 8. Sources of Truth

- `PRD_CR_Intelligence_Platform_v1_9.md`
- `TZ_CR_Intelligence_Platform_v1_8.md`
- `RUNBOOK_PILOT_RUNTIME_PROFILE.md`
- `docs/RELEASE_READY_CHECKLIST.md`
- `DOD_MVP_PILOT_v1.md`