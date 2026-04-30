# PRD CR Intelligence Platform v2.7 Restart v1

## Objective
Provide deeper governance reasoning primitives to support release confidence decisions and explainability.

## Functional Requirements
1. Evidence digest scoring and verdicting.
2. Signal normalization across heterogeneous metrics.
3. Conflict detection for contradictory governance outcomes.
4. Drift analysis between baseline and current governance snapshots.
5. Release guard decisioning with explicit reasons.
6. Trace timeline reconstruction and trend extraction.
7. Readiness window calculation for release operations.
8. Policy recommendation based on score, volatility, incidents.
9. Explainability pack narrative generation.
10. Iteration journal summarization for operator traceability.

## Non-Functional Requirements
- Deterministic outputs for identical inputs.
- Lightweight pure-Python service logic.
- Unit-test coverage for core branches.

## Success Criteria
- New modules present and importable.
- Tests validate pass/fail paths across all new services.
