from pathlib import Path


SCRIPT_PATH = Path("scripts/pilot_preflight.sh")


def _read_script() -> str:
    return SCRIPT_PATH.read_text(encoding="utf-8")


def test_pilot_preflight_script_exists():
    assert SCRIPT_PATH.exists()


def test_pilot_preflight_checks_compose_config():
    content = _read_script()
    assert "docker compose" in content
    assert "config" in content


def test_pilot_preflight_checks_required_env_vars():
    content = _read_script()
    assert "CRIN_DATABASE_URL" in content
    assert "CRIN_CELERY_BROKER_URL" in content
    assert "CRIN_S3_BUCKET" in content


def test_pilot_preflight_checks_service_availability():
    content = _read_script()
    assert "pg_isready" in content
    assert "redis-cli ping" in content
    assert "minio/health/live" in content
    assert "http://127.0.0.1:8000/health" in content
    assert "http://127.0.0.1:8501" in content


def test_pilot_preflight_checks_bucket_and_migrations():
    content = _read_script()
    assert "/data/cr-artifacts" in content
    assert "alembic" in content
    assert "current" in content
    assert "heads" in content
