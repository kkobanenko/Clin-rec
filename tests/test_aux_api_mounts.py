from types import SimpleNamespace
from unittest.mock import patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_compile_kb_endpoint_is_mounted_and_queues_task():
    task = SimpleNamespace(id="kb-task-1")
    with patch("app.api.kb.run_compile_kb.delay", return_value=task):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post("/kb/compile")

    assert resp.status_code == 202
    data = resp.json()
    assert data["task_id"] == "kb-task-1"


@pytest.mark.asyncio
async def test_task_status_endpoint_is_mounted():
    fake_result = SimpleNamespace(
        state="SUCCESS",
        ready=lambda: True,
        failed=lambda: False,
        successful=lambda: True,
        result={"items": 3},
    )
    with patch("app.api.tasks.AsyncResult", return_value=fake_result):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/tasks/demo-task?include_result=true")

    assert resp.status_code == 200
    data = resp.json()
    assert data["task_id"] == "demo-task"
    assert data["state"] == "SUCCESS"
    assert data["result"] == {"items": 3}