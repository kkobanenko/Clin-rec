# Component Versioning & Reproducibility

This document tracks component versions for reproducibility across runs, per PRD section 4 (Version everything) and section 9 (Reproducibility).

## Service Versions

## Document Versions

### PRD v1.6 (2026-04-21)

**File:** `PRD_CR_Intelligence_Platform_v1_6.md`

**Changelog:**
- Added product advancement plan for transition from quality-capable implementation to release-ready MVP.
- Added formal release contract, release gates, and go/no-go semantics.
- Added scope boundaries between immediate release hardening and post-MVP productization.
- Synced release-ready contract with additive raw document artifact access semantics and current-version validation rules.

### TZ v1.5 (2026-04-21)

**File:** `TZ_CR_Intelligence_Platform_v1_5.md`

**Changelog:**
- Added execution-ready technical plan for release-hardening tranche.
- Added work packages for runtime preflight, regression pack, governance completion, downstream verification, and release rehearsal.
- Added release-ready statuses, required release artifacts, and acceptance criteria.
- Synced technical tranche with additive raw-artifact API/UI access, valid-artifact filtering, and regression coverage expectations.

### Release Evidence Sync (2026-04-23)

**Files:** `docs/RELEASE_REHEARSAL_2026-04-23.md`, `docs/RELEASE_SUMMARY_2026-04-23.md`, `README.md`, `docs/RELEASE_READY_CHECKLIST.md`

**Changelog:**
- Added fresh compose-backed full-pack release evidence for commit `61eb4e7`.
- Promoted 2026-04-23 rehearsal/summary as current clean reference docs in README and checklist examples.
- Captured current gate evidence after raw document artifact access and document-model health fix.

### Release Evidence Sync (2026-04-23, late-stage rerun)

**Files:** `docs/RELEASE_SUMMARY_2026-04-23.md`, `.artifacts/release_checks/20260423_074011`

**Changelog:**
- Refreshed current composite release summary to latest committed head `578f578`.
- Captured late-stage rerun after scoring explanation ids, output artifact linkage and output UI follow-up.
- Confirmed operator/API regression pack remained green on same compose-backed runtime profile.

### Release Evidence Sync (2026-04-23, late-stage rerun refresh)

**Files:** `docs/RELEASE_SUMMARY_2026-04-23.md`, `.artifacts/release_checks/20260423_122035`

**Changelog:**
- Refreshed current composite release summary to validated head `4d35f23`.
- Captured late-stage rerun after discovery metrics/max-record repair, compiler auto-claims/frontmatter and KB artifact-detail UI follow-up.
- Confirmed operator/API regression pack and KB Postgres integration remained green on same compose-backed runtime profile.

### Release Evidence Sync (2026-04-23, full rerun refresh)

**Files:** `docs/RELEASE_SUMMARY_2026-04-23.md`, `.artifacts/release_checks/20260423_154936`

**Changelog:**
- Refreshed current composite release summary to validated head `f0c0a6a`.
- Captured full release-ready rerun after KB/output filter/detail operator-surface additions and KB lint follow-up.
- Confirmed structural smoke, quality smoke, API regression and KB Postgres integration remained green on same compose-backed runtime profile.

### Release Evidence Sync (2026-04-23, late-stage rerun refresh 2)

**Files:** `docs/RELEASE_SUMMARY_2026-04-23.md`, `.artifacts/release_checks/20260423_160051`

**Changelog:**
- Captured latest late-stage rerun on head `f545473` after KB review-status filters, KB conflict summaries and outputs review-status filtering.
- Confirmed review API, matrix model ops, outputs API, document outcomes API, aux routes and KB Postgres integration remained green on same compose-backed runtime profile.

### Release Evidence Sync (2026-04-23, late-stage rerun refresh 3)

**Files:** `VERSIONING.md`, `docs/TZ_PRD_PHASE2_BACKLOG.md`, `.artifacts/release_checks/20260423_164938`

**Changelog:**
- Captured latest late-stage rerun on head `79f4ede` after KB conflict artifact filter, structured entity detail UI, entity alias search, outputs generator-version filter and claims conflict-flag UI follow-up.
- Confirmed review API, matrix model ops, outputs API, document outcomes API, aux routes and KB Postgres integration remained green on same compose-backed runtime profile.

### Release Evidence Sync (2026-04-23, late-stage rerun refresh 4)

**Files:** `VERSIONING.md`, `docs/TZ_PRD_PHASE2_BACKLOG.md`, `.artifacts/release_checks/20260423_165453`

**Changelog:**
- Captured latest late-stage rerun on head `7e10158` after KB artifact generator-version filter plus compact KB entity/output table follow-up.
- Confirmed review API, matrix model ops, outputs API, document outcomes API, aux routes and KB Postgres integration remained green on same compose-backed runtime profile.

### Release Evidence Sync (2026-04-23, full rerun refresh 2)

**Files:** `docs/RELEASE_SUMMARY_2026-04-23.md`, `.artifacts/release_checks/20260423_165810`

**Changelog:**
- Refreshed current composite release summary to validated head `b2f2363`.
- Captured full release-ready rerun after KB artifact generator-version filter and compact KB/output operator table follow-up.
- Confirmed structural smoke, quality smoke, API regression and KB Postgres integration remained green on same compose-backed runtime profile.

### Release Evidence Sync (2026-04-23, late-stage rerun refresh 5)

**Files:** `VERSIONING.md`, `docs/TZ_PRD_PHASE2_BACKLOG.md`, `.artifacts/release_checks/20260423_171526`

**Changelog:**
- Captured latest late-stage rerun on head `67e3797` after expanded KB conflict scoping, KB artifact body search, KB entity ref search, richer KB/output detail metrics and outputs scope search.
- Confirmed review API, matrix model ops, outputs API, document outcomes API, aux routes and KB Postgres integration remained green on same compose-backed runtime profile.

### Release Evidence Sync (2026-04-23, late-stage rerun refresh 6)

**Files:** `VERSIONING.md`, `docs/TZ_PRD_PHASE2_BACKLOG.md`, `.artifacts/release_checks/20260423_172540`

**Changelog:**
- Captured latest late-stage rerun on head `a4a7c24` after outputs has-file filter and final KB/output operator-surface follow-up.
- Confirmed review API, matrix model ops, outputs API, document outcomes API, aux routes and KB Postgres integration remained green on same compose-backed runtime profile.

### Release Evidence Sync (2026-04-23, late-stage rerun refresh 7)

**Files:** `VERSIONING.md`, `docs/TZ_PRD_PHASE2_BACKLOG.md`, `.artifacts/release_checks/20260423_173642`

**Changelog:**
- Captured latest late-stage rerun on head `574e19c` after compact review history/queue UI and scoring diff summary follow-up.
- Confirmed review API, matrix model ops, outputs API, document outcomes API, aux routes and KB Postgres integration remained green on same compose-backed runtime profile.

### UI Multilinguality Tranche (2026-04-24)

**Files:** `app/ui/app.py`, `app/ui/ui_i18n.py`, `app/ui_i18n.py`, `tests/test_ui_i18n.py`, `TZ_CR_Intelligence_Platform_v1_5.md`, `PRD_CR_Intelligence_Platform_v1_6.md`, `docs/TZ_PRD_PHASE2_BACKLOG.md`

**Changelog:**
- Added backward-compatible Streamlit display-layer i18n for `RU`/`EN` with persisted language preference in `var/ui_preferences.json`.
- Moved the primary i18n implementation under `app/ui/ui_i18n.py` so the Streamlit script can import it safely, and left `app/ui_i18n.py` as a compatibility shim for package-style imports.
- Added focused regression coverage for translation helpers and preference round-trip, plus live compose-backed smoke verification for RU->EN->RU switching.

### Release Evidence Sync (2026-04-24, late-stage rerun)

**Files:** `VERSIONING.md`, `.artifacts/release_checks/20260424_084150`

**Changelog:**
- Captured late-stage rerun on head `20bcdb9` after multilingual Streamlit UI hardening and widget-state repair.
- Confirmed compose-backed regression pack remained green: review API `10 passed`, matrix model ops `10 passed`, outputs API `13 passed`, document outcomes API `5 passed`, aux routes `2 passed`, KB integration `2 passed`.
- Preserved structural/quality smoke evidence boundary from the last full pack while refreshing late-stage operator/API confidence for the current tranche.

### PRD v1.5 (2026-04-21)

**File:** `PRD_CR_Intelligence_Platform_v1_5.md`

**Changelog:**
- Added product advancement plan for transition from orchestration-ready to quality-ready pipeline.
- Added explicit quality contract, content quality gates, and readiness criteria for user evaluation.
- Added prioritized P0/P1/P2 roadmap aligned with current implementation blockers.

### TZ v1.4 (2026-04-21)

**File:** `TZ_CR_Intelligence_Platform_v1_4.md`

**Changelog:**
- Added execution-ready technical plan for quality-ready pipeline transition.
- Added task packages A-H with dependencies, effort estimates, and acceptance semantics.
- Added stage outcome, reason-code, and quality smoke requirements.

### PRD v1.2 (2026-04-01)

**File:** `PRD_CR_Intelligence_Platform_v1_2.md`

**Changelog:**
- Added operational consistency requirement for API/worker queue connectivity.
- Added MVP operational requirements section (runtime profile, broker alignment, smoke validity, isolation policy).
- Added explicit Definition of Done for MVP.

### TZ v1.1 (2026-04-01)

**File:** `TZ_CR_Intelligence_Platform_v1_1.md`

**Changelog:**
- Added mandatory sync PostgreSQL driver requirement for worker runtime.
- Added runtime profile and queue routing alignment requirements.
- Added E2E smoke robustness requirements and extended module acceptance criteria.
- Added explicit Definition of Done for MVP.

### Discovery Service v2.0 (2026-04-01)

**Changelog:**
- Added comprehensive quality metrics to stats_json
- Added version tracking for reproducibility
- Added coverage percentage calculation
- Improved error handling and logging

**Metrics captured:**
- `discovery_service_version`: Service version (for audit trail)
- `timestamp`: Run completion time
- `run_type`: full or incremental
- `wall_time_seconds`: Actual execution duration
- `total_raw_records`: Records extracted before deduplication
- `total_discovered`: Records after deduplication
- `duplicates_detected`: Count of duplicate removals
- `coverage_percent`: Success rate
- `strategy`: Discovery method used (backend_api, playwright_spa, dom_fallback)

**Triggers for version bump:**
- Changes to record extraction logic
- Changes to deduplication algorithm
- Changes to data structure or field mapping
- Changes to quality metrics calculation

### Fetch Service v1.0 (2026-03-31)

**Stable since initial implementation.**
- Retries with exponential backoff (MAX_RETRIES=3, RETRY_BACKOFF=2.0)
- SHA256 content hashing
- S3 artifact storage

### Normalize Service v1.0 (2026-03-31)

**Stable since initial implementation.**
- HTML normalization (BeautifulSoup)
- PDF text extraction (pdfplumber)
- Section/fragment splitting

## Configuration Hashing

## Minimum stats_json Contract (completed run)

For a run with status `completed`, `stats_json` must contain at least:

- `discovery_service_version`
- `run_type`
- `wall_time_seconds`
- `total_discovered`
- `duplicates_detected`
- `coverage_percent`

To track when configuration changes affect reproducibility:

```python
config_hash = hashlib.sha256(
    json.dumps({
        "rubricator_api_base_url": settings.rubricator_api_base_url,
        "rubricator_api_request_delay": settings.rubricator_api_request_delay,
        "rubricator_api_page_size": settings.rubricator_api_page_size,
        # ... other critical settings
    }, sort_keys=True).encode()
).hexdigest()
```

Include in stats_json when available for config-aware reproducibility validation.

## Run Comparison

When comparing two runs:

1. **Identical versions** + **identical configs** = Results must be identical
2. **Different versions** = Results may change legitimately (note changes in stats_json.discovery_service_version)
3. **Different configs** = Results may differ (different request delays, page sizes affect discovery completeness)

## Quality Gates per PRD Section 14

### Gate A — Source Quality ✅
- ✅ Stable discovery (handled by multi-strategy fallback)
- ✅ Low duplicate rate (tracked: `duplicates_detected`)
- ✅ High raw artifact completeness (`coverage_percent`)

**Acceptance:** coverage_percent >= 95% AND duplicates_detected < 1% of total_discovered

### Gate B — Text Quality (Phase 2+)
- Acceptable normalized text completeness
- Quality section split
- Low parser regression

### Gates C–F

Defined in PRD section 14, implemented in later phases.

## Reproducibility Validation Checklist

Before releasing a matrix version or making config changes:

- [ ] Run discovery twice with same version/config
- [ ] Compare stats_json: discovery_service_version, timestamp, coverage_percent must match
- [ ] duplicates_detected should be identical
- [ ] If different: investigate and document
- [ ] Update version number if logic changed
- [ ] Commit version bump with changelog

## Future Enhancements

- [ ] Config hash in stats_json (for reproducibility validation)
- [ ] Parser version tracking in normalize service
- [ ] Schema version for data model changes
- [ ] Audit trail linking matrix cells to discovery run versions

## Release Notes (2026-04-01)

- Added `psycopg2-binary` dependency to support sync SQLAlchemy engine in worker runtime.
- Hardened `scripts/e2e_smoke.py` against intermediate `pending` status and `stats_json = null`.
- Validated successful E2E run path after runtime profile alignment and worker health checks.

## Release Notes (2026-04-21)

- Added PRD v1.5 and TZ v1.4 to formalize the transition plan from orchestration-ready to quality-ready pipeline.
- Updated canonical MVP DoD with quality-smoke semantics for manual document evaluation readiness.
- Updated runtime runbook to distinguish structural smoke from quality smoke and document operator handling of empty-content runs.

## Release Notes (2026-04-23)

- Added additive raw document artifact access via documents API/UI with valid current-version filtering.
- Hid synthetic or invalid raw-source links from user-facing document access paths.
- Fixed document model type-check visibility for `DocumentSection`.
- Re-ran full `Release Ready Check` on compose runtime and recorded green release evidence for commit `61eb4e7`.
- Added scoring explanation traceability ids for contexts, pair-context scores, evidence and fragments.
- Linked accepted filed outputs to `KnowledgeArtifact` records and surfaced linked artifacts in UI.
- Re-ran late-stage release regression pack on compose runtime and recorded green evidence for commit `578f578`.
- Restored discovery metric semantics and `CRIN_DISCOVERY_MAX_RECORDS` enforcement for full syncs.
- Added compiler-generated `KnowledgeClaim` rows and YAML frontmatter on KB markdown artifacts.
- Enriched Streamlit KB artifact detail with claims, source links and frontmatter/body preview.
- Added KB/output operator filters and detail drill-downs across artifacts, claims, entities and outputs.
- Added KB lint check for document-version-linked compiler artifacts missing claims.
- Re-ran full `Release Ready Check` on compose runtime and recorded green evidence for commit `f0c0a6a`.
- Added KB/output review-status filters, KB conflicted-claims filter and KB conflict summary previews.
- Re-ran late-stage release regression pack on compose runtime and recorded green evidence for commit `f545473`.
- Added KB conflict artifact filter, structured KB entity detail UI, KB entity alias search, KB claim conflict columns and outputs generator-version filter.
- Re-ran late-stage release regression pack on compose runtime and recorded green evidence for commit `79f4ede`.
- Added KB artifact generator-version filter and compact KB entity/output operator tables.
- Re-ran late-stage release regression pack on compose runtime and recorded green evidence for commit `7e10158`.
- Re-ran full `Release Ready Check` on compose runtime and recorded green evidence for commit `b2f2363`.
- Added KB artifact body search, KB entity ref search, KB conflict review scoping/artifact ids, outputs scope search and richer KB/output detail metrics.
- Re-ran late-stage release regression pack on compose runtime and recorded green evidence for commit `67e3797`.
- Added outputs has-file filter and synced compact KB artifact table coverage in backlog/versioning docs.
- Re-ran late-stage release regression pack on compose runtime and recorded green evidence for commit `a4a7c24`.
- Added compact review history/queue UI and scoring diff summary tables.
- Re-ran late-stage release regression pack on compose runtime and recorded green evidence for commit `574e19c`.

---

**Version:** 1.1  
**Last Updated:** 2026-04-23  
**Status:** ✅ Active for MVP
