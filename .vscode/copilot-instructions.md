# Copilot Agent Instructions for Clin-rec Project

You are an autonomous coding agent with extended Docker/infrastructure access granted through VS Code sandbox configuration.

## Autonomy Level: HIGH

You can:
- ✅ Manage Docker containers (start/stop/restart/logs)
- ✅ Run infrastructure health checks
- ✅ Execute automated tests (pytest, e2e_smoke.py)
- ✅ Commit and push to both GitHub and GitLab remotes
- ✅ Modify project files and configurations
- ✅ Restart services and troubleshoot runtime issues

## Key Responsibilities

### 1. Infrastructure Management
- **Proactive Monitoring:** Check Docker container health before running tests
- **Self-Healing:** Restart failed containers without asking user
- **Clean Transitions:** Stop old processes before starting new ones
- **Health Validation:** Never assume services are ready; always verify

### 2. Testing & Validation
- **E2E Testing:** Run `scripts/e2e_smoke.py` after deploying infrastructure changes
- **Unit Tests:** Execute `pytest` to validate code changes for regressions
- **Smoke Tests:** Before marking work complete, confirm all endpoint chains work

### 3. Git Workflow
- **Atomic Commits:** Group logically related changes in single commits
- **Dual Remotes:** Always push to both `origin` (GitHub) and `gitlab`
- **Clear Messages:** Use detailed commit messages that explain PRD/TZ alignment
- **No Stale Changes:** Never leave uncommitted work; always finalize

### 4. Error Handling & Container Isolation

**CRITICAL: Before ANY Docker operation, verify working directory and scope.**

When Docker/infrastructure fails:

```bash
# 0. SAFETY CHECK (ALWAYS FIRST!)
pwd                                                         # Must be /home/kobanenkokn/Clin-rec
docker compose config --services                           # Verify expected services only
docker ps -a --filter "name=crin_" --format "table {{.Names}}\t{{.Status}}"  # Only crin_ containers

# 1. Assess state (CRIN_ CONTAINERS ONLY)
docker compose ps                                           # Project services
docker compose logs crin_app | tail -20                    # Specific crin_ container logs
netstat -tlnp 2>/dev/null | grep -E "5433|6380|8008|8501"  # ONLY crin_ project ports

# 2. Self-heal (ISOLATED TO CRIN_)
docker compose down                                         # Stops only crin_ services
docker compose up -d                                        # Starts only crin_ services  
sleep 30                                                    # Wait for health checks
docker compose ps                                           # Confirm crin_ healthy

# 3. Validate
curl http://127.0.0.1:8008/health                         # API health (compose host port)
.venv/bin/python scripts/e2e_smoke.py                      # Full chain test

# 4. Report & retry
```

**Port Isolation Guarantee:**
- ✅ SAFE: Ports 5433, 6380, 8008, 8501, 9010, 9011 (crin_ project)
- ❌ FORBIDDEN: Ports 5432, 6379, 8080, 9000 (other systems)
- ❌ FORBIDDEN: Touching non-crin_ containers (postgres, redis, airflow, superset, etc.)

See [ISOLATION_POLICY.md](ISOLATION_POLICY.md) for complete safeguards.

# 4. Report & retry
```

## Project Context

### Architecture
- **FastAPI** backend: host **8008** → container **8000** (`crin_app`)
- **Celery** workers (container: crin_worker)
- **PostgreSQL** on port 5433 (container: crin_postgres)
- **Redis** on port 6380 (container: crin_redis)
- **MinIO** S3 on port 9010 (container: crin_minio)
- **Streamlit** UI on port 8501 (container: crin_streamlit)

### Critical Files
- `.env` / `.env.example` — Configuration
- `app/core/config.py` — Settings class
- `app/services/discovery.py` — Document discovery (API-first strategy)
- `app/api/sync.py` — Pipeline triggers
- `scripts/e2e_smoke.py` — End-to-end validation

### PRD/TZ Compliance Goals
1. **Discovery:** Use `apicr.minzdrav.gov.ru` API with 1s+ delays (respect state data practices)
2. **Observability:** Populate `stats_json` with strategy, record counts, and diagnostics
3. **Resilience:** Implement multi-strategy fallback (API → Playwright SPA → DOM parsing)
4. **API Contracts:** Validate all endpoints per OpenAPI schema

## Workflow: "Продолжи работу над prd и TZ"

When user asks to continue PRD/TZ work, follow this sequence:

1. **Infrastructure Check** (mandatory)
   ```bash
   docker compose ps | grep -E "crin_(app|worker|postgres|redis)"
   # All must show "Up" status
   ```

2. **Code Review**
   - Read modified files from last session
   - Check PRD/TZ requirements alignment
   - Identify gaps or missing pieces

3. **Implementation**
   - Make targeted code changes
   - Run unit tests: `pytest -q`
   - No regressions allowed

4. **Integration Testing**
   - Run: `scripts/e2e_smoke.py`
   - Verify full chain: sync → documents → content → fragments
   - Check `stats_json` for strategy and counts

5. **Finalization**
   - Commit with detailed message
   - Push to both remotes
   - Report status to user with metrics

## Example Autonomous Session

```python
# User: "Продолжи работу над prd и TZ"
# Agent internally:

1. docker compose ps                    # ✓ All green
2. git status                           # ✓ Clean working tree
3. git log --oneline -n 3              # ✓ Review history
4. Read .env, app/core/config.py       # ✓ Study current config
5. Read app/services/discovery.py      # ✓ Understand discovery
6. Identify gap: "API response timeout not handled"
7. Edit app/services/discovery.py      # ✓ Add timeout handling
8. pytest -q                            # ✓ 48 passed, no regressions
9. docker compose restart crin_worker   # ✓ Fresh worker process
10. .venv/bin/python scripts/e2e_smoke.py  # ✓ Full chain green
11. git commit -m "feat: add timeout handling to API discovery"
12. git push origin main && git push gitlab main  # ✓ Both synced
13. Report to user with detailed metrics

# User: "Great! Now what about [next PRD point]?"
# Agent: Continues without interruption...
```

## Restrictions & Safety

### Absolute Restrictions (NEVER do these)

You CANNOT:
- ❌ Access files outside workspace without explicit permission
- ❌ Delete containers or databases without explicit user request
- ❌ Modify production credentials or secrets
- ❌ Push to main branch without explicit agreement (use feature branches if needed)
- ❌ Assume user has Docker/infrastructure running; always verify first

### Container & Port Isolation (CRITICAL)

You MUST NEVER:
- ❌ **Touch non-crin_ containers:** `docker stop airflow`, `docker restart postgres`, etc.
- ❌ **Access system ports:** 5432 (system postgres), 6379 (system redis), 9000 (system minio), 8080
- ❌ **Use system services:** Only work with crin_postgres (5433), crin_redis (6380), crin_minio (9010)
- ❌ **Modify Docker networks/volumes:** Only use crin_pg_data, crin_minio_data
- ❌ **Change working directory:** Always verify `pwd == /home/kobanenkokn/Clin-rec` before docker operations

**Safety Pre-flight Check (execute before ANY Docker command):**
```bash
pwd                                          # Must be /home/kobanenkokn/Clin-rec
docker compose config --services | sort     # Must match: app minio minio-init postgres redis streamlit worker
docker ps -a --filter "name=crin_"         # Verify ONLY crin_ containers exist in list
```

**If port conflict detected:**
```
❌ ERROR: Port 8008 already in use by non-crin_ service: [name]
→ STOP immediately
→ Report to user: cannot proceed, requires manual intervention
→ NEVER force kill other services
```

See [ISOLATION_POLICY.md](ISOLATION_POLICY.md) for complete port/container mapping and safeguards.

## Communication Style

When reporting to user:
- **Concise:** Max 3-5 sentences for common operations
- **Detailed:** Full context only when troubleshooting
- **Metrics:** Always include test counts, endpoint responses, record counts
- **Actionable:** Next steps clearly stated

**Example Report:**
```
✅ E2E Test Passed
- API: 1 run created, 707 documents discovered (strategy: backend_api)
- Content: 10 documents fetched, 5 sections per doc
- Fragments: 42 fragments extracted for first document
- Tests: 48 passed, no regressions
- Commit: 2e3d2ac pushed to origin/main and gitlab/main

Next: Integrate Streamlit UI validation if needed
```

---

**Version:** 1.0  
**Last Updated:** 2026-04-01  
**Status:** Active — Agent has Docker/infrastructure autonomy
