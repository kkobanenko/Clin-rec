# Release Summary Template

Используйте этот шаблон после полного прогона release-ready verification pack.

## 1. Build Identification

- Date:
- Branch:
- Commit SHA:
- Runtime profile: `host-only` / `docker-compose-only`
- Validation path: `full` / `late-stage rerun` / `composite`
- If `composite`, briefly state which full rehearsal established the smoke-green baseline and which later rerun closed the remaining regression gates.
- Artifact bundle(s):
- Operator:

## 2. Gate Results

| Gate | Result | Notes |
| --- | --- | --- |
| Runtime preflight | pass / fail |  |
| Structural smoke | pass / fail | Record whether a freshly queued memo/output task reached `SUCCESS` and the generated output was retrievable. |
| Quality smoke | pass / fail | Record downstream pair-evidence and matrix checks, plus memo/output task completion if this mode queued output generation. |
| Discovery report | pass / fail | Record discovery mode, strategy, source count, limit flag and completeness claim (smoke vs corpus). |
| API regression | pass / fail |  |
| Downstream verification | pass / fail |  |

## 3. Key Evidence

- Structural smoke reference: include run id, terminal state, and memo/output completion evidence (`/tasks/{task_id}`, `/outputs/{output_id}`)
- Quality smoke reference: include run id, terminal state, downstream evidence, and memo/output completion evidence when applicable
- Discovery strategy report reference: include `mode`, `strategy`, `source_count`, `limit_applied`, `completeness_claim` and explicit statement whether this is smoke validation or corpus completeness.
- Review API regression reference:
- Matrix model ops reference:
- Outputs API reference:
- Document outcomes API regression reference:
- Auxiliary mounts reference:
- KB/output verification reference: state whether verification was limited to visibility or confirmed terminal completion plus readable result

## 4. Blockers

- Blocker 1:
- Blocker 2:
- Blocker 3:

Если blocker-ов нет, зафиксировать `none`.

## 5. Residual Risks

- Risk 1:
- Risk 2:
- Risk 3:

Фиксировать только те риски, которые допустимы для MVP и явно вынесены за immediate release scope.

## 6. Scope Boundaries

- Explicitly out of scope for this release:
- Deferred to post-MVP:
- Follow-up items for next tranche:

## 7. Decision

- Final status: `release-ready` / `blocked`
- Decision rationale:
- Required next action:

## 8. Sources of Truth

- `PRD_CR_Intelligence_Platform_v1_7.md`
- `TZ_CR_Intelligence_Platform_v1_6.md`
- `RUNBOOK_RUNTIME_PROFILE.md`
- `docs/RELEASE_READY_CHECKLIST.md`
- `DOD_MVP.md`