## 2026-04-25 — Milestone A canonical docs sync

Changed:
- Updated README to reference PRD v1.7, TZ v1.6, DOD_MVP_PILOT_v1 and pilot docs in docs/.
- Updated stage wording to `release-ready MVP -> pilot hardening`.
- Split backlog into release blockers / pilot blockers / post-MVP polish.
- Added docs-level canonical wrappers: ROADMAP_PILOT_HARDENING_v1.md, OPERATOR_RUNBOOK_PILOT_v1.md, DISCOVERY_COMPLETENESS_PLAN_v1.md.

Tests:
- command: grep checks on README/docs links (run below)
- result: pass (old PRD/TZ refs now limited to historical release summary records)

Release impact:
- doc-only

Residual risks:
- Milestone B+ (discovery completeness reporting, pilot preflight, governance hardening) not implemented yet.

## 2026-04-25 — Milestone B discovery completeness hardening (partial complete)

Changed:
- Added `CRIN_DISCOVERY_MODE` support via `settings.discovery_mode` (`smoke` default, `corpus` optional).
- Added structured `discovery_strategy_report` to `PipelineRun.stats_json` in discovery execution path.
- Added API attempt/status/fallback metadata flow in discovery strategy stats.
- Updated full-sync limit behavior: applies only for `discovery_mode=smoke`.
- Added smoke wording clarifications in `scripts/e2e_smoke.py` to separate smoke validation from completeness claims.
- Expanded discovery tests for strategy report fields, fallback status propagation, and smoke/corpus limit semantics.
- Fixed sqlite pytest harness for PostgreSQL `TSVECTOR` type compilation in tests.

Tests:
- command: `.venv/bin/pytest -q tests/test_discovery.py tests/test_source_validation.py tests/test_api_health.py`
- result: pass (`15 passed`)

Release impact:
- non-blocker hardening (runtime/reporting + tests), additive only

Residual risks:
- Full architect Milestone B not fully closed yet: still need richer `completeness_claim` semantics and broader release-summary integration wording.
- Milestone C+ (pilot runtime preflight, output governance, KB lint expansion, auth minimum) not implemented yet.

## 2026-04-25 — Milestone C pilot runtime profile and preflight

Changed:
- Added `RUNBOOK_PILOT_RUNTIME_PROFILE.md` with selected pilot profile `pilot-compose-local`.
- Added executable `scripts/pilot_preflight.sh` with checks for compose config, required env vars, disk space, service availability, bucket directory, and alembic current/head alignment.
- Added lightweight assertions in `tests/test_pilot_preflight_script.py` to protect script contract.
- Updated `docs/RELEASE_READY_CHECKLIST.md` with separate pilot runtime gate and pilot runbook reference.

Tests:
- command: `.venv/bin/pytest -q tests/test_pilot_preflight_script.py`
- result: pass (`5 passed`)
- command: `bash scripts/pilot_preflight.sh`
- result: pass

Release impact:
- non-blocker hardening (pilot operations guardrails), additive only

Residual risks:
- Preflight uses container-level bucket directory check (`/data/cr-artifacts`) as practical signal; deeper S3 API-level bucket audit still optional hardening.

## 2026-04-25 — Milestone D output governance hardening (partial complete)

Changed:
- Added governance frontmatter and operator disclaimer to generated memo markdown (`output_release_id`, `generator_version`, `generated_at`, `review_status`, `source_artifacts`).
- Updated output lifecycle defaults in service layer: new outputs use `review_status=pending_review`; accepted file-back maps to `review_status=approved`.
- Added backward-compatible review-status handling:
	- API list filter aliasing (`pending_review` includes legacy `pending`/`needs_review`; `approved` includes legacy `accepted`).
	- response schema normalizes legacy statuses (`pending -> pending_review`, `accepted -> approved`).
- Updated Outputs UI review-status filter options to include `pending_review` and `released` semantics.
- Added i18n labels for `pending_review` and `released`.
- Updated/expanded output tests for governance memo header/disclaimer and status alias normalization behavior.

Tests:
- command: `.venv/bin/pytest -q tests/test_outputs_api.py tests/test_output_memo.py`
- result: pending (run after patch)

Release impact:
- additive governance hardening; backward-compatible status aliasing preserved for legacy rows.

Residual risks:
- Dedicated `release` endpoint/status transition guard is still not implemented in this slice.

## 2026-04-25 — Milestone E KB quality/lint expansion (partial complete)

Changed:
- Expanded `KnowledgeLintService` checks for:
	- provenance gaps across core KB artifact types;
	- non-hypothesis claims missing provenance (including JSON null);
	- duplicate canonical slug detection;
	- empty summary detection;
	- stale source version linkage (`document_version.is_current=false`);
	- orphan entities (`document`/`molecule`) without linked `entity_page`;
	- conflict groups with missing review status.
- Enriched KB compiler frontmatter metadata for generated artifacts with:
	- `artifact_type`, `source_document_version_ids`, `source_hashes`, `generator_version`,
		`confidence`, `review_status`, `claim_count`, `generated_at`.
- Extended `master_index` manifest/frontmatter to include `warning_counts`
	(`empty_summary`, `missing_provenance`) alongside artifact counts.
- Added targeted unit coverage:
	- `tests/test_knowledge_lint.py` (missing provenance, empty summary);
	- `tests/test_knowledge_compile.py` (rich frontmatter, master index warning counts).

Tests:
- command: `.venv/bin/pytest -q tests/test_knowledge_compile.py tests/test_knowledge_lint.py tests/test_knowledge_conflicts.py tests/test_kb_api.py tests/test_kb_integration_postgres.py`
- result: pass (`10 passed, 2 skipped`)

Release impact:
- non-blocker hardening, additive only

Residual risks:
- `duplicate_canonical_slug` lint check remains mostly sentinel-level because DB unique constraint already prevents duplicates in normal writes.
- Full pilot-grade KB lint policy can still grow (e.g., richer stale-source heuristics and severity taxonomy).
