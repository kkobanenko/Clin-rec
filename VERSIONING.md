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

---

**Version:** 1.1  
**Last Updated:** 2026-04-23  
**Status:** ✅ Active for MVP
