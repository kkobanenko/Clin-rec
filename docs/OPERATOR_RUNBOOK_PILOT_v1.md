# OPERATOR RUNBOOK PILOT v1

Дата: 2026-04-25

Этот документ — canonical operator runbook в `docs/`.
Основной source content: [../OPERATOR_RUNBOOK_PILOT_v1.md](../OPERATOR_RUNBOOK_PILOT_v1.md).

## Runtime baseline

- Validated baseline: `docker-compose-only`.
- Target stage: pilot hardening.

## Minimal operator flow

1. Preflight runtime/profile.
2. Run structural smoke.
3. Run quality smoke.
4. Run targeted regression packs.
5. Review residual risks.
6. Decide go/no-go.

## Guardrail

Не обновлять release summary без фактического нового evidence run.
