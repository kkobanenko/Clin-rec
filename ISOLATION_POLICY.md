# Port & Container Isolation Policy

## Project Container Isolation

The Clin-rec project uses Docker Compose with explicit container naming and port mapping to ensure complete isolation from other applications on the server.

### Dedicated Project Containers

**All project containers are prefixed with `crin_`:**

| Container Name | Image | Host Port | Container Port | Purpose |
|---|---|---|---|---|
| `crin_postgres` | postgres:15-alpine | `5433` | `5432` | Clinical data + audit DB |
| `crin_redis` | redis:7-alpine | `6380` | `6379` | Celery broker & cache |
| `crin_minio` | minio/minio | `9010` | `9000` | S3-compatible artifact storage |
| `crin_minio_init` | minio/mc | — | — | MinIO bucket initialization |
| `crin_app` | crin-app (built) | `8000` | `8000` | FastAPI backend |
| `crin_worker` | crin-worker (built) | — | — | Celery worker (internal) |
| `crin_streamlit` | crin-streamlit (built) | `8501` | `8501` | Streamlit UI dashboard |

### Port Conflict Prevention

**Reserved ports for this project:**
- Host: `5433, 6380, 8000, 8501, 9010, 9011`
- Used by: Only `crin_*` containers
- Other apps on server: Must use different ports (e.g., 5432, 6379, 8080, 9000 may be in use by other services)

**Before any Docker operation, the agent verifies:**
```bash
# 1. List all crin_ containers
docker ps -a --filter "label=com.docker.compose.project=crin" --format "table {{.Names}}\t{{.Status}}"

# 2. Check port conflicts (only for crin_ ports)
netstat -tlnp 2>/dev/null | grep -E "5433|6380|8000|8501|9010|9011"

# 3. Verify no OTHER containers are affected
docker ps -a --filter "label!=com.docker.compose.project=crin" --format "{{.Names}}" > /tmp/other_containers.txt
```

## Agent Safety Rules

### ✅ ALLOWED Operations

The agent can ONLY:

1. **Manage `crin_*` containers:**
   ```bash
   docker compose up -d crin_postgres crin_redis crin_app crin_worker
   docker compose restart crin_app
   docker compose logs crin_app
   docker compose down  # Only stops crin_ services
   ```

2. **Verify crin_ health:**
   ```bash
   docker compose ps                    # Shows only crin_ services
   docker inspect crin_app             # Get container details
   docker exec crin_app curl /health   # Health checks
   ```

3. **Operate on project volumes:**
   ```bash
   # These volumes are exclusive to crin_ project
   - crin_pg_data
   - crin_minio_data
   ```

### ❌ FORBIDDEN Operations

The agent MUST NEVER:

1. **Touch other containers:**
   ```bash
   # ❌ FORBIDDEN:
   docker stop airflow                  # Not crin_ prefixed
   docker restart postgres              # System service (not crin_postgres)
   docker rm redis                      # Wrong container
   ```

2. **Access non-project ports:**
   ```bash
   # ❌ FORBIDDEN:
   curl http://localhost:5432           # System PostgreSQL
   redis-cli -p 6379                    # System Redis (crin uses 6380)
   curl http://localhost:9000           # System MinIO (crin uses 9010)
   ```

3. **Modify other Docker networks/volumes:**
   ```bash
   # ❌ FORBIDDEN:
   docker network rm bridge             # Default network
   docker volume rm postgres_data       # Non-crin volume
   ```

4. **Use `docker compose` without proper scope:**
   ```bash
   # ❌ FORBIDDEN (could affect other stacks):
   cd /path/to/other/project && docker compose down  # Wrong directory!
   
   # ✅ REQUIRED (always verify cwd first):
   cd /home/kobanenkokn/Clin-rec && docker compose ps
   ```

## Pre-Operation Checklist

Before ANY Docker operation, the agent executes:

```python
def pre_docker_operation_check():
    """Verify we're only touching crin_ containers."""
    
    # 1. Verify working directory
    assert os.getcwd() == "/home/kobanenkokn/Clin-rec", "Wrong directory!"
    
    # 2. List what will be affected
    result = subprocess.run(
        "docker compose config --services",
        shell=True,
        capture_output=True,
        text=True
    )
    services = result.stdout.strip().split('\n')
    
    # 3. Verify all services are in docker-compose.yml
    expected_services = {
        'postgres', 'redis', 'minio', 'minio-init',
        'app', 'worker', 'streamlit'
    }
    assert all(s in expected_services for s in services), \
        f"Unexpected services in compose: {services}"
    
    # 4. Check for port conflicts ONLY on crin_ ports
    crin_ports = ['5433', '6380', '8000', '8501', '9010', '9011']
    # (implementation checks netstat)
    
    return True  # Safe to proceed
```

## Monitoring Other Services

The agent can safely MONITOR (read-only) other services to understand the server state:

```bash
# ✅ SAFE (read-only, no modification):
docker ps -a                           # List all containers
docker network ls                      # See all networks
docker volume ls                       # See all volumes
netstat -tlnp                          # Port usage
ps aux | grep docker                   # Process inspection
```

But will NEVER modify them.

## Emergency Procedures

If a port conflict is detected with another service:

1. **Identify conflict:**
   ```bash
   # Port 8000 in use but not by crin_app?
   sudo lsof -i :8000
   # Shows which process/container owns it
   ```

2. **Report to user:**
   ```
   ❌ Port 8000 already in use by: [service_name]
   Host 8000 is reserved for crin_app (ISOLATION_POLICY).
   
   Options:
   - Same project: docker compose down && docker compose up -d (or ./scripts/crin_compose_recycle.sh)
   - Orphan crin_app: docker stop/rm crin_app, then compose up again
   - Other process on host: stop it; do not change Clin-rec host port without policy update
   ```

3. **Never force restart or kill other services** - always wait for user approval

### Port 8000: canonical host port for `crin_app`

**Host `8000` → `crin_app` is reserved by this project** (see table above). Do not change the mapping to another host port without updating this document and all dependent docs.

If Docker reports **`failed to bind host port 0.0.0.0:8000: address already in use`**:

1. **Prefer recycling this stack** (only affects compose project `crin`):
   ```bash
   cd /path/to/Clin-rec   # repository root, where docker-compose.yml lives
   docker compose down
   docker compose up -d
   ```
   Or run the helper: `./scripts/crin_compose_recycle.sh`

2. **If the port is still taken**, see who holds it (read-only checks are safe):
   ```bash
   docker ps -a --format '{{.Names}}\t{{.Ports}}' | grep 8000
   sudo ss -tlnp | grep ':8000'
   ```
   - **Orphaned `crin_app`** (exited container still published, or name collision):  
     `docker stop crin_app 2>/dev/null; docker rm crin_app 2>/dev/null`  
     then `docker compose up -d` again from this repo.
   - **Another project or host `uvicorn`** on `8000`: stop that process, or this stack cannot start. **Do not** reassign Clin-rec to ad-hoc ports without a policy update.

3. **Host-only dev**: if you run the API with `uvicorn` on the host on port 8000, stop it before `docker compose up`, or they will conflict.

## Git Safety

Agent will NOT:
- ❌ Commit changes to files outside Clin-rec project
- ❌ Push to upstream repos without agreement
- ❌ Modify shared configuration files in parent directories

---

## Quick Reference: Safe Commands

```bash
# ✅ SAFE - Project management
cd /home/kobanenkokn/Clin-rec
docker compose up -d
docker compose ps
docker compose logs crin_app
docker compose down
./scripts/crin_compose_recycle.sh   # down + up -d — если порт 8000 занят старым crin_app

# ✅ SAFE - Monitoring (read-only)
docker ps -a --filter "name=crin_"
docker inspect crin_app
netstat -tlnp | grep -E "5433|6380|8000|8501"

# ✅ SAFE - Project operations
.venv/bin/python -m pytest
scripts/e2e_smoke.py
git commit -m "..."
git push origin/gitlab main

# ❌ UNSAFE - Never do these
docker stop postgres          # Wrong container!
docker compose down -v        # Could affect other stacks
sudo systemctl restart docker # System-wide restart!
rm -rf /var/lib/docker/*      # Catastrophic!
```

---

**Version:** 1.1  
**Last Updated:** 2026-04-03  
**Status:** ✅ Active — Agent is fully isolated to crin_* resources
