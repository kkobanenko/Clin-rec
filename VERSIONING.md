# Component Versioning & Reproducibility

This document tracks component versions for reproducibility across runs, per PRD section 4 (Version everything) and section 9 (Reproducibility).

## Service Versions

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
- ✅ Stableдiscovery (handled by multi-strategy fallback)
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

---

**Version:** 1.0  
**Last Updated:** 2026-04-01  
**Status:** ✅ Active for MVP
