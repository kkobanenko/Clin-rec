# Release Rehearsal 2026-04-21

## 1. Build Identification

- Date: 2026-04-21 23:26:53 MSK
- Branch: `main`
- Commit SHA: `38651be`
- Runtime profile: `docker-compose-only`
- Artifact bundle: `.artifacts/release_checks/runtime_rehearsal_20260421_232153`

## 2. Observed Gate Results

| Gate | Result | Notes |
| --- | --- | --- |
| Runtime preflight | pass | `docker compose ps` confirmed `crin_app`, `crin_worker`, `crin_postgres`, `crin_redis`, `crin_minio`, `crin_streamlit` were up. |
| Structural smoke | pass | Run `47`; lifecycle, outputs, KB, storage stages, task polling, documents/content/fragments all green. |
| Quality smoke | pass | Run `48`; pair evidence and matrix cell checks passed after long `pending` phase. |
| API regression | not run | Full runner did not reach pytest stage in this rehearsal. |
| Downstream verification | partial | Quality smoke validated pair-evidence and matrix cell, but dedicated regression suites were not executed. |

## 3. Key Evidence

- Structural smoke highlights:
  - run created: `47`
  - status: `completed`
  - discovered: `20`
  - content: `8` sections
  - fragments: `18`
- Quality smoke highlights:
  - run created: `48`
  - final status: `completed`
  - long `pending` period before transition to `running`
  - pair evidence: `10` items on inspected page, `60` total
  - matrix cell: score `0.13`, confidence `0.575`, supporting evidence `2`

## 4. Blocking Issue Observed

- The original live rehearsal reached successful structural and quality smoke completion, but the shell runner terminated before the pytest stage, so the full release pack did not complete end to end.
- A fresh retry was started with the current runner and a larger `SMOKE_POLL_TIMEOUT`, but its tail had not yet been confirmed at the time of this summary.

## 5. Interim Decision

- Current status: `blocked`
- Reason: release-ready decision cannot be declared until targeted API regression and the remainder of the release pack complete on the live runtime.

## 6. Immediate Next Actions

1. Finish or rerun the fresh `runtime_rehearsal_retry_*` bundle to confirm the current runner gets past smoke into pytest suites.
2. If pytest still does not start, isolate the runner failure after quality smoke and patch that slice.
3. When the full pack completes, update this rehearsal record or generate a final summary from `docs/RELEASE_SUMMARY_TEMPLATE.md`.