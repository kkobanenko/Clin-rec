# Sandbox Configuration for Agent Docker Access

## Current Setup

The VS Code sandbox is configured to allow the GitHub Copilot agent autonomous control over Docker containers and infrastructure management.

### Required Permissions

The following settings in `.vscode/settings.json` enable the agent to:
- Access Docker socket for container management
- Read Docker configuration and state
- Write to runtime directories

```json
"chat.tools.terminal.sandbox.linuxFileSystem": {
    "allowWrite": [
        "/home/kobanenkokn/Clin-rec",
        "/home/kobanenkokn/.local",
        "/home/kobanenkokn/.cache",
        "/home/kobanenkokn/.docker",
        "/tmp",
        "/run",
        "/var/run/docker.sock"
    ],
    "allowRead": ["/var/lib/docker", "/etc/docker", "/var/run"]
}
```

### Network Access

The agent can communicate with:
- Docker registries (docker.io, registry-1.docker.io, etc.)
- GitHub (github.com) and GitLab (gitlab.gdpgroup.ru)
- Russian state medical data sources (cr.minzdrav.gov.ru, apicr.minzdrav.gov.ru)
- PyPI and Python mirrors
- Localhost services

## Agent Capabilities

With these permissions, the agent can:

### Container Management
```bash
docker ps                    # List containers
docker compose up -d         # Start services
docker compose down          # Stop services
docker logs <container>      # View container logs
docker exec <container> ...  # Execute commands in container
```

### Infrastructure Operations
```bash
# Start/stop API server
docker compose up -d crin_app
docker compose restart crin_app

# Monitor worker tasks
docker compose logs -f crin_worker

# Access database utilities
docker compose exec crin_postgres psql ...

# Check service health
docker compose ps
```

### Development Workflows
- Automated testing and validation
- Smoke testing (e2e_smoke.py)
- Database migrations
- Dependency updates
- Git operations

## Example: Agent Autonomous PRD/TZ Testing

```python
# Agent can now execute entire test workflows:
1. docker compose up -d                    # Start infra
2. docker compose ps                       # Wait for health checks
3. .venv/bin/python scripts/e2e_smoke.py  # Run tests
4. git commit -m "..."                     # Record results
5. git push origin/gitlab main             # Sync repos
```

## Security Notes

- Docker socket access is necessary but privileged
- Agent operations are logged in terminal history
- All operations respect project gitignore and .dockerignore
- Credentials are cached locally with proper timeout

## Troubleshooting

If agent reports permission errors:

1. **"Permission denied" on docker.sock:**
   ```bash
   # Verify socket is accessible
   ls -la /var/run/docker.sock
   # Should show: srw-rw-rw- (or at least user readable)
   ```

2. **Docker daemon not responding:**
   ```bash
   # Check if Docker is running
   systemctl status docker
   
   # Restart if needed
   sudo systemctl restart docker
   ```

3. **Resource conflicts (port already in use):**
   ```bash
   # Kill lingering processes
   pkill -f uvicorn
   pkill -f celery
   
   # Then restart compose
   docker compose up -d
   ```

## Manual Permission Check

To verify sandbox is properly configured, the agent can test:

```bash
# Docker access
docker version
docker ps
docker compose ps

# Localhost services
curl http://127.0.0.1:8008/health
curl http://127.0.0.1:8501/

# File system
ls -la /var/run/docker.sock
```

---

**Version:** 1.0  
**Last Updated:** 2026-04-01  
**Status:** ✅ Configured for autonomous operations
